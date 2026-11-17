#!/usr/bin/env bash
# oha scenarios of Charge.md. Usage: loadtest/run_oha.sh [base_url] [out_dir] [scenario...]
# Needs a database seeded with loadtest/seed.py and an API running on it in the docker
# container $CONTAINER (restarted before each scenario, so that a saturated run cannot
# spoil the next one). Scenarios: o1 o2 o2long (default), o6 (4 workers API, with
# CONTAINER=gaspirator-load-api-w4).
set -euo pipefail

BASE=${1:-http://localhost:8001}
OUT=${2:-loadtest/results}
shift 2 || true
SCENARIOS=${*:-o1 o2 o2long}
CONTAINER=${CONTAINER:-gaspirator-load-api}
mkdir -p "$OUT"

fresh() {
    docker restart "$CONTAINER" >/dev/null
    until curl -sf "$BASE/health" >/dev/null; do sleep 1; done
    sleep 2
}

token() {
    # A fresh access token (valid 15 min) of the association loadtest-asso-0.
    curl -s -X POST "$BASE/api/v1/auth/login" -H 'content-type: application/json' \
        -d '{"email":"loadtest-asso-0@example.com","password":"loadtest-password"}' |
        python -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}

run() { # name, oha args... Call `fresh` (and get $AUTH) before expanding the args.
    local name=$1
    shift
    echo "== $name"
    oha --no-tui --output-format json -o "$OUT/$name.json" "$@"
}

SEARCH="$BASE/api/v1/suppliers?latitude=45.76&longitude=4.83"

for scenario in $SCENARIOS; do
    case $scenario in
    o1) # Ceiling of the stack without database nor auth.
        fresh
        run o1-health -z 20s -c 50 "$BASE/health" ;;
    o2) # Nominal search (radius 10 km, page of 20), up to the breaking point.
        for c in 10 25 50; do
            fresh
            AUTH="Authorization: Bearer $(token)"
            run "o2-search-c$c" -z 30s -c "$c" -H "$AUTH" "$SEARCH"
        done ;;
    o2long) # Past the breaking point, long enough for the 30 s pool timeout to show.
        for c in 75 100 200; do
            fresh
            AUTH="Authorization: Bearer $(token)"
            run "o2-search-c$c-90s" -z 90s -c "$c" -H "$AUTH" "$SEARCH"
        done ;;
    o6) # Same search with 4 uvicorn workers, no --reload (see Charge.md).
        for c in 50 100 200; do
            fresh
            AUTH="Authorization: Bearer $(token)"
            run "o6-workers4-c$c" -z 60s -c "$c" -H "$AUTH" "$SEARCH"
        done ;;
    esac
done
