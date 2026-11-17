"""Print a Markdown table of the oha JSON results and locust CSV stats.

    uv run python loadtest/summarize.py loadtest/results

oha counts the requests still in flight when `-z` ends ("aborted due to deadline") in its
req/s; here req/s counts the 2xx responses only, the error rate is over the requests that
got an answer (non-2xx or network error), and the requests left without an answer at the
end are shown apart ("sans réponse").
"""

import csv
import json
import sys
from pathlib import Path


def ms(seconds: float | None) -> str:
    return "–" if seconds is None else f"{seconds * 1000:.0f}"


def oha_row(path: Path) -> str:
    data = json.loads(path.read_text())
    codes = data.get("statusCodeDistribution", {})
    errors = data.get("errorDistribution", {})
    pending = sum(n for k, n in errors.items() if "deadline" in k)
    failures = sum(n for k, n in errors.items() if "deadline" not in k)
    ok = sum(n for code, n in codes.items() if code.startswith("2"))
    answered = sum(codes.values()) + failures
    bad = answered - ok
    p = data["latencyPercentiles"]
    return (
        f"| {path.stem} | {answered} | {ok / data['summary']['total']:.1f} "
        f"| {ms(p['p50'])} | {ms(p['p95'])} | {ms(p['p99'])} "
        f"| {100 * bad / answered if answered else 0:.1f} | {pending} "
        f"| {', '.join(f'{k}×{v}' for k, v in {**codes, **errors}.items())} |"
    )


def locust_rows(path: Path) -> list[str]:
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            n = int(r["Request Count"])
            rows.append(
                f"| {path.stem.removesuffix('_stats')} {r['Name']} | {n} "
                f"| {float(r['Requests/s']):.1f} | {r['50%']} | {r['95%']} | {r['99%']} "
                f"| {100 * int(r['Failure Count']) / n if n else 0:.1f} | | |"
            )
    return rows


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "loadtest/results")
    print(
        "| Run | Réponses | req/s (2xx) | p50 ms | p95 ms | p99 ms | % erreur | Sans réponse | Détail |"
    )
    print("|---|---|---|---|---|---|---|---|---|")
    for path in sorted(folder.glob("o*.json")):  # oha runs (r*.json: race outcomes)
        if path.stat().st_size:  # an empty file is a run still in progress
            print(oha_row(path))
    for path in sorted(folder.glob("*_stats.csv")):
        print("\n".join(locust_rows(path)))


if __name__ == "__main__":
    main()
