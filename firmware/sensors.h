/**
 * @file sensors.h
 * @brief Drivers and signal processing for environmental and distance sensors.
 *
 * Filtering Strategy:
 *   - EnvSensor:      Median filter (5-sample window, 1s poll)
 *   - DistanceSensor:  Trimmed mean (15-sample window, 100ms poll, drops 3 highest + 3 lowest)
 *
 * All sensors include:
 *   - CRC / Checksum validation (reject corrupt readings at the source)
 *   - Range validation (reject physically impossible values)
 *   - Staleness detection (IsResponding() returns false if no fresh data within timeout)
 */

#ifndef AEROSENSE_SENSORS_H_
#define AEROSENSE_SENSORS_H_

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// --- CRC-8 for SHT3x (Polynomial 0x31, Init 0xFF) ---
/**
 * @brief Compute CRC-8 checksum per Sensirion SHT3x datasheet.
 * @param data Pointer to the 2-byte measurement word.
 * @param len  Number of bytes (always 2 for SHT3x words).
 * @return The computed CRC byte.
 */
static uint8_t sht3x_crc8(const uint8_t *data, uint8_t len) {
  uint8_t crc = 0xFF;
  for (uint8_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t bit = 0; bit < 8; bit++) {
      if (crc & 0x80)
        crc = (crc << 1) ^ 0x31;
      else
        crc = crc << 1;
    }
  }
  return crc;
}

// --- ENVIRONMENT SENSOR ---
/**
 * @brief Driver for Temperature & Humidity environmental sensor (SHT3x).
 *
 * Uses a median filter to reject outliers from the I2C readings.
 * Validates each sample with CRC-8 and range checks before buffering.
 */
class EnvSensor {
 private:
  float t_buffer_[ENV_BUFFER_SIZE];
  float h_buffer_[ENV_BUFFER_SIZE];
  uint8_t head_;
  uint8_t valid_samples_;
  unsigned long last_poll_;
  unsigned long last_success_;

  /**
   * @brief Insertion sort for a small float array (in-place).
   */
  static void sort_float(float *arr, uint8_t len) {
    for (uint8_t i = 1; i < len; i++) {
      float key = arr[i];
      int8_t j = i - 1;
      while (j >= 0 && arr[j] > key) {
        arr[j + 1] = arr[j];
        j--;
      }
      arr[j + 1] = key;
    }
  }

 public:
  EnvSensor() : head_(0), valid_samples_(0), last_poll_(0), last_success_(0) {}

  void Begin() {
    Wire.begin();
  }

  /**
   * @brief Polls the sensor, validates CRC + range, and updates the buffer.
   */
  void Update() {
    if (millis() - last_poll_ < ENV_POLL_INTERVAL_MS) return;
    last_poll_ = millis();

    // Send high-repeatability measurement command (0x2400)
    Wire.beginTransmission(ENV_I2C_ADDR);
    Wire.write(0x24);
    Wire.write(0x00);
    if (Wire.endTransmission() != 0) return;

    delay(15);

    // Read 6 bytes: [Temp MSB, Temp LSB, Temp CRC, Hum MSB, Hum LSB, Hum CRC]
    Wire.requestFrom(ENV_I2C_ADDR, 6);
    if (Wire.available() == 6) {
      uint8_t raw[6];
      for (uint8_t i = 0; i < 6; i++) {
        raw[i] = Wire.read();
      }

      // CRC Validation
      if (sht3x_crc8(&raw[0], 2) != raw[2]) return;  // Temp CRC fail
      if (sht3x_crc8(&raw[3], 2) != raw[5]) return;  // Hum CRC fail

      // Conversion
      uint16_t t_raw = (raw[0] << 8) | raw[1];
      uint16_t h_raw = (raw[3] << 8) | raw[4];

      float t_c = -45.0 + 175.0 * (t_raw / 65535.0);
      float t_f = t_c * 1.8 + 32.0;
      float h_rel = 100.0 * (h_raw / 65535.0);

      // Range Validation
      if (t_f < ENV_TEMP_MIN_F || t_f > ENV_TEMP_MAX_F) return;
      if (h_rel < ENV_HUM_MIN || h_rel > ENV_HUM_MAX) return;

      // Add to circular buffer
      t_buffer_[head_] = t_f;
      h_buffer_[head_] = h_rel;

      head_ = (head_ + 1) % ENV_BUFFER_SIZE;
      if (valid_samples_ < ENV_BUFFER_SIZE) valid_samples_++;

      last_success_ = millis();
    }
  }

  /**
   * @brief Returns the median-filtered temperature.
   * @return Temperature in Fahrenheit (median of buffered samples).
   */
  float GetFilteredTemp() {
    if (valid_samples_ == 0) return 0.0;

    // Copy buffer and sort
    float sorted[ENV_BUFFER_SIZE];
    memcpy(sorted, t_buffer_, valid_samples_ * sizeof(float));
    sort_float(sorted, valid_samples_);

    return sorted[valid_samples_ / 2];
  }

  /**
   * @brief Returns the median-filtered humidity.
   * @return Relative Humidity % (median of buffered samples).
   */
  float GetFilteredHum() {
    if (valid_samples_ == 0) return 0.0;

    // Copy buffer and sort
    float sorted[ENV_BUFFER_SIZE];
    memcpy(sorted, h_buffer_, valid_samples_ * sizeof(float));
    sort_float(sorted, valid_samples_);

    return sorted[valid_samples_ / 2];
  }

  /**
   * @brief Check if the sensor is alive and producing fresh data.
   * @return True if at least one sample exists AND data is not stale.
   */
  bool IsResponding() const {
    if (valid_samples_ == 0) return false;
    return (millis() - last_success_) < ENV_STALENESS_MS;
  }
};

// --- DISTANCE SENSOR ---
/**
 * @brief Driver for Ultrasonic distance sensor (serial UART).
 *
 * Uses a trimmed mean to reject outlier spikes common with ultrasonic sensors.
 * Drops the 3 highest and 3 lowest readings, averages the middle.
 */
class DistanceSensor {
 private:
  uint16_t buffer_[DIST_BUFFER_SIZE];
  uint8_t head_;
  unsigned long last_poll_;
  uint8_t valid_samples_;
  unsigned long last_success_;

  // Number of samples to trim from each end
  static const uint8_t TRIM_COUNT = 3;

  /**
   * @brief Insertion sort for a small uint16_t array (in-place).
   */
  static void sort_u16(uint16_t *arr, uint8_t len) {
    for (uint8_t i = 1; i < len; i++) {
      uint16_t key = arr[i];
      int8_t j = i - 1;
      while (j >= 0 && arr[j] > key) {
        arr[j + 1] = arr[j];
        j--;
      }
      arr[j + 1] = key;
    }
  }

 public:
  DistanceSensor() : head_(0), last_poll_(0), valid_samples_(0), last_success_(0) {}

  void Begin() {
    DIST_SERIAL.begin(9600);
  }

  /**
   * @brief Reads serial stream, validates checksum + range, and buffers data.
   */
  void Update() {
    if (millis() - last_poll_ < DIST_POLL_INTERVAL_MS) return;
    last_poll_ = millis();

    // Parse stream
    while (DIST_SERIAL.available() >= 4) {
      // Look for Frame Header
      if (DIST_SERIAL.read() == 0xFF) {
        uint8_t d_hi = DIST_SERIAL.read();
        uint8_t d_lo = DIST_SERIAL.read();
        uint8_t sum = DIST_SERIAL.read();

        // Validate Checksum
        if (((0xFF + d_hi + d_lo) & 0xFF) == sum) {
          uint16_t dist = (d_hi << 8) | d_lo;

          // Range Validation
          if (dist < DIST_MIN_MM || dist > DIST_MAX_MM) continue;

          // Add to circular buffer
          buffer_[head_] = dist;
          head_ = (head_ + 1) % DIST_BUFFER_SIZE;
          if (valid_samples_ < DIST_BUFFER_SIZE) valid_samples_++;

          last_success_ = millis();
        }
      }
    }
  }

  /**
   * @brief Returns the trimmed-mean filtered distance.
   *
   * Sorts the buffer, drops TRIM_COUNT from each end, averages the middle.
   * Falls back to simple average if fewer than (2 * TRIM_COUNT + 1) samples.
   *
   * @return Distance in mm.
   */
  uint16_t GetFilteredDistance() {
    if (valid_samples_ == 0) return 0;

    // Copy buffer and sort
    uint16_t sorted[DIST_BUFFER_SIZE];
    memcpy(sorted, buffer_, valid_samples_ * sizeof(uint16_t));
    sort_u16(sorted, valid_samples_);

    // Determine trim amount (need at least 2*trim+1 samples to trim)
    uint8_t trim = (valid_samples_ >= (2 * TRIM_COUNT + 1)) ? TRIM_COUNT : 0;

    unsigned long total = 0;
    uint8_t count = 0;
    for (uint8_t i = trim; i < valid_samples_ - trim; i++) {
      total += sorted[i];
      count++;
    }

    return (count > 0) ? (total / count) : 0;
  }

  /**
   * @brief Check if the sensor is alive and producing fresh data.
   * @return True if at least one sample exists AND data is not stale.
   */
  bool IsResponding() const {
    if (valid_samples_ == 0) return false;
    return (millis() - last_success_) < DIST_STALENESS_MS;
  }
};

#endif  // AEROSENSE_SENSORS_H_
