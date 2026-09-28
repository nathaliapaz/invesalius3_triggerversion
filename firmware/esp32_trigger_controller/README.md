# ESP32 trigger controller

This PlatformIO project is the USB-serial endpoint for InVesalius. The active
configuration in `platformio.ini` drives D13 normally HIGH and drives it LOW
for 2 seconds for each `TRIGGER` command. Build flags control this behaviour.

## USB protocol

InVesalius sends one newline-terminated command:

```text
TRIGGER\n
```

Firmware responses are line-based:

- `READY`, `PONG`, `DRY_RUN`, `DRY_RUN_TRIGGER`: diagnostic messages only.
- `PULSE`: emitted only after a physical GPIO pulse when BNC output has been
  explicitly enabled. InVesalius records this as a pulse event.

## PlatformIO use

Open this folder in VS Code with PlatformIO, connect the ESP32 by USB, select
the correct serial port, then build and upload. The generic `esp32dev` board
in `platformio.ini` is compatible with the ESP32 DevKit V1. This project uses
the pin labelled `D13`, normally GPIO 13 on that board; confirm that marking on
the physical board before wiring.

## Before enabling physical BNC output

Do **not** change `ENABLE_BNC_OUTPUT` from `0` until all of the following are
known and bench-tested by qualified personnel:

1. exact ESP32 board and GPIO used;
2. exact trigger-input BNC on the Magstim 3901-00 module;
3. required input voltage, polarity and minimum pulse duration;
4. isolated, electrically compatible interface circuit between ESP32 and BNC.

The ESP32 GPIO must not be wired directly to a medical-device BNC input.

## Current test pulse

`TRIGGER_ACTIVE_HIGH=0` makes the inactive state HIGH and the active state
LOW. `PULSE_WIDTH_US=2000000` holds the active LOW state for 2 seconds. This
is suitable for observing an LED test circuit. A long active-low level must
not be used with a stimulation input configured for level-triggered re-fire;
use edge-trigger mode and validate the actual interface separately.
