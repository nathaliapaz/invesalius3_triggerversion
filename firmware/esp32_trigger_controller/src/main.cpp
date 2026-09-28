#include <Arduino.h>

// This controller receives commands from InVesalius through the ESP32 USB
// serial port. The build flags in platformio.ini control whether TRIGGER
// produces a GPIO pulse; this file defaults to dry-run only when no flag is set.
#ifndef ENABLE_BNC_OUTPUT
#define ENABLE_BNC_OUTPUT 1
#endif

#ifndef TRIGGER_PIN
#define TRIGGER_PIN -1
#endif

#ifndef TRIGGER_ACTIVE_HIGH
#define TRIGGER_ACTIVE_HIGH 0
#endif

#ifndef PULSE_WIDTH_US
#define PULSE_WIDTH_US 2000000
#endif

namespace {
constexpr uint32_t SERIAL_BAUD_RATE = 115200;
constexpr size_t MAX_COMMAND_LENGTH = 32;

String command_buffer;

int active_level() {
  return TRIGGER_ACTIVE_HIGH ? HIGH : LOW;
}

int inactive_level() {
  return TRIGGER_ACTIVE_HIGH ? LOW : HIGH;
}

void wait_for_pulse_width() {
  // delay() yields to the ESP32 runtime while a multi-second level is held.
  // Keep the remainder in microseconds so shorter widths remain possible.
  const unsigned long milliseconds = PULSE_WIDTH_US / 1000UL;
  const unsigned int microseconds = PULSE_WIDTH_US % 1000UL;
  if (milliseconds > 0) {
    delay(milliseconds);
  }
  if (microseconds > 0) {
    delayMicroseconds(microseconds);
  }
}

void emit_trigger() {
#if ENABLE_BNC_OUTPUT
  if (TRIGGER_PIN < 0) {
    Serial.println("CONFIG_ERROR");
    return;
  }

  digitalWrite(TRIGGER_PIN, active_level());
  wait_for_pulse_width();
  digitalWrite(TRIGGER_PIN, inactive_level());

  // InVesalius treats only this exact line as a confirmed pulse event.
  Serial.println("PULSE");
#else
  // This response is intentionally not PULSE: dry-run mode must never be
  // recorded as a delivered stimulation event.
  Serial.println("DRY_RUN_TRIGGER");
#endif
}

void handle_command(const String& command) {
  if (command == "PING") {
    Serial.println("PONG");
  } else if (command == "STATUS") {
#if ENABLE_BNC_OUTPUT
    Serial.println("OUTPUT_ENABLED");
#else
    Serial.println("DRY_RUN");
#endif
  } else if (command == "TRIGGER") {
    emit_trigger();
  } else if (!command.isEmpty()) {
    Serial.println("UNKNOWN_COMMAND");
  }
}
}  // namespace

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  command_buffer.reserve(MAX_COMMAND_LENGTH);

#if ENABLE_BNC_OUTPUT
  if (TRIGGER_PIN >= 0) {
    pinMode(TRIGGER_PIN, OUTPUT);
    digitalWrite(TRIGGER_PIN, inactive_level());
  }
#endif

  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    const char character = static_cast<char>(Serial.read());
    if (character == '\n' || character == '\r') {
      if (!command_buffer.isEmpty()) {
        command_buffer.trim();
        command_buffer.toUpperCase();
        handle_command(command_buffer);
        command_buffer = "";
      }
    } else if (command_buffer.length() < MAX_COMMAND_LENGTH) {
      command_buffer += character;
    } else {
      command_buffer = "";
      Serial.println("COMMAND_TOO_LONG");
    }
  }
}
