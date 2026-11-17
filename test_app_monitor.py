import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import gpw_battery
import hidpp


class MonitorTests(unittest.TestCase):
    def test_idle_popup_timer_stops(self):
        app = gpw_battery.App(demo=True)
        app.hwnd = 1
        app.popup = SimpleNamespace(visible=False)
        app.menu = SimpleNamespace(visible=False)
        with patch.object(gpw_battery.user32, "KillTimer") as kill, \
                patch.object(gpw_battery.user32, "GetCursorPos") as cursor:
            app._on_watch_timer()
        kill.assert_called_once_with(1, app.ID_TIMER_WATCH)
        cursor.assert_not_called()

    def test_refresh_wakes_single_monitor(self):
        app = gpw_battery.App()
        first_read = threading.Event()
        second_read = threading.Event()
        calls = []

        def read():
            calls.append(threading.current_thread())
            if len(calls) == 1:
                first_read.set()
            else:
                second_read.set()
            return hidpp.BatteryReading(percent=87)

        with patch.object(hidpp, "read_battery", side_effect=read):
            app._start_monitor()
            try:
                self.assertTrue(first_read.wait(2))
                app.refresh()
                self.assertTrue(second_read.wait(2))
                self.assertIs(calls[0], calls[1])
            finally:
                app._stop.set()
                app._refresh_requested.set()
                app._monitor.join(2)
                self.assertFalse(app._monitor.is_alive())


if __name__ == "__main__":
    unittest.main()
