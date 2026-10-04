"""Check the encoder against commands captured from the Moonboon app."""

from hashlib import sha256
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "moonboon" / "protocol.py"
)
spec = importlib.util.spec_from_file_location("moonboon_protocol", MODULE_PATH)
assert spec and spec.loader
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)

CAPTURE_HASHES = {
    "low": "dd8a7b5f5db1e0ea9cee09b6a2b903c0acd23c7d57c4dbf5ee384e241e42cdfb",
    "medium": "ea2b7396ba39ccadf37df1005c28097ed97116bd71bc3cc862c3e27eb84f930b",
    "high": "6b596b9f26ad39de01f82337d67d7d4e9762d9f1025c5df5cc9a5670f1b948f2",
    "start": "1fc2bc43c5d454fe099c86ba1a971758769f5acf7a5fdf1f47d0257feb4f102c",
    "stop": "8fc10116804ac01cc883901923ca4af49b32cfcd20965484bdb385d42181e322",
}


class ProtocolTest(unittest.TestCase):
    def test_commands_match_captured_writes(self) -> None:
        for command, expected_hash in CAPTURE_HASHES.items():
            with self.subTest(command=command):
                frame = protocol.encode_command(command, now_ms=1_700_000_000_000)
                self.assertEqual(sha256(frame).hexdigest(), expected_hash)

    def test_timestamp_changes_without_changing_program(self) -> None:
        first = protocol.encode_command("low", now_ms=1_700_000_000_000)
        second = protocol.encode_command("low", now_ms=1_700_000_000_001)
        self.assertEqual(first[:-1], second[:-1])
        self.assertNotEqual(first, second)

    def test_rejects_unknown_command(self) -> None:
        with self.assertRaises(ValueError):
            protocol.encode_command("reset")


if __name__ == "__main__":
    unittest.main()
