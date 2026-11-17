import unittest
from unittest.mock import patch

import hidpp


class IdentityTests(unittest.TestCase):
    def test_device_name_is_read_in_chunks(self):
        device = object.__new__(hidpp.HidppDevice)
        name = b"PRO X Wireless"
        offsets = []

        def send(index, function, params=b""):
            if function == 2:
                return bytes([0, 0, index, 0, hidpp.DEVICE_TYPE_MOUSE])
            if function == 0:
                return bytes([0, 0, index, 0, len(name)])
            offset = params[0]
            offsets.append(offset)
            return bytes([0, 0, index, 0]) + name[offset:offset + 3]

        device.get_feature = lambda feature: 3
        device._send = send
        self.assertEqual(device.read_identity(), (hidpp.DEVICE_TYPE_MOUSE, name.decode()))
        self.assertEqual(offsets, [0, 3, 6, 9, 12])

    def test_short_identity_response_is_rejected(self):
        device = object.__new__(hidpp.HidppDevice)
        device.get_feature = lambda feature: 3
        device._send = lambda index, function, params=b"": b"\0\0\0\0"
        with self.assertRaises(hidpp.HidppError):
            device.read_identity()

    def test_unrelated_function_response_is_ignored(self):
        device = object.__new__(hidpp.HidppDevice)
        device.info = {"in_len": 20}
        device.device_index = 1
        device._drain = lambda: None
        responses = iter([
            bytes([0x11, 1, 3, 0x01, 99]),
            bytes([0x11, 1, 0x8F, 3, 0x01, 8]),
            bytes([0x11, 1, 3, 0x11, 42]),
        ])

        class FakeHandle:
            def write(self, packet, timeout):
                pass

            def read(self, length, timeout):
                return next(responses)

        device.handle = FakeHandle()
        response = device._send_once(bytes([0x11, 1, 3, 0x11]), 3, 20, 1000)
        self.assertEqual(response[4], 42)

    def test_only_target_mouse_battery_is_read(self):
        channel = {"receiver": True, "pid": 0xC547}
        cases = {
            1: (1, "Keyboard", 10),
            2: (hidpp.DEVICE_TYPE_MOUSE, "Other Mouse", 20),
            3: (hidpp.DEVICE_TYPE_MOUSE, "PRO X Wireless", 87),
        }
        battery_reads = []

        class FakeHandle:
            def close(self):
                pass

        class FakeDevice:
            def __init__(self, info, receiver, device_index):
                self.index = device_index
                self.handle = FakeHandle()

            def read_identity(self):
                device_type, name, _ = cases[self.index]
                return device_type, name

            def read_battery(self):
                battery_reads.append(self.index)
                return cases[self.index][2], hidpp.STATUS_DISCHARGING, 0, "test"

        with patch.object(hidpp, "_hidpp_channels", return_value=[channel]), \
                patch.object(hidpp, "_channel_responds", return_value=True), \
                patch.object(hidpp, "_candidate_devices", return_value=[1, 2, 3]), \
                patch.object(hidpp, "HidppDevice", FakeDevice):
            reading = hidpp.read_battery()
            self.assertEqual((reading.device_name, reading.percent), ("PRO X Wireless", 87))
            self.assertEqual(battery_reads, [3])

    def test_unidentified_device_is_not_accepted(self):
        channel = {"receiver": True, "pid": 0xC547}

        class FakeDevice:
            def __init__(self, info, receiver, device_index):
                self.handle = self

            def close(self):
                pass

            def read_identity(self):
                raise hidpp.HidppError("identity unavailable")

            def read_battery(self):
                raise AssertionError("unidentified device must not be read")

        with patch.object(hidpp, "_hidpp_channels", return_value=[channel]), \
                patch.object(hidpp, "_channel_responds", return_value=True), \
                patch.object(hidpp, "_candidate_devices", return_value=[1]), \
                patch.object(hidpp, "HidppDevice", FakeDevice):
            reading = hidpp.read_battery()
            self.assertIsNone(reading.percent)
            self.assertIsNotNone(reading.error)


if __name__ == "__main__":
    unittest.main()
