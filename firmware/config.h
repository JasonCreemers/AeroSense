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
#define ENV_POLL_INTERVAL_MS 1000 // Temp interval 
#define DIST_POLL_INTERVAL_MS 100 // Distance interval
#define DIST_BUFFER_SIZE 10 // Number of samples to average

// --- SAFETY LIMITS ---
#define PUMP_MAX_RUNTIME_MS 30000UL

#endif  // AEROSENSE_CONFIG_H_