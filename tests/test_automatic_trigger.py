from unittest.mock import MagicMock

from invesalius.navigation.navigation import Navigation


def make_navigation():
    """Create the minimal Navigation state needed for automatic-trigger tests."""
    navigation = object.__new__(Navigation)
    navigation.coil_at_target = False
    navigation.automatic_trigger_enabled = True
    navigation._automatic_trigger_timer = None
    navigation._automatic_trigger_cooldown_timer = None
    navigation._automatic_trigger_fired = False
    navigation.serial_port_in_use = True
    navigation.serial_port_connection = MagicMock()
    navigation.wifi_trigger_in_use = False
    navigation.wifi_trigger_connection = None
    return navigation


def test_automatic_trigger_starts_random_cooldown_after_stable_target(mocker):
    navigation = make_navigation()
    timer = MagicMock()
    call_later = mocker.patch(
        "invesalius.navigation.navigation.wx.CallLater", return_value=timer
    )
    mocker.patch("invesalius.navigation.navigation.random.uniform", return_value=5.0)
    mocker.patch("invesalius.navigation.navigation.Publisher.sendMessage")

    Navigation.CoilAtTarget(navigation, True)
    Navigation.CoilAtTarget(navigation, True)

    call_later.assert_called_once_with(2000, navigation._fire_automatic_trigger)
    Navigation._fire_automatic_trigger(navigation)

    navigation.serial_port_connection.SendPulse.assert_called_once_with()
    assert navigation._automatic_trigger_fired is True
    assert navigation.automatic_trigger_enabled is True
    call_later.assert_called_with(
        5000, navigation._complete_automatic_trigger_cooldown
    )


def test_cooldown_completion_requires_a_new_stable_target_check(mocker):
    navigation = make_navigation()
    navigation.coil_at_target = True
    navigation._automatic_trigger_fired = True
    navigation._automatic_trigger_cooldown_timer = MagicMock()
    mocker.patch("invesalius.navigation.navigation.Publisher.sendMessage")
    call_later = mocker.patch("invesalius.navigation.navigation.wx.CallLater")

    Navigation._complete_automatic_trigger_cooldown(navigation)

    assert navigation._automatic_trigger_fired is False
    call_later.assert_called_once_with(2000, navigation._fire_automatic_trigger)


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


def test_leaving_target_does_not_cancel_post_trigger_cooldown(mocker):
    navigation = make_navigation()
    cooldown_timer = MagicMock()
    navigation._automatic_trigger_fired = True
    navigation._automatic_trigger_cooldown_timer = cooldown_timer
    mocker.patch("invesalius.navigation.navigation.Publisher.sendMessage")

    Navigation.CoilAtTarget(navigation, False)

    cooldown_timer.Stop.assert_not_called()
    assert navigation._automatic_trigger_cooldown_timer is cooldown_timer
