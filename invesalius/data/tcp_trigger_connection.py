# --------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
# --------------------------------------------------------------------------
"""TCP connection used by the local ESP32 Wi-Fi trigger test."""

import socket
import threading
import time

from invesalius import constants
from invesalius.pubsub import pub as Publisher


class ESP32TCPTriggerConnection:
    """Send trigger commands to one ESP32 access point over TCP."""

    def __init__(self, host, port, timeout_seconds):
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds
        self.connection = None
        self._receive_buffer = b""
        self._lock = threading.Lock()

    def Connect(self):
        try:
            self.connection = socket.create_connection(
                (self.host, self.port), timeout=self.timeout_seconds
            )
            self.connection.settimeout(self.timeout_seconds)
            if self._read_line() != b"READY":
                print("ESP32 Wi-Fi init error: expected READY.")
                self.Disconnect()
                return False
        except OSError as error:
            print(f"ESP32 Wi-Fi init error: {error}")
            self.connection = None
            return False

        print(f"ESP32 Wi-Fi trigger connected to {self.host}:{self.port}.")
        Publisher.sendMessage("Wi-Fi trigger connection", state=True)
        return True

    def Disconnect(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except OSError:
                pass
        self.connection = None
        self._receive_buffer = b""
        Publisher.sendMessage("Wi-Fi trigger connection", state=False)

    def SendPulse(self):
        """Request one ESP32 D13 pulse and wait for its explicit completion."""
        if self.connection is None:
            print("ESP32 Wi-Fi error: connection is not active.")
            return False

        with self._lock:
            try:
                self.connection.sendall(constants.ESP32_TRIGGER_COMMAND)
                deadline = time.monotonic() + self.timeout_seconds
                while time.monotonic() < deadline:
                    self.connection.settimeout(max(deadline - time.monotonic(), 0.01))
                    response = self._read_line()
                    if response == b"PULSE":
                        Publisher.sendMessage("ESP32 trigger command sent")
                        return True
                    if response.startswith(b"ERROR"):
                        return False
            except OSError as error:
                print(f"ESP32 Wi-Fi trigger error: {error}")
                self.Disconnect()
                return False

        print("ESP32 Wi-Fi trigger error: PULSE response timed out.")
        return False

    def _read_line(self):
        while b"\n" not in self._receive_buffer:
            chunk = self.connection.recv(128)
            if not chunk:
                raise OSError("ESP32 closed the TCP connection")
            self._receive_buffer += chunk

        line, self._receive_buffer = self._receive_buffer.split(b"\n", 1)
        return line.strip().upper()
