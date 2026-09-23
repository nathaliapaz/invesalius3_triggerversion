from unittest.mock import MagicMock

from invesalius import constants
from invesalius.data.serial_port_connection import SerialPortConnection


def make_connection():
    connection = SerialPortConnection(
        com_port="COM1",
        baud_rate=115200,
        serial_port_queue=MagicMock(),
        event=MagicMock(),
        sleep_nav=0.01,
    )
    connection.connection = MagicMock()
    return connection


def test_send_pulse_sends_one_esp32_trigger_command(mocker):
    connection = make_connection()
    mocker.patch("invesalius.data.serial_port_connection.Publisher.sendMessage")

    assert connection.SendPulse() is True
    connection.connection.write.assert_called_once_with(constants.ESP32_TRIGGER_COMMAND)
    connection.connection.flush.assert_called_once_with()


def test_send_pulse_fails_without_serial_connection():
    connection = make_connection()
    connection.connection = None

    assert connection.SendPulse() is False


def test_only_explicit_esp32_pulse_event_is_accepted():
    assert SerialPortConnection._has_pulse_event([b"READY\r\n", b"PONG\r\n"]) is False
    assert SerialPortConnection._has_pulse_event([b"DRY_RUN_TRIGGER\r\n"]) is False
    assert SerialPortConnection._has_pulse_event([b"PULSE\r\n"]) is True
