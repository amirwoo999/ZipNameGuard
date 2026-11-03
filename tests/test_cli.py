import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clean = self.root / "clean file.zip"
        self.bad = self.root / "bad.zip"
        self.warning = self.root / "warning.zip"
        for path, names in (
            (self.clean, ["a"]),
            (self.bad, ["A", "a\x1b[31m"]),
            (self.warning, ["./a"]),
        ):
            with zipfile.ZipFile(path, "w") as archive:
                for name in names:
                    archive.writestr(name, "payload")

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "zipnameguard", *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_help_version(self) -> None:
        for flag in ("--help", "--version"):
            self.assertEqual(self.run_cli(flag).returncode, 0)
        self.assertEqual(self.run_cli("--version").stdout, "ZipNameGuard 0.1.0\n")
        self.assertIn("Exit:", self.run_cli("--help").stdout)
        self.assertIn("does not mean extraction is safe", self.run_cli("--help").stdout)

    def test_exit_statuses(self) -> None:
        for paths, expected in (
            ((self.clean,), 0),
            ((self.bad,), 1),
            ((self.root / "missing",), 2),
            ((self.bad, self.root / "missing", self.clean), 2),
        ):
            with self.subTest(paths=paths):
                self.assertEqual(self.run_cli(*(str(p) for p in paths)).returncode, expected)

    def test_json_reports_success_and_errors(self) -> None:
        result = self.run_cli("--json", str(self.bad), str(self.root / "missing"), str(self.clean))
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(len(data["reports"]), 2)
        self.assertEqual(len(data["errors"]), 1)
        self.assertEqual(result.stderr, "")
        finding = data["reports"][0]["findings"][0]
        self.assertEqual(
            set(finding), {"code", "severity", "member", "entry_index", "message", "related_member"}
        )

    def test_terminal_escape(self) -> None:
        result = self.run_cli(str(self.bad))
        self.assertNotIn("\x1b", result.stdout)
        self.assertIn("\\u001b", result.stdout)

    def test_strict_and_override_config(self) -> None:
        config = self.root / "settings.toml"
        config.write_text("[zipnameguard]\nstrict = true\nmax_entries = 1\n", encoding="utf-8")
        self.assertEqual(self.run_cli(str(self.warning)).returncode, 0)
        self.assertEqual(self.run_cli("--strict", str(self.warning)).returncode, 1)
        self.assertEqual(self.run_cli("--config", str(config), str(self.warning)).returncode, 1)
        self.assertEqual(
            self.run_cli("--config", str(config), "--no-strict", str(self.warning)).returncode, 0
        )
        self.assertEqual(self.run_cli("--config", str(config), str(self.bad)).returncode, 2)
        self.assertEqual(
            self.run_cli("--config", str(config), "--max-entries", "2", str(self.bad)).returncode, 1
        )

    def test_invalid_config(self) -> None:
        config = self.root / "settings.toml"
        for content in (
            "[zipnameguard]\nstrict = 1",
            "[zipnameguard]\nmax_entries = false",
            "[zipnameguard]\nmax_entries = 0",
            "[zipnameguard]\nx = 1",
            "[other]",
            "not toml",
            "[zipnameguard]\nstrict = true\n[other]",
        ):
            with self.subTest(content=content):
                config.write_text(content, encoding="utf-8")
                result = self.run_cli("--json", "--config", str(config), str(self.clean))
                self.assertEqual(result.returncode, 2)
                self.assertTrue(json.loads(result.stdout)["errors"])

    def test_invalid_arguments(self) -> None:
        for value in ("0", "-1", "nope"):
            self.assertEqual(self.run_cli("--max-entries", value, str(self.clean)).returncode, 2)
        self.assertEqual(self.run_cli().returncode, 2)

    def test_deterministic_output(self) -> None:
        args = ("--json", str(self.bad))
        self.assertEqual(self.run_cli(*args).stdout, self.run_cli(*args).stdout)

    def test_json_golden_case_collision(self) -> None:
        path = self.root / "golden.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("README.txt", "one")
            archive.writestr("readme.txt", "two")
        result = self.run_cli("--json", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            json.loads(result.stdout),
            {
                "schema_version": 1,
                "errors": [],
                "reports": [
                    {
                        "archive": str(path),
                        "entries": 2,
                        "findings": [
                            {
                                "code": "portable-name-collision",
                                "severity": "error",
                                "entry_index": 1,
                                "member": "readme.txt",
                                "related_member": "README.txt",
                                "message": (
                                    "Case/normalization-insensitive filesystems "
                                    "(common on Windows/macOS) may merge these paths; "
                                    "rename one. Policy: NFC, casefold, trim dots/spaces."
                                ),
                            }
                        ],
                    }
                ],
            },
        )

    def test_leading_dash_path_and_unicode_input_path(self) -> None:
        path = self.root / "-日本語.zip"
        path.write_bytes(self.clean.read_bytes())
        result = subprocess.run(
            [sys.executable, "-m", "zipnameguard", "--json", "--", path.name],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["reports"][0]["archive"], path.name)

    def test_missing_invalid_utf8_and_directory_config(self) -> None:
        config = self.root / "bad.toml"
        for path in (config, self.root):
            self.assertEqual(self.run_cli("--config", str(path), str(self.clean)).returncode, 2)
        config.write_bytes(b"\xff\xfe")
        result = self.run_cli("--json", "--config", str(config), str(self.clean))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["errors"][0]["archive"], None)
        self.assertNotIn("Traceback", result.stderr)

    def test_size_config_override_and_empty_table(self) -> None:
        config = self.root / "settings.toml"
        config.write_text("[zipnameguard]\nmax_archive_bytes = 1\n", encoding="utf-8")
        self.assertEqual(self.run_cli("--config", str(config), str(self.clean)).returncode, 2)
        self.assertEqual(
            self.run_cli(
                "--config", str(config), "--max-archive-bytes", "10000", str(self.clean)
            ).returncode,
            0,
        )
        config.write_text("[zipnameguard]\n", encoding="utf-8")
        self.assertEqual(self.run_cli("--config", str(config), str(self.clean)).returncode, 0)

    def test_text_operational_error_is_actionable(self) -> None:
        result = self.run_cli(str(self.root / "missing.zip"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Cannot inspect archive", result.stderr)
        self.assertIn("missing.zip", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
