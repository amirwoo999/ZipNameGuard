import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from zipnameguard import ScanError, scan_archive


class ScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fixture.zip"

    def archive(self, *names: str) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.path, "w") as archive:
                for name in names:
                    archive.writestr(name, "content")

    def test_problem_reproduction_crc_passes_nonportable_archive(self) -> None:
        self.archive("SHOULDERS.md", "shoulders.md", "NUL.txt")
        with zipfile.ZipFile(self.path) as archive:
            self.assertIsNone(archive.testzip())
        report = scan_archive(self.path)
        self.assertTrue(report.has_errors)
        self.assertEqual(
            {f.code for f in report.findings}, {"portable-name-collision", "windows-device"}
        )

    def test_clean_and_empty(self) -> None:
        for names in ((), ("a/", "a/b")):
            self.archive(*names)
            self.assertFalse(scan_archive(self.path).findings)

    def test_no_payload_reads_or_writes(self) -> None:
        self.archive("../outside", "a", "A")
        original = self.path.read_bytes()
        with patch.object(zipfile.ZipFile, "open", side_effect=AssertionError("payload opened")):
            self.assertTrue(scan_archive(self.path).has_errors)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_missing_corrupt_and_directory(self) -> None:
        with self.assertRaises(ScanError):
            scan_archive(self.path)
        with self.assertRaises(ScanError):
            scan_archive(self.path.parent)
        self.path.write_bytes(b"not a ZIP")
        with self.assertRaises(ScanError):
            scan_archive(self.path)

    def test_limits(self) -> None:
        self.archive("a", "b")
        with self.assertRaisesRegex(ScanError, "bytes"):
            scan_archive(self.path, max_archive_bytes=1)
        with self.assertRaisesRegex(ScanError, "entries"):
            scan_archive(self.path, max_entries=1)
        self.assertEqual(scan_archive(self.path, max_entries=2).entries, 2)

    def test_invalid_api_limits(self) -> None:
        for bad in (0, -1, True, 1.5):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                scan_archive(self.path, max_entries=bad)
            with self.subTest(size=bad), self.assertRaises(ValueError):
                scan_archive(self.path, max_archive_bytes=bad)

    def test_byte_limit_exact_boundary_and_permission_error(self) -> None:
        self.archive("a")
        size = self.path.stat().st_size
        self.assertEqual(scan_archive(self.path, max_archive_bytes=size).entries, 1)
        with self.assertRaises(ScanError):
            scan_archive(self.path, max_archive_bytes=size - 1)
        with patch("builtins.open", side_effect=PermissionError("permission denied")):
            with self.assertRaisesRegex(ScanError, "permission denied"):
                scan_archive(self.path)

    def test_nul_from_real_central_directory(self) -> None:
        self.archive("aXb")
        data = self.path.read_bytes().replace(b"aXb", b"a\x00b")
        self.path.write_bytes(data)
        self.assertEqual(scan_archive(self.path).findings[0].member, "a\x00b")
