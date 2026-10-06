# ESP32 Wi-Fi TCP test bridge

This is the Wi-Fi trigger test for InVesalius. It uses D13/GPIO13 with the
same active-low, two-second LED pulse configured in the previous USB-serial
test. It does **not** use MAX3232, DB26, UART, or MagPy commands.

The ESP32 creates a Wi-Fi access point and accepts one TCP client. The test
protocol is:

- computer -> ESP32: `PING`;
- ESP32 -> computer: `READY` when the connection opens and `PONG` after a
  `PING`.
- InVesalius -> ESP32: `TRIGGER`; ESP32 drives D13 LOW for 2 seconds, returns
  D13 HIGH, then replies `PULSE`.

## 1. Configure Wi-Fi locally

In PowerShell, from this folder, create your private configuration file:

```powershell
Copy-Item include\wifi_config.h.example include\wifi_config.h
```

Open `include/wifi_config.h` in VS Code. Choose a unique password with at
least eight characters. That private file is ignored by Git and must never be
committed.

The ESP32's default access-point IP is `192.168.4.1` and the TCP port is
`7000`.

## 2. Upload and connect

1. Build and upload this folder using PlatformIO.
2. Disconnect the programming USB cable if desired; the ESP32 remains powered
   from the programming USB only for this network test.
3. On the computer, connect Wi-Fi to the SSID configured in `wifi_config.h`.
   Windows may report that the network has no internet; that is expected.
4. Use any TCP terminal client to connect to `192.168.4.1` on port `7000`.
   Send this line, followed by Enter:

```text
PING
```

The ESP32 must answer `PONG`. Its USB serial monitor also prints that it
received `PING` and sent `PONG`.

## InVesalius trigger test

1. Connect the computer running InVesalius to the ESP32 Wi-Fi access point.
2. Start InVesalius and, before starting navigation, enable the new `WIFI`
   button in the Navigation controls.
3. Start navigation. InVesalius connects to `192.168.4.1:7000` and waits for
   the ESP32 `READY` line.
4. When the automatic-trigger conditions are met, InVesalius sends `TRIGGER`.
   The LED follows the configured active-low, two-second pulse and the ESP32
   replies `PULSE`.

## Safety boundary

No Magstim pins, MAX3232 pins, DB26, or UART are configured. A later phase
will add a byte-for-byte TCP-to-UART bridge, then separately validate the
Magstim remote-control protocol.
