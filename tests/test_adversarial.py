import hashlib
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from archive_corpus import Member, corpus, unicode_extra, zip_bytes

from zipnameguard import ScanError, scan_archive
from zipnameguard.cli import main


class CorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fixture.zip"

    def test_exact_corpus_results(self) -> None:
        for name, case in corpus().items():
            with self.subTest(case=name):
                content = zip_bytes(case.members)
                self.path.write_bytes(content)
                report = scan_archive(self.path)
                self.assertEqual(tuple(f.code for f in report.findings), case.codes)
                self.assertEqual(report.entries, len(case.members))
                self.assertEqual(self.path.read_bytes(), content)
                for finding in report.findings:
                    self.assertEqual(finding.member, case.members[finding.entry_index].name)
                    warning_codes = {
                        "long-component",
                        "directory-metadata",
                        "alternate-name-metadata",
                        "noncanonical-path",
                        "symlink-entry",
                        "special-entry",
                    }
                    self.assertEqual(
                        finding.severity, "warning" if finding.code in warning_codes else "error"
                    )

    def test_deterministic_writer(self) -> None:
        approved = json.loads(Path(__file__).with_name("corpus-manifest.json").read_text())
        self.assertEqual(set(approved), set(corpus()))
        for name, case in corpus().items():
            with self.subTest(case=name):
                content = zip_bytes(case.members)
                self.assertEqual(hashlib.sha256(content).hexdigest(), approved[name]["sha256"])

    def test_ordinary_fixtures_have_valid_payloads(self) -> None:
        for name in ("valid-basic", "valid-unicode", "valid-boundaries", "legacy-cp437"):
            self.path.write_bytes(zip_bytes(corpus()[name].members))
            with self.subTest(case=name), zipfile.ZipFile(self.path) as archive:
                self.assertIsNone(archive.testzip())

    def test_writer_preserves_names_including_windows_backslash(self) -> None:
        names = ("a\\b", "a\x00b", "", "日本語")
        self.path.write_bytes(zip_bytes(tuple(Member(name) for name in names)))
        with zipfile.ZipFile(self.path) as archive:
            self.assertEqual(tuple(i.orig_filename for i in archive.infolist()), names)

    def test_many_entries_limit_boundary(self) -> None:
        self.path.write_bytes(zip_bytes(tuple(Member(f"{i}.txt", b"") for i in range(10001))))
        self.assertEqual(scan_archive(self.path, max_entries=10001).entries, 10001)
        with self.assertRaisesRegex(ScanError, "10001.*10000"):
            scan_archive(self.path, max_entries=10000)

    def test_malformed_metadata(self) -> None:
        good = zip_bytes((Member("a"),))
        bad_signature = good.replace(b"PK\x01\x02", b"BAD!", 1)
        unsupported_version = bytearray(good)
        central = good.index(b"PK\x01\x02")
        struct.pack_into("<H", unsupported_version, central + 6, 999)
        cases = {
            "missing-eocd": good[:-22],
            "truncated-eocd": good[:-1],
            "invalid-central-signature": bad_signature,
            "invalid-utf8": zip_bytes((Member(b"\xff"),)),
            "invalid-extra": zip_bytes((Member("a", extra=b"\x75\x70\xff\xff"),)),
            "unsupported-version": bytes(unsupported_version),
        }
        for name, content in cases.items():
            with self.subTest(case=name):
                self.path.write_bytes(content)
                with self.assertRaises(ScanError):
                    scan_archive(self.path)

    def test_known_non_goals_do_not_validate_payload_or_local_header(self) -> None:
        good = zip_bytes((Member("safe", b"payload"),))
        for content in (
            good.replace(b"payload", b"corrupt", 1),
            good.replace(b"PK\x03\x04", b"BAD!", 1),
        ):
            self.path.write_bytes(content)
            self.assertEqual(scan_archive(self.path).findings, ())
            with zipfile.ZipFile(self.path) as archive, self.assertRaises(zipfile.BadZipFile):
                archive.read("safe")

    def test_parser_warnings_do_not_break_json_contract(self) -> None:
        import warnings
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO
        from unittest.mock import patch

        self.path.write_bytes(zip_bytes((Member("safe", extra=unicode_extra(b"safe", "")),)))
        output, error = StringIO(), StringIO()
        original = zipfile.ZipFile

        def warning_parser(*args, **kwargs):
            warnings.warn("Ambiguous ZIP metadata", UserWarning, stacklevel=2)
            return original(*args, **kwargs)

        with patch("zipnameguard.scan.zipfile.ZipFile", side_effect=warning_parser):
            with redirect_stdout(output), redirect_stderr(error):
                result = main(["--json", str(self.path)])
        self.assertEqual(error.getvalue(), "")
        self.assertEqual(result, 2)
        self.assertTrue(json.loads(output.getvalue())["errors"])

    def test_nul_input_path_has_useful_api_error(self) -> None:
        with self.assertRaisesRegex(ScanError, "Cannot inspect"):
            scan_archive("bad\x00path.zip")

    def test_real_empty_unicode_extra_has_no_stderr_leak(self) -> None:
        import warnings
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO

        self.path.write_bytes(zip_bytes((Member("safe", extra=unicode_extra(b"safe", "")),)))
        output, error = StringIO(), StringIO()
        with warnings.catch_warnings(), redirect_stdout(output), redirect_stderr(error):
            warnings.simplefilter("always")
            status = main(["--strict", "--json", str(self.path)])
        self.assertEqual(error.getvalue(), "")
        # Older parsers ignore this extension; newer ones warn/reject an empty override.
        self.assertIn(status, (1, 2))
        result = json.loads(output.getvalue())
        if status == 1:
            self.assertEqual(
                [f["code"] for f in result["reports"][0]["findings"]], ["alternate-name-metadata"]
            )
        else:
            self.assertTrue(result["errors"])
            self.assertIn("unicode", result["errors"][0]["message"].lower())

    def test_zip64_central_metadata_with_small_payload(self) -> None:
        good = zip_bytes((Member("a", b"payload"),))
        local_end = good.index(b"PK\x01\x02")
        central = bytearray(good[local_end:-22])
        struct.pack_into("<II", central, 20, 0xFFFFFFFF, 0xFFFFFFFF)
        extra = struct.pack("<HHQQ", 1, 16, 7, 7)
        struct.pack_into("<H", central, 30, len(extra))
        central.extend(extra)
        end = bytearray(good[-22:])
        struct.pack_into("<I", end, 12, len(central))
        self.path.write_bytes(good[:local_end] + central + end)
        self.assertEqual(scan_archive(self.path).findings, ())
        with zipfile.ZipFile(self.path) as archive:
            self.assertEqual(archive.read("a"), b"payload")

    def test_bounded_metadata_mutations_have_no_untranslated_exceptions(self) -> None:
        good = zip_bytes((Member("fixture.txt"),))
        central = good.index(b"PK\x01\x02")
        # Bounded 16-bit metadata fields; never mutate payload sizes or allocate huge buffers.
        for offset in (6, 8, 10, 12, 14, 28, 30, 32, 34):
            for value in (0, 1, 4, 63, 255):
                content = bytearray(good)
                struct.pack_into("<H", content, central + offset, value)
                self.path.write_bytes(content)
                with self.subTest(offset=offset, value=value):
                    try:
                        scan_archive(self.path)
                    except ScanError:
                        pass
