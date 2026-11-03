import stat
import unittest
from zipfile import ZipInfo

from zipnameguard.rules import inspect_names


def check(*names: str) -> list[str]:
    return [finding.code for finding in inspect_names([ZipInfo(name) for name in names])]


class NameRulesTests(unittest.TestCase):
    def test_clean_including_explicit_directory_after_child(self) -> None:
        self.assertEqual(check("assets/readme.txt", "assets/", ".hidden", "日本語.txt"), [])

    def test_windows_devices(self) -> None:
        for name in ("CON", "aux.txt", "x/NUL.tar.gz", "COM¹.log", "LPT9", "CON .txt"):
            with self.subTest(name=name):
                self.assertIn("windows-device", check(name))
        self.assertEqual(check("COM0", "COM10", "console", "auxiliary.txt"), [])

    def test_windows_characters(self) -> None:
        for name in ("time:12", "a?b", "a*b", 'a"b', "a<b", "a>b", "a|b", "a\x1bb"):
            with self.subTest(name=name):
                self.assertIn("windows-character", check(name))

    def test_nul_uses_original_filename(self) -> None:
        entry = ZipInfo("good\x00bad")
        self.assertEqual(entry.filename, "good")
        finding = inspect_names([entry])[0]
        self.assertEqual(finding.member, "good\x00bad")
        self.assertEqual(finding.code, "windows-character")

    def test_trailing_characters(self) -> None:
        self.assertIn("trailing-dot-space", check("a./b"))
        self.assertIn("trailing-dot-space", check("a /b"))

    def test_absolute_and_drive_paths(self) -> None:
        for name in ("/etc/passwd", "C:relative.txt", "C:/file", "\\server\\share"):
            with self.subTest(name=name):
                self.assertIn("absolute-path", check(name))

    def test_parent_paths(self) -> None:
        for name in ("../outside", "a/../b", "a\\..\\b"):
            with self.subTest(name=name):
                self.assertIn("parent-path", check(name))

    def test_backslashes_and_noncanonical_paths(self) -> None:
        self.assertIn("backslash-path", check("a\\b"))
        for name in ("./a", "a//b", "a//", "/"):
            with self.subTest(name=name):
                self.assertIn("noncanonical-path", check(name))

    def test_duplicate(self) -> None:
        self.assertEqual(check("a", "a"), ["duplicate-entry"])
        self.assertEqual(check("a/", "a/"), ["duplicate-entry"])

    def test_case_and_unicode_collisions(self) -> None:
        for names in (("README", "readme"), ("café", "cafe\u0301"), ("a", "A.")):
            with self.subTest(names=names):
                self.assertIn("portable-name-collision", check(*names))

    def test_implicit_directory_collision(self) -> None:
        self.assertIn("portable-name-collision", check("Assets/a", "assets/b"))

    def test_file_directory_conflicts_in_both_orders(self) -> None:
        for names in (("a", "a/b"), ("a/b", "a"), ("A/", "a"), ("a/b", "A")):
            with self.subTest(names=names):
                self.assertIn("file-directory-conflict", check(*names))

    def test_normalized_path_alias(self) -> None:
        self.assertIn("normalized-path-collision", check("a/b", "a/./b"))
        self.assertIn("normalized-path-collision", check("a/b", "a\\b"))

    def test_symlinks_and_special_files(self) -> None:
        for mode, code in ((stat.S_IFLNK, "symlink-entry"), (stat.S_IFIFO, "special-entry")):
            entry = ZipInfo("link")
            entry.create_system = 3
            entry.external_attr = (mode | 0o777) << 16
            self.assertEqual(inspect_names([entry])[0].code, code)

    def test_empty_name(self) -> None:
        entry = ZipInfo("a")
        entry.orig_filename = ""
        self.assertEqual(inspect_names([entry])[0].code, "empty-name")

    def test_related_member_index_and_determinism(self) -> None:
        entries = [ZipInfo("A"), ZipInfo("a")]
        report = inspect_names(entries)
        self.assertEqual(report, inspect_names(entries))
        self.assertEqual(report[0].entry_index, 1)
        self.assertEqual(report[0].related_member, "A")

    def test_deep_paths_do_not_require_recursion_or_full_prefix_copies(self) -> None:
        prefix = "level/" * 2000
        self.assertEqual(check(prefix + "a", prefix + "b"), [])

    def test_directory_alias_still_reports_after_explicit_directory(self) -> None:
        self.assertIn("portable-name-collision", check("Assets/a", "assets/", "Assets/b"))

    def test_directory_metadata_variants(self) -> None:
        directory = ZipInfo("folder")
        directory.create_system = 0
        directory.external_attr = 0x10
        child = ZipInfo("folder/child")
        findings = inspect_names([directory, child])
        self.assertEqual([f.code for f in findings], ["directory-metadata"])
        mismatch = ZipInfo("folder/")
        mismatch.create_system = 3
        mismatch.external_attr = (stat.S_IFREG | 0o644) << 16
        self.assertEqual([f.code for f in inspect_names([mismatch])], ["directory-metadata"])

    def test_alternate_name_field_after_unrelated_extra(self) -> None:
        from archive_corpus import unicode_extra

        entry = ZipInfo("safe")
        entry.extra = b"\xfe\xca\x02\x00ab" + unicode_extra(b"safe", "other")
        self.assertEqual([f.code for f in inspect_names([entry])], ["alternate-name-metadata"])
        entry.extra = b"\xfe\xca\x02\x00ab"
        self.assertEqual(inspect_names([entry]), ())
