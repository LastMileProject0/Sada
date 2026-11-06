"""Audit installed production Python dependency closure against OSV.

Only public package names/versions leave the process. No application import,
environment/credential access, database connection or inference request.
"""
from importlib.metadata import distribution
import json
from pathlib import Path
from urllib.request import Request, urlopen
import sys

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOTS = ["fastapi", "uvicorn", "pandas", "openpyxl", "pydantic", "psycopg[binary]", "httpx"]


def runtime_packages():
    packages, processed = {}, {}
    queue = [Requirement(name) for name in ROOTS]
    while queue:
        requirement = queue.pop()
        name = canonicalize_name(requirement.name)
        extras = set(requirement.extras) | processed.get(name, set())
        if name in processed and extras == processed[name]:
            continue
        processed[name] = extras
        installed = distribution(name)
        packages[name] = installed.version
        for raw in installed.requires or []:
            child = Requirement(raw)
            if child.marker is None or any(child.marker.evaluate({"extra": extra})
                                            for extra in extras | {""}):
                queue.append(child)
    return packages


def main():
    packages = runtime_packages()
    payload = {"queries": [{"package": {"name": name, "ecosystem": "PyPI"},
                            "version": version} for name, version in sorted(packages.items())]}
    request = Request("https://api.osv.dev/v1/querybatch",
                      data=json.dumps(payload).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        results = json.load(response)["results"]
    if len(results) != len(packages):
        raise RuntimeError("Incomplete vulnerability response")
    findings = [{"package": name, "version": version, "advisories": result.get("vulns", [])}
                for (name, version), result in zip(sorted(packages.items()), results)
                if result.get("vulns")]
    report = {"source": "OSV querybatch", "packages": packages, "findings": findings}
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if output:
        output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"runtime_packages": len(packages), "affected_packages": len(findings),
                      "findings": findings}))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
