#!/usr/bin/env bash
set -euo pipefail

if (( $# > 0 )); then
	printf '%s\n' 'FEIL: Skriptet tar ingen argumenter. Kjoering ruller ut til alle repoene i policy/repoer.json.' >&2
	exit 1
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."

for tools in gh mvn java; do
	if ! command -v "$tools" > /dev/null; then
		printf 'FEIL: %s maa vaere installert og tilgjengelig i PATH.\n' "$tools" >&2
		exit 1
	fi
done

if ! gh auth status --hostname github.com; then
	gh auth login --hostname github.com
	gh auth status --hostname github.com
fi

mvn -f scripts/forvaltning/pom.xml clean verify
exec java -jar scripts/forvaltning/target/forvaltning.jar
