/**
 * @file sensors.h
 * @brief Drivers and signal processing for environmental and distance sensors.
 */

#ifndef AEROSENSE_SENSORS_H_
#define AEROSENSE_SENSORS_H_

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

// Local buffer size for environment sensor smoothing
#define ENV_BUFFER_SIZE 5 

// --- ENVIRONMENT SENSOR ---
/**
 * @brief Driver for Temperature & Humidity environmental sensor.
 */
class EnvSensor {
 private:
  float t_buffer_[ENV_BUFFER_SIZE];
  float h_buffer_[ENV_BUFFER_SIZE];
  uint8_t head_;
  uint8_t valid_samples_;
  unsigned long last_poll_;

 public:
  EnvSensor() : head_(0), valid_samples_(0), last_poll_(0) {}

  void Begin() {
    Wire.begin();
  }

  /**
   * @brief Polls the sensor and updates the moving average buffer.
   */
  void Update() {
    if (millis() - last_poll_ < ENV_POLL_INTERVAL_MS) return;
    last_poll_ = millis();

    // Send measurement command
    Wire.beginTransmission(ENV_I2C_ADDR);
    Wire.write(0x24);
    Wire.write(0x00);
    if (Wire.endTransmission() != 0) return; 

    delay(15);

    // Read bytes
    Wire.requestFrom(ENV_I2C_ADDR, 6);
    if (Wire.available() == 6) {
      uint16_t t_raw = (Wire.read() << 8) | Wire.read();
      Wire.read();
      uint16_t h_raw = (Wire.read() << 8) | Wire.read();
      Wire.read();

      // Conversion
      float t_c = -45.0 + 175.0 * (t_raw / 65535.0);
      float t_f = t_c * 1.8 + 32.0; 
      float h_rel = 100.0 * (h_raw / 65535.0);

      // Add to circular buffer
      t_buffer_[head_] = t_f;
      h_buffer_[head_] = h_rel;
      
      head_ = (head_ + 1) % ENV_BUFFER_SIZE;
      if (valid_samples_ < ENV_BUFFER_SIZE) valid_samples_++;
    }
  }

  /**
   * @brief Returns the smoothed temperature.
   * @return Temperature in Fahrenheit (Average of last N samples).
   */
  float GetAverageTemp() {
    if (valid_samples_ == 0) return 0.0;
    float sum = 0;
    for(int i=0; i<valid_samples_; i++) sum += t_buffer_[i];
    return sum / valid_samples_;
  }

  /**
   * @brief Returns the smoothed humidity.
   * @return Relative Humidity % (Average of last N samples).
   */
  float GetAverageHum() {
    if (valid_samples_ == 0) return 0.0;
    float sum = 0;
    for(int i=0; i<valid_samples_; i++) sum += h_buffer_[i];
    return sum / valid_samples_;
  }

  bool IsResponding() const { return valid_samples_ > 0; }
};

// --- DISTANCE SENSOR ---
/**
 * @brief Driver for Ultrasonic sensor.
 */
class DistanceSensor {
 private:
  uint16_t buffer_[DIST_BUFFER_SIZE];
  uint8_t head_;
  unsigned long last_poll_;
  uint8_t valid_samples_;

 public:
  DistanceSensor() : head_(0), last_poll_(0), valid_samples_(0) {}

  void Begin() {
    // Standard baud rate
    DIST_SERIAL.begin(9600);
  }

  /**
   * @brief Reads serial stream and validates data frames.
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

          // Add to circular buffer
          buffer_[head_] = dist;
          head_ = (head_ + 1) % DIST_BUFFER_SIZE;
          if (valid_samples_ < DIST_BUFFER_SIZE) valid_samples_++;
        }
      }
    }
  }

/**
   * @brief Returns the smoothed distance.
   * @return Distance in mm (Average of last N samples).
   */
  uint16_t GetAverageDistance() {
    if (valid_samples_ == 0) return 0;

    unsigned long total = 0;
    for (int i = 0; i < valid_samples_; i++) {
      total += buffer_[i];
    }
    return total / valid_samples_;
  }

  bool IsResponding() const {
    return valid_samples_ > 0;
  }
};

#endif  // AEROSENSE_SENSORS_H_