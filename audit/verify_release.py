"""Build and verify a release in disposable clean environments, without publishing."""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def python_in(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def verify(output: Path, artifacts: Path | None) -> None:
    sandbox_root = (ROOT / "audit" / "verification-sandbox").resolve()
    sandbox_root.relative_to(ROOT)
    sandbox_root.mkdir(exist_ok=True)
    record: dict[str, object] = {
        "platform": platform.platform(),
        "python": sys.version,
        "published": False,
        "commands": [],
    }
    commands: list[dict[str, object]] = []
    record["commands"] = commands
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONHASHSEED"] = "0"

    with tempfile.TemporaryDirectory(prefix="release-", dir=sandbox_root) as directory:
        sandbox = Path(directory).resolve()
        sandbox.relative_to(sandbox_root)  # Cleanup is confined to this newly created sandbox.
        checkout = sandbox / "checkout"
        checkout.mkdir()
        for folder in ("src", "tests", "examples", "docs", "benchmarks", ".github"):
            shutil.copytree(
                ROOT / folder,
                checkout / folder,
                ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
            )
        for source in ROOT.iterdir():
            if source.is_file() and source.suffix in (".md", ".toml", ".in"):
                shutil.copy2(source, checkout / source.name)
        shutil.copy2(ROOT / "LICENSE", checkout / "LICENSE")
        (checkout / "audit").mkdir()
        for source in (ROOT / "audit").glob("*.py"):
            shutil.copy2(source, checkout / "audit" / source.name)

        def clean(value: str) -> str:
            for prefix, replacement in (
                (str(sandbox), "<SANDBOX>"),
                (str(ROOT), "<WORKSPACE>"),
                (str(Path.home()), "<USER>"),
            ):
                for spelling in (prefix, json.dumps(prefix)[1:-1], prefix.replace("\\", "/")):
                    value = re.sub(
                        re.escape(spelling),
                        replacement,
                        value,
                        flags=re.IGNORECASE if os.name == "nt" else 0,
                    )
            return value

        def run(
            arguments: list[str | Path], *, cwd: Path = checkout, expected: int = 0
        ) -> subprocess.CompletedProcess[str]:
            command = [str(argument) for argument in arguments]
            process = subprocess.run(
                command,
                cwd=cwd,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                timeout=180,
            )
            commands.append(
                {
                    "command": [clean(arg) for arg in command],
                    "cwd": clean(str(cwd)),
                    "exit": process.returncode,
                    "expected_exit": expected,
                    "stdout": clean(process.stdout),
                    "stderr": clean(process.stderr),
                }
            )
            print(f"[{process.returncode}] {' '.join(clean(arg) for arg in command)}", flush=True)
            if process.returncode != expected:
                raise RuntimeError(f"Unexpected exit status: {process.stdout}\n{process.stderr}")
            return process

        try:
            builder = sandbox / "builder"
            venv.create(builder, with_pip=True)
            build_python = python_in(builder)
            run([build_python, "-m", "pip", "install", "build==1.3.0"])
            run([build_python, "-m", "build", "--outdir", sandbox / "artifacts"])
            wheels = list((sandbox / "artifacts").glob("*.whl"))
            if len(wheels) != 1:
                raise RuntimeError("Expected exactly one wheel")
            installed = sandbox / "installed"
            venv.create(installed, with_pip=True)
            installed_python = python_in(installed)
            run([installed_python, "-m", "pip", "install", "--no-deps", wheels[0]])
            run([installed_python, "-m", "pip", "check"])
            isolated_cwd = sandbox / "outside-checkout"
            isolated_cwd.mkdir()
            metadata = run(
                [
                    installed_python,
                    "-c",
                    "import importlib.metadata as m,json,zipnameguard,sys; "
                    "from pathlib import Path; "
                    "d=m.distribution('zipnameguard'); "
                    "assert d.version == zipnameguard.__version__ == '0.1.0'; "
                    "assert d.metadata['Name'] == 'zipnameguard'; "
                    "assert d.metadata['Requires-Python'] == '>=3.11'; "
                    "assert d.metadata['License-Expression'] == 'MIT'; "
                    "assert ('zipnameguard','zipnameguard.cli:main') in "
                    "[(e.name,e.value) for e in d.entry_points]; "
                    "assert Path(zipnameguard.__file__).is_relative_to(Path(sys.prefix)); "
                    "assert all('extra ==' in r for r in (d.requires or [])); "
                    "print(json.dumps({'name':d.metadata['Name'],'version':d.version,"
                    "'summary':d.metadata['Summary'],'requires_python':d.metadata['Requires-Python'],"
                    "'license_expression':d.metadata['License-Expression'],"
                    "'dependencies':d.requires,'import_path':zipnameguard.__file__,"
                    "'entry_points':[(e.name,e.value) for e in d.entry_points]}))",
                ],
                cwd=isolated_cwd,
            )
            record["metadata"] = json.loads(clean(metadata.stdout))
            run([installed_python, "-m", "zipnameguard", "--version"], cwd=isolated_cwd)
            run([installed_python, "-m", "zipnameguard", "--help"], cwd=isolated_cwd)
            run(
                [installed_python, "-m", "unittest", "discover", "-s", checkout / "tests", "-v"],
                cwd=isolated_cwd,
            )
            run(
                [
                    installed_python,
                    checkout / "tests" / "archive_corpus.py",
                    "--output",
                    sandbox / "corpus",
                ]
            )
            console = installed / (
                "Scripts/zipnameguard.exe" if os.name == "nt" else "bin/zipnameguard"
            )
            for name, status in (
                ("valid-basic", 0),
                ("case", 1),
                ("trailing-space", 1),
                ("unicode-nfc-nfd", 1),
                ("file-directory", 1),
                ("long-ascii-component", 1),
            ):
                response = run(
                    [console, "--strict", "--json", sandbox / "corpus" / f"{name}.zip"],
                    cwd=isolated_cwd,
                    expected=status,
                )
                json.loads(response.stdout)
            run([console, "--json", sandbox / "missing.zip"], cwd=isolated_cwd, expected=2)

            # Execute the README commands in a real activation session; no policy override.
            if os.name == "nt":
                shell = shutil.which("pwsh") or shutil.which("powershell")
                if shell is None:
                    raise RuntimeError("PowerShell required for exact Windows README verification")
                script = sandbox / "readme.ps1"
                script.write_text(
                    "$ErrorActionPreference = 'Stop'\n"
                    "python -m venv .venv\n"
                    ".venv\\Scripts\\Activate.ps1\n"
                    "python -m pip install .\n"
                    "if ($LASTEXITCODE -ne 0) { throw 'README installation failed' }\n"
                    "python examples/create_demo.py\n"
                    "zipnameguard demo.zip\n"
                    "if ($LASTEXITCODE -ne 1) { throw 'Expected demo exit 1' }\n"
                    "exit 0\n",
                    encoding="utf-8",
                )
                run([shell, "-NoProfile", "-File", script])
            else:
                script = sandbox / "readme.sh"
                script.write_text(
                    "set -eu\npython -m venv .venv\nsource .venv/bin/activate\n"
                    "python -m pip install .\npython examples/create_demo.py\n"
                    "set +e\nzipnameguard demo.zip\nstatus=$?\n"
                    'test "$status" -eq 1\n',
                    encoding="utf-8",
                )
                run(["bash", script])
            hashes = {}
            for artifact in (sandbox / "artifacts").iterdir():
                hashes[artifact.name] = hashlib.sha256(artifact.read_bytes()).hexdigest()
                if artifacts is not None:
                    artifacts.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(artifact, artifacts / artifact.name)
            record["artifact_sha256"] = hashes
            if artifacts is not None:
                (artifacts / "SHA256SUMS").write_text(
                    "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items())),
                    encoding="ascii",
                )
            record["status"] = "passed"
        except Exception as error:
            record["status"] = "failed"
            record["failure"] = clean(str(error))
            raise
        finally:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path)
    arguments = parser.parse_args()
    verify(
        arguments.output.resolve(), arguments.artifacts.resolve() if arguments.artifacts else None
    )
