"""Fail when a pip-audit JSON report holds a finding at or above a GHSA severity.

pip-audit has no severity filter, so each finding's GHSA severity is read from OSV.
A finding whose severity cannot be found counts as CRITICAL (fail closed).

Usage: python3 pip_audit_gate.py <pip-audit.json> [LOW|MODERATE|HIGH|CRITICAL]
"""

import json
import sys
import urllib.request

LEVELS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def severity(vuln: dict) -> str:
    for vuln_id in [vuln["id"], *vuln.get("aliases", [])]:
        if not vuln_id.startswith("GHSA-"):
            continue
        try:
            with urllib.request.urlopen(f"https://api.osv.dev/v1/vulns/{vuln_id}", timeout=20) as r:
                level = json.load(r).get("database_specific", {}).get("severity", "").upper()
        except OSError:
            continue
        if level in LEVELS:
            return level
    return "CRITICAL"


def main() -> int:
    report_path, threshold = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "HIGH").upper()
    with open(report_path) as f:
        report = json.load(f)
    blocking = 0
    for dep in report["dependencies"]:
        for vuln in dep.get("vulns", []):
            level = severity(vuln)
            blocks = LEVELS.index(level) >= LEVELS.index(threshold)
            blocking += blocks
            fix = ", ".join(vuln.get("fix_versions", [])) or "none"
            print(f"{'BLOCK' if blocks else 'warn '} {level:<8} {dep['name']} {dep['version']} {vuln['id']} (fix: {fix})")
    print(f"{blocking} finding(s) at or above {threshold}")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
