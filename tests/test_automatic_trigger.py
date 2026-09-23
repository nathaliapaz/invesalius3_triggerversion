from unittest.mock import MagicMock

from invesalius.navigation.navigation import Navigation


def make_navigation():
    """Create the minimal Navigation state needed for automatic-trigger tests."""
    navigation = object.__new__(Navigation)
    navigation.coil_at_target = False
    navigation.automatic_trigger_enabled = True
    navigation._automatic_trigger_timer = None
    navigation._automatic_trigger_fired = False
    navigation.serial_port_in_use = True
    navigation.serial_port_connection = MagicMock()
    return navigation


def test_automatic_trigger_fires_once_after_stable_target(mocker):
    navigation = make_navigation()
    timer = MagicMock()
    call_later = mocker.patch(
        "invesalius.navigation.navigation.wx.CallLater", return_value=timer
    )
    mocker.patch("invesalius.navigation.navigation.Publisher.sendMessage")

    Navigation.CoilAtTarget(navigation, True)
    Navigation.CoilAtTarget(navigation, True)

    call_later.assert_called_once_with(2000, navigation._fire_automatic_trigger)
    Navigation._fire_automatic_trigger(navigation)

    navigation.serial_port_connection.SendPulse.assert_called_once_with()
    assert navigation._automatic_trigger_fired is True
    assert navigation.automatic_trigger_enabled is False


def test_auto_can_remain_enabled_after_fire_when_policy_is_disabled(mocker):
    navigation = make_navigation()
    navigation.coil_at_target = True
    mocker.patch("invesalius.navigation.navigation.Publisher.sendMessage")
    mocker.patch("invesalius.navigation.navigation.const.AUTOMATIC_TRIGGER_DISABLE_AFTER_FIRE", False)

    Navigation._fire_automatic_trigger(navigation)

    navigation.serial_port_connection.SendPulse.assert_called_once_with()
    assert navigation.automatic_trigger_enabled is True


def test_leaving_target_cancels_pending_automatic_trigger(mocker):
    navigation = make_navigation()
    timer = MagicMock()
    mocker.patch("invesalius.navigation.navigation.wx.CallLater", return_value=timer)
    mocker.patch("invesalius.navigation.navigation.Publisher.sendMessage")

    Navigation.CoilAtTarget(navigation, True)
    Navigation.CoilAtTarget(navigation, False)

    timer.Stop.assert_called_once_with()
    assert navigation._automatic_trigger_timer is None
    assert navigation._automatic_trigger_fired is False
