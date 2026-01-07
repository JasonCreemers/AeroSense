/**
 * @file firmware.ino
 * @brief Main entry point for the AeroSense firmware.
 */

#include "config.h"
#include "actuators.h" 
#include "sensors.h"
#include "music.h"

// --- OBJECT INSTANTIATION ---
WaterPump pump;
GrowLights lights;
DistanceSensor dist_sensor;
EnvSensor env_sensor;
MusicPlayer music;

String input_buffer = "";

void setup() {
  Serial.begin(BAUD_RATE);

  // Seed random generator
  randomSeed(analogRead(A5));
  
  // Initialize subsystems
  pump.Begin();
  lights.Begin();
  dist_sensor.Begin();
  env_sensor.Begin();
  music.Begin();

  Serial.println(F("SYSTEM:READY"));
}

void loop() {
  // Background tasks
  pump.Update();
  lights.Update();
  dist_sensor.Update();
  env_sensor.Update();
  music.Update();
  if (pump.Update()) {
    music.PlaySong("Denied");
  }

  // Command parsing
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      ProcessCommand(input_buffer);
      input_buffer = "";
    } else {
      if (input_buffer.length() < 64) {
        input_buffer += c;
      }
    }
  }
}


// --- COMMAND ROUTER ---
/**
 * @brief Parses and routes incoming Serial commands to the appropriate subsystem.
 */
void ProcessCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  
  // Tokenize
  int first_space = cmd.indexOf(' ');
  String action = (first_space == -1) ? cmd : cmd.substring(0, first_space);
  String args   = (first_space == -1) ? ""  : cmd.substring(first_space + 1);

  // --- ACTUATORS ---
  // Pump control
  if (action == "PUMP") {
    if (args.startsWith("ON")) {
      long dur = 0;
      int space2 = args.indexOf(' ');
      if (space2 != -1) dur = args.substring(space2 + 1).toInt();
      pump.TurnOn(dur);
    }
    else if (args == "OFF") pump.TurnOff();
  } 
  
  // Lights control
  else if (action == "LIGHTS") {
    if (args.startsWith("ON")) {
      long dur = 0;
      int space2 = args.indexOf(' ');
      if (space2 != -1) dur = args.substring(space2 + 1).toInt();
      lights.TurnOn(dur);
    } 
    else if (args == "OFF") lights.TurnOff();
  }

  // --- SENSORS ---
  // Environment sensor
  else if (action == "READ_TEMP") {
    Serial.print(F("DATA_TEMP:"));
    Serial.print(env_sensor.GetAverageTemp(), 2);
    Serial.print(",");
    Serial.println(env_sensor.GetAverageHum(), 2);
  }

  // Distance sensor
  else if (action == "READ_DISTANCE") {
    Serial.print(F("DATA_DISTANCE:"));
    Serial.println(dist_sensor.GetAverageDistance());
  }

  // --- MUSIC ---
  else if (action == "MUSIC") {
    if (args.startsWith("PLAY")) {
      String param = args.substring(5);
      
      // Play note
      if (param.startsWith("NOTE ")) {
         String content = param.substring(5);
         
         String noteName = content;
         int duration = 0;
         
         // Check for note duration
         int spaceIndex = content.indexOf(' ');
         if (spaceIndex != -1) {
            noteName = content.substring(0, spaceIndex);
            duration = content.substring(spaceIndex + 1).toInt();
         }
         
         music.PlayNote(noteName, duration);
      } 
      else {
         // Play song
         music.PlaySong(param);
      }
    }
    // Stop music
    else if (args == "STOP") {
      music.Stop();
    }
  }

  // --- DIAGNOSTICS ---
  else if (action == "PING") {
    if (args == "" || args == "SYSTEM") {
      Serial.println(F("PONG"));
    }
    else if (args == "PUMP") {
      Serial.println(pump.IsActive() ? F("PONG:PUMP_ON") : F("PONG:PUMP_OFF"));
    }
    else if (args == "LIGHTS") {
      Serial.println(lights.IsActive() ? F("PONG:LIGHTS_ON") : F("PONG:LIGHTS_OFF"));
    }
    else if (args == "TEMP") {
      Serial.println(env_sensor.IsResponding() ? F("PONG:TEMP_OK") : F("PONG:TEMP_FAIL"));
    }
    else if (args == "DIST") {
      Serial.println(dist_sensor.IsResponding() ? F("PONG:DIST_OK") : F("PONG:DIST_FAIL"));
    }
    else if (args == "MUSIC") {
      Serial.println(music.IsPlaying() ? F("PONG:MUSIC_BUSY") : F("PONG:MUSIC_IDLE"));
    }
  }
  
  // --- SYSTEM ---
  else if (action == "STOP") {
    pump.TurnOff();
    lights.TurnOff();
    music.Stop();
    Serial.println(F("ACK:EMERGENCY_STOP"));
  }
}