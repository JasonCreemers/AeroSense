/**
 * @file config.h
 * @brief Central configuration file for hardware pins, timing, and safety limits.
 */

#ifndef AEROSENSE_CONFIG_H_
#define AEROSENSE_CONFIG_H_

// --- SERIAL CONFIGURATION ---
#define BAUD_RATE 115200

// --- PIN DEFINITIONS ---
#define PIN_PUMP 2
#define PIN_LIGHTS 3
#define PIN_BUZZER 4

// --- SENSOR INTERFACES ---
// Environment I2C
#define ENV_I2C_ADDR 0x44

// Ultrasonic Serial1
#define DIST_SERIAL Serial1

// --- SENSOR TIMING ---
#define ENV_POLL_INTERVAL_MS 1000  // Temp poll interval
#define DIST_POLL_INTERVAL_MS 100  // Distance poll interval

// --- SENSOR BUFFER SIZES ---
#define ENV_BUFFER_SIZE 5      // Median filter window
#define DIST_BUFFER_SIZE 15    // Trimmed-mean filter window

// --- SENSOR STALENESS ---
#define ENV_STALENESS_MS 10000UL   // 10s without new data = stale
#define DIST_STALENESS_MS 5000UL   // 5s without new data = stale

// --- SENSOR RANGE LIMITS ---
#define ENV_TEMP_MIN_F  -20.0  // Min valid temperature (°F)
#define ENV_TEMP_MAX_F  150.0  // Max valid temperature (°F)
#define ENV_HUM_MIN     0.0    // Min valid humidity (%)
#define ENV_HUM_MAX     100.0  // Max valid humidity (%)
#define DIST_MIN_MM     20     // Min valid distance (mm)
#define DIST_MAX_MM     4500   // Max valid distance (mm)

// --- SAFETY LIMITS ---
#define PUMP_MAX_RUNTIME_MS 30000UL
#define LIGHTS_MAX_RUNTIME_MS 86400000UL  // 24 hours

// --- PI HEARTBEAT WATCHDOG ---
#define PI_HEARTBEAT_TIMEOUT_MS 60000UL   // 60s without Pi contact = safe shutdown

#endif  // AEROSENSE_CONFIG_H_