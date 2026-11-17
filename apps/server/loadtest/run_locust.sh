#!/usr/bin/env bash
# locust scenarios of Charge.md. Usage: loadtest/run_locust.sh [base_url] [out_dir] [scenario...]
# Scenarios: l1 (brief's Association, ramp to 200 users), l1w4 (the same against the
# 4 workers API: CONTAINER=gaspirator-load-api-w4). The reservation race is
# loadtest/locust_race.py, see Charge.md.
set -euo pipefail

BASE=${1:-http://localhost:8001}
OUT=${2:-loadtest/results}
shift 2 || true
SCENARIOS=${*:-l1}
CONTAINER=${CONTAINER:-gaspirator-load-api}
mkdir -p "$OUT"

fresh() {
    docker restart "$CONTAINER" >/dev/null
    until curl -sf "$BASE/health" >/dev/null; do sleep 1; done
    sleep 2
}

locust_run() { # name, user class, users, spawn rate, duration
    echo "== $1"
    fresh
    uvx locust -f loadtest/locustfile.py --host "$BASE" --headless --only-summary \
        -u "$3" -r "$4" -t "$5" --csv "$OUT/$1" --csv-full-history --html "$OUT/$1.html" "$2" ||
        true # locust exits with 1 when a request failed: keep the next scenarios
}

for scenario in $SCENARIOS; do
    case $scenario in
    l1) locust_run l1-association Association 200 5 3m ;;
    l1w4) locust_run l1-association-workers4 Association 200 5 3m ;;
    esac
done
