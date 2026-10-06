#include <Arduino.h>
#include <WiFi.h>
#include "wifi_config.h"

namespace {

constexpr uint32_t SERIAL_BAUD_RATE = 115200;
constexpr size_t MAX_COMMAND_LENGTH = 16;

#ifndef TRIGGER_PIN
#define TRIGGER_PIN 13
#endif

#ifndef TRIGGER_ACTIVE_HIGH
#define TRIGGER_ACTIVE_HIGH 0
#endif

#ifndef PULSE_WIDTH_MS
#define PULSE_WIDTH_MS 2000
#endif

WiFiServer tcp_server(WIFI_TCP_PORT);
WiFiClient active_client;
String command_buffer;

int active_level() {
  return TRIGGER_ACTIVE_HIGH ? HIGH : LOW;
}

int inactive_level() {
  return TRIGGER_ACTIVE_HIGH ? LOW : HIGH;
}

bool client_is_connected() {
  return active_client && active_client.connected();
}

void disconnect_client() {
  if (active_client) {
    active_client.stop();
  }
  command_buffer = "";
  Serial.println("TCP client disconnected.");
}

void handle_command(String command) {
  command.trim();
  command.toUpperCase();

  if (command == "PING") {
    active_client.print("PONG\n");
    Serial.println("TCP: PING received; PONG sent.");
  } else if (command == "TRIGGER") {
    digitalWrite(TRIGGER_PIN, active_level());
    delay(PULSE_WIDTH_MS);
    digitalWrite(TRIGGER_PIN, inactive_level());
    active_client.print("PULSE\n");
    Serial.println("TCP: TRIGGER received; D13 pulse completed.");
  }
}

void accept_new_client() {
  WiFiClient candidate = tcp_server.available();
  if (!candidate) {
    return;
  }

  if (client_is_connected()) {
    // One controlling computer at a time. Do not allow a second client to
    // inject data into a future Magstim bridge.
    candidate.print("BUSY\n");
    candidate.stop();
    return;
  }

  if (active_client) {
    disconnect_client();
  }

  active_client = candidate;
  active_client.setNoDelay(true);
  command_buffer = "";
  active_client.print("READY\n");
  Serial.print("TCP client connected from ");
  Serial.println(active_client.remoteIP());
}

void read_from_computer() {
  while (client_is_connected() && active_client.available()) {
    const char next_character = static_cast<char>(active_client.read());

    if (next_character == '\n') {
      handle_command(command_buffer);
      command_buffer = "";
    } else if (next_character != '\r') {
      if (command_buffer.length() >= MAX_COMMAND_LENGTH) {
        command_buffer = "";
      } else {
        command_buffer += next_character;
      }
    }
  }
}

}  // namespace

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  command_buffer.reserve(MAX_COMMAND_LENGTH);
  delay(200);

  pinMode(TRIGGER_PIN, OUTPUT);
  digitalWrite(TRIGGER_PIN, inactive_level());

  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD)) {
    Serial.println("ERROR: failed to start Wi-Fi access point.");
    return;
  }

  tcp_server.begin();
  tcp_server.setNoDelay(true);

  Serial.println("ESP32 Wi-Fi TCP test bridge ready.");
  Serial.print("SSID: ");
  Serial.println(WIFI_AP_SSID);
  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());
  Serial.print("TCP port: ");
  Serial.println(WIFI_TCP_PORT);
}

void loop() {
  accept_new_client();

  if (active_client && !active_client.connected()) {
    disconnect_client();
    return;
  }

  read_from_computer();
}
