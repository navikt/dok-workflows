#!/usr/bin/env python3
"""Les repo-konfigurasjon og skriv GitHub Actions-matrise uten API-kall."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

AVHENGIGHETER = ("PyYAML==6.0.3",)

if __name__ == "__main__" and sys.argv[1:] == ["--installer-avhengigheter"]:
	if sys.prefix == sys.base_prefix:
		sys.exit("Opprett et virtuelt Python-miljo med python3 -m venv foerst.")
	sys.exit(subprocess.run(
		[sys.executable, "-m", "pip", "install", *AVHENGIGHETER],
		check=False,
	).returncode)

import yaml


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "policy"
REPO_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


class PolicyError(Exception):
	pass


class StrictLoader(yaml.SafeLoader):
	pass


def mapping(loader, node):
	result = {}
	for key_node, value_node in node.value:
		key = loader.construct_object(key_node)
		if not isinstance(key, str) or key in result:
			raise PolicyError("Konfigurasjonen har ugyldig eller duplisert feltnavn.")
		result[key] = loader.construct_object(value_node)
	return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def load_yaml(path):
	with path.open() as source:
		return yaml.load(source, Loader=StrictLoader)


def fields(value, expected, location):
	if not isinstance(value, dict) or set(value) != set(expected):
		raise PolicyError(f"{location}: forventer feltene {', '.join(expected)}.")


def strings(value, location):
	if not isinstance(value, list) or not value or any(
		not isinstance(item, str) or not item.strip() for item in value
	) or len(set(value)) != len(value):
		raise PolicyError(f"{location}: forventer en ikke-tom liste med unike strenger.")


def positive_id(value, location):
	if type(value) is not int or value <= 0:
		raise PolicyError(f"{location}: forventer en positiv numerisk GitHub-ID.")
	return value


def validate_checks(checks):
	if not isinstance(checks, list) or not checks:
		raise PolicyError("required_checks kan ikke vaere tom.")
	for check in checks:
		fields(check, ["context", "integration_id"], "required_checks")
		if not isinstance(check["context"], str) or not check["context"].strip():
			raise PolicyError("Ugyldig check-navn.")
		positive_id(check["integration_id"], "integration_id")
	if len({check["context"] for check in checks}) != len(checks):
		raise PolicyError("Dupliserte check-navn.")


def load_repos(directory=POLICY):
	repositories = load_yaml(directory / "repoer.yml")
	fields(repositories, ["repoer"], "repoer.yml")
	repositories = repositories["repoer"]
	if not isinstance(repositories, dict) or not repositories:
		raise PolicyError("repoer.yml maa inneholde en eksplisitt repo-liste.")
	for name, config in repositories.items():
		if not REPO_NAME.fullmatch(name):
			raise PolicyError(f"Ugyldig repository-navn: {name}")
		fields(config, ["type", "required_checks", "prod_workflows", "release_tags",
			"automerge"], name)
		if config["type"] != "nais-app":
			raise PolicyError(f"{name}: bare nais-app stoettes.")
		validate_checks(config["required_checks"])
		strings(config["prod_workflows"], f"{name}: prod_workflows")
		for path in config["prod_workflows"]:
			if not re.fullmatch(r"\.github/workflows/[A-Za-z0-9_-]+\.ya?ml", path):
				raise PolicyError(f"{name}: oppgi eksakte workflow-stier.")
		strings(config["release_tags"], f"{name}: release_tags")
		if any(not pattern.startswith("refs/tags/") or pattern == "refs/tags/"
				for pattern in config["release_tags"]):
			raise PolicyError(f"{name}: release_tags maa starte med refs/tags/.")
		auto = config["automerge"]
		fields(auto, ["aktivert", "semver_filter", "minimum_alder_dager",
			"ignorerte_avhengigheter", "alltid_tillat"], f"{name}: automerge")
		if type(auto["aktivert"]) is not bool:
			raise PolicyError(f"{name}: automerge.aktivert skal vaere boolsk.")
		if type(auto["minimum_alder_dager"]) is not int or auto["minimum_alder_dager"] < 0:
			raise PolicyError(f"{name}: ugyldig minimum_alder_dager.")
		for key in ("semver_filter", "ignorerte_avhengigheter", "alltid_tillat"):
			if not isinstance(auto[key], str):
				raise PolicyError(f"{name}: {key} skal vaere en streng.")
		if not set(auto["semver_filter"].split(",")) <= {"patch", "minor", "major", "unknown"}:
			raise PolicyError(f"{name}: ugyldig semver_filter.")
	return repositories


def select_repos(repositories, selection):
	if selection == "alle":
		return sorted(repositories)
	names = selection.split(",")
	if not names or any(name not in repositories for name in names) or len(set(names)) != len(names):
		raise PolicyError("Velg 'alle' eller unike repo-navn fra repoer.yml, kommaseparert.")
	return names


def main():
	parser = argparse.ArgumentParser(description=__doc__,
		epilog="Installer avhengigheter i et virtuelt miljo med --installer-avhengigheter.")
	selection = parser.add_mutually_exclusive_group(required=True)
	selection.add_argument("--repo", help="Kommaseparerte repo-navn, eller 'alle'.")
	selection.add_argument("--alle", action="store_true")
	parser.add_argument("--automerge", action="store_true", help="Velg bare repoer med automerge aktivert.")
	args = parser.parse_args()
	try:
		repositories = load_repos()
		names = select_repos(repositories, "alle" if args.alle else args.repo)
		if args.automerge:
			names = [name for name in names if repositories[name]["automerge"]["aktivert"]]
		print(json.dumps({"include": [{"repo": name, **repositories[name]["automerge"]} for name in names]}))
		return 0
	except (PolicyError, OSError, ValueError, yaml.YAMLError) as error:
		print(f"FEIL: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
