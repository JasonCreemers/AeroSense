/**
 * @file actuators.h
 * @brief Abstraction layer for GPIO-controlled actuators.
 */

#ifndef AEROSENSE_ACTUATORS_H_
#define AEROSENSE_ACTUATORS_H_

#include <Arduino.h>
#include "config.h"

// --- BASE COMPONENT CLASS ---
/**
 * @brief Base class for any binary hardware component.
 */
class Component {
 protected:
  uint8_t pin_;
  bool is_active_;
  unsigned long start_time_;
  unsigned long duration_;
  bool is_timed_;

 public:
  explicit Component(uint8_t pin)
      : pin_(pin), is_active_(false), start_time_(0), duration_(0), is_timed_(false) {}

  /**
   * @brief Initializes the hardware pin.
   */
  void Begin() {
    pinMode(pin_, OUTPUT);
    digitalWrite(pin_, LOW);
  }

  /**
   * @brief Checks if the component is currently powered.
   * @return true if the component is ON, false otherwise.
   */
  bool IsActive() const {
    return is_active_;
  }

  /**
   * @brief Deactivates the component immediately.
   */
  virtual void TurnOff() {
    digitalWrite(pin_, LOW);
    is_active_ = false;
    is_timed_ = false;
  }

  /**
   * @brief Activates the component.
   * * @param duration (Optional) Duration in milliseconds to keep the component on.
   */
  virtual void TurnOn(unsigned long duration = 0) {
    digitalWrite(pin_, HIGH);
    is_active_ = true;
    start_time_ = millis();
    duration_ = duration;
    is_timed_ = (duration > 0);
  }

  /**
   * @brief Main state machine update. 
   */
  virtual bool Update() {
    if (is_active_ && is_timed_) {
      if (millis() - start_time_ >= duration_) {
        TurnOff();
        Serial.println(F("ALERT:TIMER_COMPLETE"));
        return false; // Normal timer completion = No Alarm
      }
    }
    return false;
  }
};

// --- PUMP ---
/**
 * @brief Controller for the water pump with safety overrides.
 */
class WaterPump : public Component {
 public:
  WaterPump() : Component(PIN_PUMP) {}

  /**
   * @brief Activates the pump with a mandatory safety limit.
   * @param duration Duration in ms. Clamped to PUMP_MAX_RUNTIME_MS.
   */
  void TurnOn(unsigned long duration = 0) override {
    // Enforce hard limit
    if (duration == 0 || duration > PUMP_MAX_RUNTIME_MS) {
      duration = PUMP_MAX_RUNTIME_MS;
    }

    Component::TurnOn(duration);
    Serial.print(F("ACK:PUMP_ON,"));
    Serial.println(duration);
  }

  void TurnOff() override {
    Component::TurnOff();
    Serial.println(F("ACK:PUMP_OFF"));
  }

  /**
   * @brief Checks pump timer and redundant safety cutoff.
   */
  bool Update() override {
    if (is_active_) {
      if (millis() - start_time_ >= PUMP_MAX_RUNTIME_MS) {
        TurnOff();
        Serial.println(F("ALERT:PUMP_SAFETY_CUTOFF"));
        return true; // <--- TRIGGER ALARM!
      }
      return Component::Update(); 
    }
    return false;
  }
};

// --- LIGHTS ---
/**
 * @brief Controller for the grow lights.
 */
class GrowLights : public Component {
 public:
  GrowLights() : Component(PIN_LIGHTS) {}

  void TurnOff() override {
    Component::TurnOff();
    Serial.println(F("ACK:LIGHTS_OFF"));
  }

  void TurnOn(unsigned long duration = 0) override {
    Component::TurnOn(duration);
    if (duration > 0) {
      Serial.print(F("ACK:LIGHTS_ON_TIMED,"));
      Serial.println(duration);
    } else {
      Serial.println(F("ACK:LIGHTS_ON"));
    }
  }
};

#endif  // AEROSENSE_ACTUATORS_H_