from unittest.mock import MagicMock

from invesalius import constants
from invesalius.data.tcp_trigger_connection import ESP32TCPTriggerConnection


def test_tcp_trigger_connects_and_sends_trigger(mocker):
    socket_connection = MagicMock()
    socket_connection.recv.side_effect = [b"READY\n", b"PULSE\n"]
    create_connection = mocker.patch(
        "invesalius.data.tcp_trigger_connection.socket.create_connection",
        return_value=socket_connection,
    )
    mocker.patch("invesalius.data.tcp_trigger_connection.Publisher.sendMessage")
    connection = ESP32TCPTriggerConnection("192.168.4.1", 7000, 4.0)

    assert connection.Connect() is True
    assert connection.SendPulse() is True

    create_connection.assert_called_once_with(("192.168.4.1", 7000), timeout=4.0)
    socket_connection.sendall.assert_called_once_with(constants.ESP32_TRIGGER_COMMAND)


def test_tcp_trigger_fails_when_esp32_does_not_send_ready(mocker):
    socket_connection = MagicMock()
    socket_connection.recv.return_value = b"PONG\n"
    mocker.patch(
        "invesalius.data.tcp_trigger_connection.socket.create_connection",
        return_value=socket_connection,
    )
    mocker.patch("invesalius.data.tcp_trigger_connection.Publisher.sendMessage")
    connection = ESP32TCPTriggerConnection("192.168.4.1", 7000, 4.0)

    assert connection.Connect() is False
    socket_connection.close.assert_called_once_with()
