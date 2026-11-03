"""Read-only exact-name queries; never reserves names or uploads artifacts."""

import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

URLS = {
    "pypi-zipnameguard": "https://pypi.org/pypi/zipnameguard/json",
    "npm-zipnameguard": "https://registry.npmjs.org/zipnameguard",
    "crates-zipnameguard": "https://crates.io/api/v1/crates/zipnameguard",
    "github-name": "https://api.github.com/search/repositories?q=zipnameguard+in:name",
    "pypi-pathward": "https://pypi.org/pypi/pathward/json",
    "pypi-zipguard": "https://pypi.org/pypi/zipguard/json",
}


def query(item: tuple[str, str]) -> tuple[str, dict[str, object]]:
    name, url = item
    result: dict[str, object] = {"url": url}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "ZipNameGuard-local-audit"})
        with urllib.request.urlopen(request, timeout=20) as response:
            result["http_status"] = response.status
            data = json.load(response)
        if name == "github-name":
            result["total_count"] = data.get("total_count")
            result["repositories"] = [entry["html_url"] for entry in data.get("items", [])]
        elif name.startswith("pypi"):
            result["name"] = data["info"]["name"]
            result["version"] = data["info"]["version"]
            result["summary"] = data["info"]["summary"]
            result["requires_dist"] = data["info"].get("requires_dist")
            result["project_urls"] = data["info"].get("project_urls")
    except urllib.error.HTTPError as error:
        result["http_status"] = error.code
    except (OSError, ValueError) as error:
        result["error"] = str(error)
    return name, result


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = dict(executor.map(query, URLS.items()))
    results = {"audit_date": "2026-10-30", "queries": results}
    destination = Path(__file__).with_name("registry-results.json")
    destination.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(destination.read_text(encoding="utf-8"))
