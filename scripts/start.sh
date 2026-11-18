#!/bin/sh
# Starts the whole stack in Docker. Only Docker is needed on the machine: the containers install
# the dependencies themselves. Production runs the images CI publishes, not this script.
set -eu
cd "$(dirname "$0")/.."

command -v docker >/dev/null 2>&1 || {
	echo "Docker is not installed" >&2
	exit 1
}
docker info >/dev/null 2>&1 || {
	echo "Docker is not running" >&2
	exit 1
}

for app in web server; do
	if [ ! -f "apps/$app/.env" ]; then
		cp "apps/$app/.env.example" "apps/$app/.env"
		echo "apps/$app/.env créé à partir de apps/$app/.env.example"
	fi
done

docker compose up -d --build

echo
echo "Gaspirator started:"
echo "  Web site : http://localhost:5173"
echo "  API      : http://localhost:8000/docs"
echo "  E-mails  : http://localhost:8025"
echo "Logs : docker compose logs -f    Stop : docker compose down"
