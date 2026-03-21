/**
 * @file firmware.ino
 * @brief Main entry point for the AeroSense firmware.
 */

#include "config.h"
#include "actuators.h" 
#include "sensors.h"
#include "music.h"
#include <avr/wdt.h>

// --- OBJECT INSTANTIATION ---
WaterPump pump;
GrowLights lights;
DistanceSensor dist_sensor;
EnvSensor env_sensor;
MusicPlayer music;

// --- STATIC MEMORY ALLOCATION ---
const int MAX_CMD_LEN = 64;
char input_buffer[MAX_CMD_LEN + 1];
int buffer_index = 0;

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
  wdt_enable(WDTO_4S);

  Serial.println(F("SYSTEM:READY"));
}

void loop() {
  // Background tasks
  wdt_reset();
  lights.Update();
  dist_sensor.Update();
  env_sensor.Update();
  music.Update();

  // Pump Safety Monitor
  if (pump.Update()) {
    music.PlaySong("Denied");
  }

  // --- SERIAL READ LOOP ---
  while (Serial.available()) {
    char c = (char)Serial.read();

    // End of command detected (New Line)
    if (c == '\n') {
      input_buffer[buffer_index] = '\0';
      ProcessCommand(input_buffer);
      buffer_index = 0;
    } 
    else {
      // Buffer Overflow Protection
      if (buffer_index < MAX_CMD_LEN) {
        input_buffer[buffer_index++] = c;
      }
    }
  }
}


// --- COMMAND ROUTER ---
/**
 * @brief Parses and routes incoming Serial commands using C-strings.
 * @param cmd The raw character array to parse (modified in-place by strtok).
 */
void ProcessCommand(char* cmd) {
  // Uppercase the entire command buffer for case-insensitive matching
  for (int i = 0; cmd[i]; i++) {
    cmd[i] = toupper(cmd[i]);
  }

  // Tokenize
  char* action = strtok(cmd, " \r\n");

  // Safety
  if (action == NULL) return;

  // --- ACTUATORS ---
  // Pump control
  if (strcmp(action, "PUMP") == 0) {
    char* arg = strtok(NULL, " \r\n");
    
    if (arg != NULL) {
      if (strcmp(arg, "ON") == 0) {
        long dur = 0;
        char* dur_str = strtok(NULL, " \r\n");
        if (dur_str != NULL) {
          dur = atol(dur_str);
        }
        pump.TurnOn(dur);
      }
      else if (strcmp(arg, "OFF") == 0) {
        pump.TurnOff();
      }
    }
  }

  // Lights control
  else if (strcmp(action, "LIGHTS") == 0) {
    char* arg = strtok(NULL, " \r\n");

    if (arg != NULL) {
      if (strcmp(arg, "ON") == 0) {
        long dur = 0;
        char* dur_str = strtok(NULL, " \r\n");
        if (dur_str != NULL) {
          dur = atol(dur_str);
        }
        lights.TurnOn(dur);
      }
      else if (strcmp(arg, "OFF") == 0) {
        lights.TurnOff();
      }
    }
  }

  // --- SENSORS ---
  // Environment sensor (gated behind staleness check)
  else if (strcmp(action, "READ_TEMP") == 0) {
    if (env_sensor.IsResponding()) {
      Serial.print(F("DATA_TEMP:"));
      Serial.print(env_sensor.GetFilteredTemp(), 2);
      Serial.print(",");
      Serial.println(env_sensor.GetFilteredHum(), 2);
    }
  }

  // Distance sensor (gated behind staleness check)
  else if (strcmp(action, "READ_DISTANCE") == 0) {
    if (dist_sensor.IsResponding()) {
      Serial.print(F("DATA_DISTANCE:"));
      Serial.println(dist_sensor.GetFilteredDistance());
    }
  }

  // --- MUSIC ---
  // Format: MUSIC PLAY <SONG> or MUSIC PLAY NOTE <NOTE> <DUR>
  else if (strcmp(action, "MUSIC") == 0) {
    char* sub_cmd = strtok(NULL, " \r\n");

    if (sub_cmd != NULL) {
      if (strcmp(sub_cmd, "PLAY") == 0) {
        char* target = strtok(NULL, " \r\n");
        
        if (target != NULL) {
          // Check if user wants to play a specific note
          if (strcmp(target, "NOTE") == 0) {
             char* noteName = strtok(NULL, " \r\n");
             char* durStr = strtok(NULL, " \r\n");
             int duration = 0;
             if (durStr != NULL) duration = atoi(durStr);
             
             if (noteName != NULL) {
                // Cast to String for library compatibility
                music.PlayNote(String(noteName), duration); 
             }
          } 
          else {
             // Play song
             music.PlaySong(String(target));
          }
        }
      }
      // Stop music
      else if (strcmp(sub_cmd, "STOP") == 0) {
        music.Stop();
      }
    }
  }

  // --- DIAGNOSTICS ---
  else if (strcmp(action, "PING") == 0) {
    char* arg = strtok(NULL, " \r\n");
    
    if (arg == NULL || strcmp(arg, "SYSTEM") == 0) {
      Serial.println(F("PONG"));
    }
    else if (strcmp(arg, "PUMP") == 0) {
      Serial.println(pump.IsActive() ? F("PONG:PUMP_ON") : F("PONG:PUMP_OFF"));
    }
    else if (strcmp(arg, "LIGHTS") == 0) {
      Serial.println(lights.IsActive() ? F("PONG:LIGHTS_ON") : F("PONG:LIGHTS_OFF"));
    }
    else if (strcmp(arg, "TEMP") == 0) {
      Serial.println(env_sensor.IsResponding() ? F("PONG:TEMP_OK") : F("PONG:TEMP_FAIL"));
    }
    else if (strcmp(arg, "DIST") == 0) {
      Serial.println(dist_sensor.IsResponding() ? F("PONG:DIST_OK") : F("PONG:DIST_FAIL"));
    }
    else if (strcmp(arg, "MUSIC") == 0) {
      Serial.println(music.IsPlaying() ? F("PONG:MUSIC_BUSY") : F("PONG:MUSIC_IDLE"));
    }
  }
  
  // --- SYSTEM ---
  else if (strcmp(action, "STOP") == 0) {
    pump.TurnOff();
    lights.TurnOff();
    music.Stop();
    Serial.println(F("ACK:EMERGENCY_STOP"));
  }
}