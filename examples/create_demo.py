"""Create a deterministic demonstration ZIP without creating invalid disk names."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def create_demo(destination: Path) -> None:
    with ZipFile(destination, "w") as archive:
        for name in ("README.md", "readme.md", "assets/CON.txt", "logs/12:30.txt"):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, b"demonstration data\n")


if __name__ == "__main__":
    create_demo(Path("demo.zip"))
    print("Created demo.zip; scan it with: zipnameguard demo.zip")
