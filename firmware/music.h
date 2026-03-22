/**
 * @file music.h
 * @brief Non-blocking music player and frequency definitions.
 */

#ifndef AEROSENSE_MUSIC_H_
#define AEROSENSE_MUSIC_H_

#include <Arduino.h>
#include <avr/pgmspace.h>
#include "config.h"

// --- FREQUENCIES ---
#define REST 0
#define NOTE_C3  131
#define NOTE_CS3 139
#define NOTE_D3  147
#define NOTE_DS3 156
#define NOTE_E3  165
#define NOTE_F3  175
#define NOTE_FS3 185
#define NOTE_G3  196
#define NOTE_GS3 208
#define NOTE_A3  220
#define NOTE_AS3 233
#define NOTE_B3  247
#define NOTE_C4  262
#define NOTE_CS4 277
#define NOTE_D4  294
#define NOTE_DS4 311
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_FS4 370
#define NOTE_G4  392
#define NOTE_GS4 415
#define NOTE_A4  440
#define NOTE_AS4 466
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_CS5 554
#define NOTE_D5  587
#define NOTE_DS5 622
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_FS5 740
#define NOTE_G5  784
#define NOTE_GS5 831
#define NOTE_A5  880
#define NOTE_AS5 932
#define NOTE_B5  988
#define NOTE_C6  1047
#define NOTE_CS6 1109
#define NOTE_D6  1175
#define NOTE_DS6 1245
#define NOTE_E6  1319
#define NOTE_F6  1397
#define NOTE_FS6 1480
#define NOTE_G6  1568
#define NOTE_GS6 1661
#define NOTE_A6  1760
#define NOTE_AS6 1865
#define NOTE_B6  1976
#define NOTE_C7  2093
#define NOTE_CS7 2217
#define NOTE_D7  2349
#define NOTE_DS7 2489
#define NOTE_E7  2637
#define NOTE_F7  2794
#define NOTE_FS7 2960
#define NOTE_G7  3136
#define NOTE_GS7 3322
#define NOTE_A7  3520
#define NOTE_AS7 3729
#define NOTE_B7  3951
#define NOTE_C8  4186

// --- STRUCTS ---
/**
 * @brief Represents a single note.
 */
struct Note {
  int freq;
  float duration_beats;
};

/**
 * @brief Represents a complete song.
 */
struct Song {
  const char* name;
  const Note* notes;
  int num_notes;
  int tempo;
};

/**
 * @brief Helper for mapping string names to frequencies.
 */
struct NoteLookup {
  char name[5];
  int frequency;
};

// --- SINGLE NOTE TABLE ---
const NoteLookup kNoteTable[] PROGMEM = {
    {"C3", NOTE_C3}, {"CS3", NOTE_CS3}, {"D3", NOTE_D3}, {"DS3", NOTE_DS3}, {"E3", NOTE_E3}, {"F3", NOTE_F3}, {"FS3", NOTE_FS3}, {"G3", NOTE_G3}, {"GS3", NOTE_GS3}, {"A3", NOTE_A3}, {"AS3", NOTE_AS3}, {"B3", NOTE_B3},
    {"C4", NOTE_C4}, {"CS4", NOTE_CS4}, {"D4", NOTE_D4}, {"DS4", NOTE_DS4}, {"E4", NOTE_E4}, {"F4", NOTE_F4}, {"FS4", NOTE_FS4}, {"G4", NOTE_G4}, {"GS4", NOTE_GS4}, {"A4", NOTE_A4}, {"AS4", NOTE_AS4}, {"B4", NOTE_B4},
    {"C5", NOTE_C5}, {"CS5", NOTE_CS5}, {"D5", NOTE_D5}, {"DS5", NOTE_DS5}, {"E5", NOTE_E5}, {"F5", NOTE_F5}, {"FS5", NOTE_FS5}, {"G5", NOTE_G5}, {"GS5", NOTE_GS5}, {"A5", NOTE_A5}, {"AS5", NOTE_AS5}, {"B5", NOTE_B5},
    {"C6", NOTE_C6}, {"CS6", NOTE_CS6}, {"D6", NOTE_D6}, {"DS6", NOTE_DS6}, {"E6", NOTE_E6}, {"F6", NOTE_F6}, {"FS6", NOTE_FS6}, {"G6", NOTE_G6}, {"GS6", NOTE_GS6}, {"A6", NOTE_A6}, {"AS6", NOTE_AS6}, {"B6", NOTE_B6},
    {"C7", NOTE_C7}, {"CS7", NOTE_CS7}, {"D7", NOTE_D7}, {"DS7", NOTE_DS7}, {"E7", NOTE_E7}, {"F7", NOTE_F7}, {"FS7", NOTE_FS7}, {"G7", NOTE_G7}, {"GS7", NOTE_GS7}, {"A7", NOTE_A7}, {"AS7", NOTE_AS7}, {"B7", NOTE_B7},
    {"C8", NOTE_C8}
};
const int kNoteTableSize = sizeof(kNoteTable) / sizeof(kNoteTable[0]);

// --- SONGS ---
// Daisy Bell (Daisy)
const Note kDaisy[] PROGMEM = {
  {NOTE_G5, 3}, {NOTE_E5, 3}, {NOTE_C5, 3}, {NOTE_G4, 3}, {NOTE_A4, 1}, {NOTE_B4, 1}, {NOTE_C5, 1}, {NOTE_A4, 2}, {NOTE_C5, 1}, {NOTE_G4, 4}, {REST, 2},
  {NOTE_D5, 3}, {NOTE_G5, 3}, {NOTE_E5, 3}, {NOTE_C5, 3}, {NOTE_A4, 1}, {NOTE_B4, 1}, {NOTE_C5, 1}, {NOTE_D5, 2}, {NOTE_E5, 1}, {NOTE_D5, 4}, {REST, 1},
  {NOTE_E5, 1}, {NOTE_F5, 1}, {NOTE_E5, 1}, {NOTE_D5, 1}, {NOTE_G5, 2}, {NOTE_E5, 1}, {NOTE_D5, 1}, {NOTE_C5, 3}, {REST, 2},
  {NOTE_D5, 1}, {NOTE_E5, 2}, {NOTE_C5, 1}, {NOTE_A4, 2}, {NOTE_C5, 1}, {NOTE_A4, 1}, {NOTE_G4, 2}, {REST, 2},
  {NOTE_G4, 1}, {NOTE_C5, 2}, {NOTE_E5, 1}, {NOTE_D5, 2}, {NOTE_G4, 1}, {NOTE_C5, 2}, {NOTE_E5, 1}, {NOTE_D5, 0.5}, {NOTE_E5, 1}, {NOTE_F5, 1.5}, {NOTE_G5, 1}, {NOTE_E5, 1}, {NOTE_C5, 1}, {NOTE_D5, 2},
  {NOTE_G4, 1}, {NOTE_C5, 6}
};

// Happy Birthday (Curiosity)
const Note kCuriosity[] PROGMEM = {
    {NOTE_G3, 1}, {NOTE_G3, 1}, {NOTE_A3, 2}, {NOTE_G3, 2}, {NOTE_C4, 2}, {NOTE_B3, 3}, {REST, 0.5},
    {NOTE_G3, 1}, {NOTE_G3, 1}, {NOTE_A3, 2}, {NOTE_G3, 2}, {NOTE_D4, 2}, {NOTE_C4, 3},
    {NOTE_G3, 1}, {NOTE_G3, 1}, {NOTE_G4, 2}, {NOTE_E4, 2}, {NOTE_C4, 2}, {NOTE_B3, 2}, {NOTE_A3, 2.5}, {REST, 0.5},
    {NOTE_F4, 1}, {NOTE_F4, 1}, {NOTE_E4, 2}, {NOTE_C4, 2}, {NOTE_D4, 2}, {NOTE_C4, 4}
};

// No Strings on Me (Ultron)
const Note kUltron[] PROGMEM = {
    {NOTE_AS3, 0.75}, {NOTE_B3, 1}, {NOTE_D4, 1}, {NOTE_G3, 1}, {REST, 0.5}, {NOTE_B3, 0.5}, {NOTE_D3, 1}, {NOTE_D3, 1}, {NOTE_D3, 1}, {REST, 0.5}, {NOTE_B3, 0.5},
    {NOTE_D3, 1}, {NOTE_D3, 1}, {NOTE_D3, 1}, {REST, 0.5}, {NOTE_D3, 0.5}, {NOTE_G3, 1}, {NOTE_A3, 1}, {NOTE_B3, 1}, {REST, 1},
    {NOTE_B3, 1}, {NOTE_D4, 1}, {NOTE_G3, 1}, {REST, 0.5}, {NOTE_B3, 0.5}, {NOTE_D3, 1}, {NOTE_D3, 1}, {NOTE_D3, 1}, {REST, 0.5}, {NOTE_B3, 0.5},
    {NOTE_D3, 1}, {NOTE_D3, 1}, {NOTE_E3, 1}, {NOTE_E3, 1}, {NOTE_G3, 4} 
};

// Max Verstappen Theme (MV1)
const Note kMax[] PROGMEM = {
    {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_E4, 2},
    {REST, 0.25}, {NOTE_E4, 1}, {NOTE_E4, 0.25}, {NOTE_C4, 1}, {NOTE_B3, 1},
    {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_E4, 2},
    {REST, 0.25}, {NOTE_E4, 1}, {NOTE_E4, 0.25}, {NOTE_C4, 1}, {NOTE_B3, 1},
    {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_E4, 2},
    {REST, 0.25}, {NOTE_E4, 1}, {NOTE_E4, 0.25}, {NOTE_C4, 1}, {NOTE_B3, 1},
    {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_A3, 0.66}, {NOTE_E4, 2},
    {REST, 0.25}, {NOTE_E4, 1}, {NOTE_E4, 0.25}, {NOTE_C4, 1}, {NOTE_B3, 1},
};

// Interstellar Theme (Tars)
const Note kInterstellar[] PROGMEM = {
    {NOTE_A3, 0.25}, {NOTE_B3, 0.25}, {NOTE_C4, 0.25}, {NOTE_B3, 0.25}, {NOTE_A3, 0.25}, {NOTE_C4, 0.25},
    {NOTE_B3, 0.25}, {NOTE_A3, 0.25}, {NOTE_G3, 0.25}, {NOTE_A3, 0.25}, {NOTE_B3, 0.25}, {NOTE_A3, 0.25},
    {NOTE_B3, 0.25}, {NOTE_A3, 0.25}, {NOTE_G3, 0.25}, {NOTE_A3, 0.25}, {NOTE_B3, 0.25}, {NOTE_A3, 0.25},
    {NOTE_A3, 1}, {NOTE_B3, 1}, {NOTE_C4, 1}, {NOTE_B3, 1}, {NOTE_A3, 1}, {NOTE_B3, 1},
    {NOTE_C4, 0.25}, {NOTE_C4, 0.25}, {NOTE_A3, 0.25}, {NOTE_C4, 0.25}, {NOTE_B3, 0.25}, {NOTE_A3, 0.25},
    {NOTE_B3, 0.25}, {NOTE_A3, 0.25}, {NOTE_G3, 0.25}, {NOTE_A3, 0.25}, {NOTE_B3, 0.25}, {NOTE_A3, 0.25},
    {NOTE_B3, 0.25}, {NOTE_A3, 0.25}, {NOTE_G3, 0.25}, {NOTE_A3, 0.25}, {NOTE_B3, 0.25}, {NOTE_A3, 0.25},
};

// Panic Alarm (Panic)
const Note kAlarm[] PROGMEM = {
    {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B5, 0.5}, {NOTE_F5, 0.5}, {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B5, 0.5}, {NOTE_F5, 0.5},
    {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B5, 0.5}, {NOTE_F5, 0.5}, {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B4, 0.5}, {NOTE_F5, 0.5},
    {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B5, 0.5}, {NOTE_F5, 0.5}, {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B5, 0.5}, {NOTE_F5, 0.5},
    {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B5, 0.5}, {NOTE_F5, 0.5}, {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, {NOTE_B4, 0.5}, {NOTE_F5, 0.5}, 
};

// Morning Mood (Morning)
const Note kMorning[] PROGMEM = {
    {NOTE_G4, 1}, {NOTE_E4, 1}, {NOTE_D4, 1}, {NOTE_C4, 1}, 
    {NOTE_D4, 1}, {NOTE_E4, 1}, {NOTE_G4, 1}, 
    {NOTE_E4, 1}, {NOTE_D4, 1}, {NOTE_C4, 1}, 
    {NOTE_D4, 0.5}, {NOTE_E4, 0.5}, {NOTE_D4, 0.5}, {NOTE_E4, 0.5},
    {NOTE_G4, 1}, {NOTE_E4, 1}, {NOTE_G4, 1}, {NOTE_A4, 1}, {NOTE_E4, 1}, 
    {NOTE_A4, 1}, {NOTE_G4, 1}, {NOTE_E4, 1}, {NOTE_D4, 1}, {NOTE_C4, 2}
};

// Nighttime Lullaby (Sleep)
const Note kLullaby[] PROGMEM = {
    {NOTE_A3, 0.5}, {NOTE_A3, 0.5}, {NOTE_C4, 2}, {NOTE_A3, 0.5}, {NOTE_A3, 0.5}, {NOTE_C4, 2},
    {NOTE_A3, 0.5}, {NOTE_C4, 0.5}, {NOTE_F4, 1}, {NOTE_E4, 1}, {NOTE_D4, 1}, {NOTE_D4, 1}, {NOTE_C4, 1},
    {NOTE_G3, 0.5}, {NOTE_A3, 0.5}, {NOTE_B3, 1}, {NOTE_G3, 1}, {NOTE_G3, 0.5}, {NOTE_A3, 0.5}, {NOTE_B3, 2},
    {NOTE_G3, 0.5}, {NOTE_B3, 0.5}, {NOTE_E4, 0.5}, {NOTE_D4, 0.5}, {NOTE_C4, 1}, {NOTE_E4, 1}, {NOTE_F4, 3}
};

// FNAF Beatbox (FNAF)
const Note kFnaf[] PROGMEM = {
    {NOTE_C4, 1}, {NOTE_D4, 0.75}, {NOTE_C4, 0.25}, {NOTE_A3, 1}, {NOTE_A3, 1}, 
    {NOTE_A3, 0.75}, {NOTE_G3, 0.25}, {NOTE_A3, 0.75}, {NOTE_AS3, 0.25}, {NOTE_A3, 1.5}, {REST, 0.5},
    {NOTE_AS3, 1}, {NOTE_G3, 0.75}, {NOTE_C4, 0.25}, {NOTE_A3, 2},
    {NOTE_F3, 1}, {NOTE_D3, 0.75}, {NOTE_G3, 0.25}, {NOTE_CS3, 2}
};

// SpongeBob Sad Theme (Sponge)
const Note kSponge[] PROGMEM = {
    {NOTE_G3, 1}, {NOTE_G4, 3}, {NOTE_G4, 0.5}, {NOTE_FS4, 0.5}, {NOTE_F4, 3}, {NOTE_D4, 1}, {NOTE_A4, 2}, {NOTE_G4, 4},
    {NOTE_E4, 1}, {NOTE_E5, 1.33}, {NOTE_C5, 0.66}, {NOTE_G4, 1}, {NOTE_FS4, 0.5}, {NOTE_A4, 0.5}, {NOTE_G4, 1.33}, {NOTE_G4, 0.66}, {NOTE_A3, 1}, {NOTE_AS3, 1}, {NOTE_B3, 5}
};

// Sad Violin (Violin)
const Note kViolin[] PROGMEM = {
    {NOTE_F5, 2}, {NOTE_B4, 2}, {NOTE_G5, 1.5}, {NOTE_F5, 0.5}, {NOTE_E5, 1.5}, {NOTE_D5, 0.5}, {NOTE_C5, 1}, {NOTE_A4, 1}, {NOTE_A5, 1.5}, {NOTE_G5, 0.5}, {NOTE_F5, 4},
    {NOTE_E5, 1.5}, {NOTE_F5, 0.5}, {NOTE_G5, 1}, {NOTE_E5, 1}, {NOTE_F5, 1.5}, {NOTE_B4, 0.5}, {NOTE_C5, 1}, {NOTE_D5, 1}, {NOTE_B5, 1.5}, {NOTE_E5, 0.5}, {NOTE_F5, 1}, {NOTE_G5, 1}, {NOTE_A5, 4}
};

// Succession Theme (Succession)
const Note kSuccession[] PROGMEM = {
    {NOTE_C3, 0.5}, {NOTE_B4, 0.1}, {NOTE_C5, 0.4}, {REST, 0.75}, {NOTE_B4, 0.125}, {NOTE_C5, 0.125},
    {NOTE_D5, 0.25}, {NOTE_C5, 0.25}, {NOTE_AS4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_FS4, 0.25}, {NOTE_G4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_G4, 0.25},
    {REST, 0.25}, {NOTE_G5, 0.25}, {NOTE_F5, 0.25}, {NOTE_DS5, 0.25}, {NOTE_CS5, 0.25}, {NOTE_D5, 0.25}, {NOTE_DS5, 0.25}, {NOTE_D5, 0.25},
    {NOTE_D5, 0.25}, {NOTE_C5, 0.25}, {NOTE_B4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_G4, 0.25}, {NOTE_F4, 0.25}, {NOTE_DS4, 0.25}, {NOTE_D4, 0.25},
    {NOTE_C3, 0.5}, {NOTE_B4, 0.1}, {NOTE_C5, 0.4}, {REST, 0.75}, {NOTE_B4, 0.125}, {NOTE_C5, 0.125},
    {NOTE_D5, 0.25}, {NOTE_C5, 0.25}, {NOTE_AS4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_FS4, 0.25}, {NOTE_G4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_G4, 0.25},
    {REST, 0.25}, {NOTE_G5, 0.25}, {NOTE_F5, 0.25}, {NOTE_DS5, 0.25}, {NOTE_CS5, 0.25}, {NOTE_D5, 0.25}, {NOTE_DS5, 0.25}, {NOTE_D5, 0.25},
    {NOTE_D5, 0.25}, {NOTE_C5, 0.25}, {NOTE_B4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_G4, 0.25}, {NOTE_F4, 0.25}, {NOTE_DS4, 0.25}, {NOTE_D4, 0.25}
};

// Test Note Sweep (Test)
const Note kTest[] PROGMEM = {
    {NOTE_C3, 0.5}, {NOTE_C3, 0.5}, {NOTE_C3, 0.5}, {NOTE_C3, 0.5},
    {NOTE_CS3, 0.25}, {NOTE_D3, 0.25}, {NOTE_DS3, 0.25}, {NOTE_E3, 0.25}, {NOTE_F3, 0.25}, {NOTE_FS3, 0.25}, 
    {NOTE_G3, 0.25}, {NOTE_GS3, 0.25}, {NOTE_A3, 0.25}, {NOTE_AS3, 0.25}, {NOTE_B3, 0.25},

    {NOTE_C4, 0.25}, {NOTE_CS4, 0.25}, {NOTE_D4, 0.25}, {NOTE_DS4, 0.25}, {NOTE_E4, 0.25}, {NOTE_F4, 0.25}, 
    {NOTE_FS4, 0.25}, {NOTE_G4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_A4, 0.25}, {NOTE_AS4, 0.25}, {NOTE_B4, 0.25},

    {NOTE_C5, 0.25}, {NOTE_CS5, 0.25}, {NOTE_D5, 0.25}, {NOTE_DS5, 0.25}, {NOTE_E5, 0.25}, {NOTE_F5, 0.25}, 
    {NOTE_FS5, 0.25}, {NOTE_G5, 0.25}, {NOTE_GS5, 0.25}, {NOTE_A5, 0.25}, {NOTE_AS5, 0.25}, {NOTE_B5, 0.25},

    {NOTE_C6, 0.25}, {NOTE_CS6, 0.25}, {NOTE_D6, 0.25}, {NOTE_DS6, 0.25}, {NOTE_E6, 0.25}, {NOTE_F6, 0.25}, 
    {NOTE_FS6, 0.25}, {NOTE_G6, 0.25}, {NOTE_GS6, 0.25}, {NOTE_A6, 0.25}, {NOTE_AS6, 0.25}, {NOTE_B6, 0.25},

    {NOTE_C7, 0.25}, {NOTE_CS7, 0.25}, {NOTE_D7, 0.25}, {NOTE_DS7, 0.25}, {NOTE_E7, 0.25}, {NOTE_F7, 0.25}, 
    {NOTE_FS7, 0.25}, {NOTE_G7, 0.25}, {NOTE_GS7, 0.25}, {NOTE_A7, 0.25}, {NOTE_AS7, 0.25}, {NOTE_B7, 0.25},

    {NOTE_C8, 0.5}, {NOTE_C8, 0.5}, {NOTE_C8, 0.5}, {NOTE_C8, 0.5},

    {NOTE_B7, 0.25}, {NOTE_AS7, 0.25}, {NOTE_A7, 0.25}, {NOTE_GS7, 0.25}, {NOTE_G7, 0.25}, {NOTE_FS7, 0.25}, 
    {NOTE_F7, 0.25}, {NOTE_E7, 0.25}, {NOTE_DS7, 0.25}, {NOTE_D7, 0.25}, {NOTE_CS7, 0.25}, {NOTE_C7, 0.25},

    {NOTE_B6, 0.25}, {NOTE_AS6, 0.25}, {NOTE_A6, 0.25}, {NOTE_GS6, 0.25}, {NOTE_G6, 0.25}, {NOTE_FS6, 0.25}, 
    {NOTE_F6, 0.25}, {NOTE_E6, 0.25}, {NOTE_DS6, 0.25}, {NOTE_D6, 0.25}, {NOTE_CS6, 0.25}, {NOTE_C6, 0.25},

    {NOTE_B5, 0.25}, {NOTE_AS5, 0.25}, {NOTE_A5, 0.25}, {NOTE_GS5, 0.25}, {NOTE_G5, 0.25}, {NOTE_FS5, 0.25}, 
    {NOTE_F5, 0.25}, {NOTE_E5, 0.25}, {NOTE_DS5, 0.25}, {NOTE_D5, 0.25}, {NOTE_CS5, 0.25}, {NOTE_C5, 0.25},

    {NOTE_B4, 0.25}, {NOTE_AS4, 0.25}, {NOTE_A4, 0.25}, {NOTE_GS4, 0.25}, {NOTE_G4, 0.25}, {NOTE_FS4, 0.25}, 
    {NOTE_F4, 0.25}, {NOTE_E4, 0.25}, {NOTE_DS4, 0.25}, {NOTE_D4, 0.25}, {NOTE_CS4, 0.25}, {NOTE_C4, 0.25},

    {NOTE_B3, 0.25}, {NOTE_AS3, 0.25}, {NOTE_A3, 0.25}, {NOTE_GS3, 0.25}, {NOTE_G3, 0.25}, {NOTE_FS3, 0.25}, 
    {NOTE_F3, 0.25}, {NOTE_E3, 0.25}, {NOTE_DS3, 0.25}, {NOTE_D3, 0.25}, {NOTE_CS3, 0.25}, 
    {NOTE_C3, 0.5}, {NOTE_C3, 0.5}, {NOTE_C3, 0.5}, {NOTE_C3, 0.5}
};

// Positive Feedback (Granted)
const Note kGranted[] PROGMEM = {
    {NOTE_C5, 0.2}, {NOTE_E5, 0.2}, {NOTE_G5, 0.2}, {NOTE_C6, 0.6}
};

// Negative Feedback (Denied)
const Note kDenied[] PROGMEM = {
    {NOTE_B3, 0.25}, {NOTE_F3, 0.5} 
};

// Pump Warning (Warning)
const Note kWarning[] PROGMEM = {
    {NOTE_A4, 1}, {REST, 1}, {NOTE_A4, 1}, {REST, 1}, {NOTE_A4, 1}
};

// --- SONG REGISTRY ---
#define COUNT(x) (sizeof(x) / sizeof(x[0]))
Song kSongList[] = {
  {"Daisy", kDaisy, COUNT(kDaisy), 200},
  {"Curiosity", kCuriosity, COUNT(kCuriosity), 120},
  {"Ultron", kUltron, COUNT(kUltron), 120},
  {"MV1", kMax, COUNT(kMax), 128},
  {"Tars", kInterstellar, COUNT(kInterstellar), 60},
  {"Panic", kAlarm, COUNT(kAlarm), 120},
  {"Morning", kMorning, COUNT(kMorning), 100},
  {"Sleep", kLullaby, COUNT(kLullaby), 100},
  {"Fnaf", kFnaf, COUNT(kFnaf), 108},
  {"Sponge", kSponge, COUNT(kSponge), 108},
  {"Violin", kViolin, COUNT(kViolin), 110},
  {"Succession", kSuccession, COUNT(kSuccession), 70},
  {"Test", kTest, COUNT(kTest), 160},
  {"Granted", kGranted, COUNT(kGranted), 240},
  {"Denied", kDenied, COUNT(kDenied), 240},
  {"Warning", kWarning, COUNT(kWarning), 120}
};
const int kSongCount = COUNT(kSongList);

// --- MUSIC CLASS ---
/**
 * @brief Manages background music playback using the passive buzzer.
 */
class MusicPlayer {
 private:
  bool is_playing_;
  const Note* current_song_notes_;
  int note_count_;
  int current_note_index_;
  int tempo_;
  unsigned long next_note_time_;

 public:
  MusicPlayer() : is_playing_(false), current_song_notes_(nullptr), note_count_(0), current_note_index_(0), tempo_(120) {}

  void Begin() {
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);
  }

/**
   * @brief Advances song playback.
   */
  void Update() {
    if (!is_playing_) return;

    if (millis() >= next_note_time_) {
      if (current_note_index_ < note_count_) {
        // Read directly from Flash Memory
        int freq = pgm_read_word(&(current_song_notes_[current_note_index_].freq));
        float beats = pgm_read_float(&(current_song_notes_[current_note_index_].duration_beats));

        // Calculate absolute duration in ms based on tempo
        int beat_duration = 60000 / tempo_;
        int note_duration = beat_duration * beats;

        if (freq != REST) {
          // Play for 90% of duration to create separation
          tone(PIN_BUZZER, freq, note_duration * 0.9);
        }
        
        next_note_time_ = millis() + note_duration;
        current_note_index_++;
      } else {
        Stop();
        Serial.println(F("ALERT:SONG_COMPLETE"));
      }
    }
  }

/**
   * @brief Plays a specific note by name.
   */
  void PlayNote(String note_name, int duration_sec = 0) {
    char buffer[5];
    int freq = 0;
    
    // Scan lookup table
    for (int i = 0; i < kNoteTableSize; i++) {
        memcpy_P(buffer, &kNoteTable[i].name, 5);
        if (note_name.equalsIgnoreCase(buffer)) {
            freq = pgm_read_word(&(kNoteTable[i].frequency));
            break;
        }
    }

    if (freq > 0) {
        Stop();
        
        int duration_ms = (duration_sec > 0) ? (duration_sec * 1000) : 1000;
        
        tone(PIN_BUZZER, freq, duration_ms);
        
        Serial.print(F("ACK:PLAY_NOTE,")); 
        Serial.print(note_name);
        Serial.print(",");
        Serial.println(duration_ms);
    } else {
        Serial.println(F("ERROR:UNKNOWN_NOTE"));
    }
  }

/**
   * @brief Starts playback of a predefined song or random track.
   */
  void PlaySong(String target) {
    Stop();
    
    // Random selection
    if (target.equalsIgnoreCase("RANDOM")) {
        int r = random(0, kSongCount);
        target = kSongList[r].name;
    }
    
    // Search song registry
    for(int i=0; i<kSongCount; i++) {
        if (target.equalsIgnoreCase(kSongList[i].name)) {
            current_song_notes_ = kSongList[i].notes;
            note_count_ = kSongList[i].num_notes;
            tempo_ = kSongList[i].tempo;
            
            is_playing_ = true;
            current_note_index_ = 0;
            next_note_time_ = millis();
            
            Serial.print(F("ACK:PLAY_SONG,")); Serial.println(kSongList[i].name);
            return;
        }
    }
    
    // Fallback: If no song found, try playing it as a single note
    PlayNote(target);
  }

  void Stop() {
    noTone(PIN_BUZZER);
    is_playing_ = false;
    Serial.println(F("ACK:MUSIC_STOP"));
  }

  bool IsPlaying() const { return is_playing_; }
};

#endif  // AEROSENSE_MUSIC_H_