#!/usr/bin/env python3
"""Rull ut repository-policy med gh api. Utrulling krever eksplisitt --apply."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote

import yaml

from repoer import (
	POLICY, ROOT, PolicyError, fields, load_repos, load_yaml, positive_id,
	select_repos, strings, validate_checks,
)


class ApiError(PolicyError):
	def __init__(self, endpoint, status):
		self.status = status
		super().__init__(f"GitHub API feilet for {endpoint} (HTTP {status or 'ukjent'}).")


def load_config(directory=POLICY):
	common = load_yaml(directory / "fellesregler.yml")
	fields(common, ["organisasjon", "team", "rulesets", "actions_policies",
		"workflow_permissions"], "fellesregler.yml")
	if common["organisasjon"] != "navikt" or common["team"] != "teamdokumenthandtering":
		raise PolicyError("Denne utrullingen er avgrenset til navikt/teamdokumenthandtering.")
	repositories = load_repos(directory)
	for config in repositories.values():
		# Valider ogsaa regelmalene uten aa kreve app-/team-ID eller API-tilgang.
		desired_policy(common, config, 1, 2)
	return common, repositories


def github_api(method, endpoint, payload=None, missing_ok=False):
	command = ["gh", "api", "--hostname", "github.com", "--method", method,
		"-H", "Accept: application/vnd.github+json",
		"-H", "X-GitHub-Api-Version: 2022-11-28", endpoint]
	if payload is not None:
		command.extend(["--input", "-"])
	result = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
		text=True, capture_output=True, timeout=120, check=False)
	if result.returncode:
		status_match = re.search(r"\(HTTP (\d{3})\)", result.stderr)
		status = int(status_match[1]) if status_match else None
		if missing_ok and status == 404:
			return None
		# Ikke skriv API-respons eller token til logger.
		raise ApiError(endpoint, status)
	return json.loads(result.stdout) if result.stdout.strip() else None


def pages(endpoint, key=None):
	result = []
	page = 1
	while True:
		separator = "&" if "?" in endpoint else "?"
		response = github_api("GET", f"{endpoint}{separator}per_page=100&page={page}")
		items = response[key] if key else response
		if not isinstance(items, list):
			raise PolicyError(f"Uventet listeformat fra {endpoint}.")
		result.extend(items)
		if len(items) < 100:
			return result
		page += 1


def validate_rule(rule, actions=False):
	parameter_fields = {
		"deletion": [],
		"non_fast_forward": [],
		"creation": [],
		"update": ["update_allows_fetch_and_merge"],
		"required_status_checks": ["strict_required_status_checks_policy",
			"do_not_enforce_on_create", "required_status_checks"],
		"pull_request": ["allowed_merge_methods", "required_approving_review_count",
			"dismiss_stale_reviews_on_push", "require_code_owner_review", "require_last_push_approval",
			"required_review_thread_resolution", "required_reviewers", "dismissal_restriction"],
	}
	if actions:
		parameter_fields = {
			"restrict_actions_actors": ["allowed_actors"],
			"restrict_action_events": ["allowed_events"],
		}
	if not isinstance(rule, dict) or not isinstance(rule.get("type"), str) or rule["type"] not in parameter_fields:
		raise PolicyError("Ukjent regeltype i fellesregler.yml.")
	expected = parameter_fields[rule["type"]]
	fields(rule, ["name", "type", "parameters"] if expected else ["name", "type"], "regel")
	if not isinstance(rule["name"], str) or not rule["name"].strip():
		raise PolicyError("Hver regel skal ha et lesbart name.")
	parameters = rule.get("parameters", {})
	fields(parameters, expected, rule["name"])
	for key in ("update_allows_fetch_and_merge", "strict_required_status_checks_policy",
			"do_not_enforce_on_create", "dismiss_stale_reviews_on_push", "require_code_owner_review",
			"require_last_push_approval", "required_review_thread_resolution"):
		if key in parameters and type(parameters[key]) is not bool:
			raise PolicyError(f"{rule['name']}: {key} skal vaere boolsk.")
	if rule["type"] == "pull_request":
		count = parameters["required_approving_review_count"]
		if type(count) is not int or not 0 <= count <= 10:
			raise PolicyError("required_approving_review_count skal vaere mellom 0 og 10.")
		strings(parameters["allowed_merge_methods"], "allowed_merge_methods")
		if not set(parameters["allowed_merge_methods"]) <= {"merge", "squash", "rebase"}:
			raise PolicyError("Ugyldig allowed_merge_methods.")
		reviewers = parameters["required_reviewers"]
		if not isinstance(reviewers, list):
			raise PolicyError("required_reviewers skal vaere en liste.")
		for reviewer in reviewers:
			fields(reviewer, ["file_patterns", "minimum_approvals", "reviewer"], "required_reviewers")
			strings(reviewer["file_patterns"], "file_patterns")
			if type(reviewer["minimum_approvals"]) is not int or not 0 <= reviewer["minimum_approvals"] <= 10:
				raise PolicyError("minimum_approvals skal vaere mellom 0 og 10.")
			fields(reviewer["reviewer"], ["id", "type"], "reviewer")
			positive_id(reviewer["reviewer"]["id"], "reviewer.id")
			if reviewer["reviewer"]["type"] != "Team":
				raise PolicyError("Bare Team stoettes som required reviewer.")
		dismissal = parameters["dismissal_restriction"]
		fields(dismissal, ["enabled", "allowed_actors"], "dismissal_restriction")
		if type(dismissal["enabled"]) is not bool or dismissal != {"enabled": False, "allowed_actors": []}:
			raise PolicyError("Egne dismissal restrictions stoettes ikke i foerste versjon.")
	if rule["type"] == "required_status_checks":
		validate_checks(parameters["required_status_checks"])
	if rule["type"] == "restrict_actions_actors":
		actors = parameters["allowed_actors"]
		if not isinstance(actors, list) or not actors:
			raise PolicyError("allowed_actors kan ikke vaere tom.")
		for actor in actors:
			fields(actor, ["id", "type"], "allowed_actors")
			positive_id(actor["id"], "allowed_actors.id")
			if actor["type"] != "Team":
				raise PolicyError("Bare Team stoettes som Actions-aktoer i foerste versjon.")
	if rule["type"] == "restrict_action_events":
		strings(parameters["allowed_events"], "allowed_events")
	return {key: value for key, value in rule.items() if key != "name"}


def desired_policy(common, config, team_id, app_id):
	positive_id(team_id, "TEAM_ID")
	positive_id(app_id, "AUTOMERGE_APP_ID")
	values = {
		"${team_id}": team_id, "${automerge_app_id}": app_id,
		"${required_checks}": config["required_checks"], "${prod_workflows}": config["prod_workflows"],
	}

	def resolve(value):
		if isinstance(value, str) and "${" in value:
			if value not in values:
				raise PolicyError(f"Ukjent plassholder: {value}. Bruk en hel verdi, ikke strenginterpolasjon.")
			return deepcopy(values[value])
		if isinstance(value, list):
			return [resolve(item) for item in value]
		if isinstance(value, dict):
			return {key: resolve(item) for key, item in value.items()}
		return value

	def compile_entries(entries, actions=False):
		if not isinstance(entries, list) or not entries:
			raise PolicyError("rulesets og actions_policies skal vaere ikke-tomme lister.")
		result = []
		names = set()
		for entry in resolve(entries):
			fields(entry, ["name", "enforcement", "conditions", "rules"] if actions else
				["name", "target", "enforcement", "bypass_actors", "rules"], "policy")
			name = entry["name"]
			if not isinstance(name, str) or not re.fullmatch(r"dok-[a-z0-9-]+", name) or name in names:
				raise PolicyError("Policy-navn skal vaere unike og starte med dok-.")
			names.add(name)
			if entry["enforcement"] not in ("active", "disabled", "evaluate"):
				raise PolicyError(f"{name}: ugyldig enforcement.")
			if not isinstance(entry["rules"], list) or not entry["rules"]:
				raise PolicyError(f"{name}: rules kan ikke vaere tom.")
			entry["rules"] = [validate_rule(rule, actions) for rule in entry["rules"]]
			if len({rule["type"] for rule in entry["rules"]}) != len(entry["rules"]):
				raise PolicyError(f"{name}: dupliserte regeltyper.")
			if actions:
				fields(entry["conditions"], ["workflow_path"], f"{name}: conditions")
				paths = entry["conditions"]["workflow_path"]
				fields(paths, ["include", "exclude"], "workflow_path")
				if paths != {"include": config["prod_workflows"], "exclude": []}:
					raise PolicyError("Actions-policy skal gjelde de konfigurerte prod_workflows.")
			else:
				if entry["target"] not in ("branch", "tag"):
					raise PolicyError(f"{name}: target skal vaere branch eller tag.")
				if entry["target"] == "tag" and any(
					rule["type"] not in ("creation", "update", "deletion") for rule in entry["rules"]
				):
					raise PolicyError(f"{name}: ugyldig regeltype for tags.")
				if not isinstance(entry["bypass_actors"], list):
					raise PolicyError(f"{name}: bypass_actors skal vaere en liste.")
				for actor in entry["bypass_actors"]:
					fields(actor, ["actor_id", "actor_type", "bypass_mode"], "bypass_actors")
					positive_id(actor["actor_id"], "actor_id")
					if actor["actor_type"] not in ("Team", "Integration") or actor["bypass_mode"] not in ("pull_request", "always"):
						raise PolicyError(f"{name}: ugyldig bypass-aktoer eller modus.")
					if entry["target"] == "tag" and actor["bypass_mode"] != "always":
						raise PolicyError("Tag-regler stoetter ikke PR-only bypass.")
				entry["conditions"] = {"ref_name": {
					"include": config["release_tags"] if entry["target"] == "tag" else ["~DEFAULT_BRANCH"],
					"exclude": [],
				}}
			result.append(entry)
		return result

	token = common["workflow_permissions"]
	fields(token, ["default_workflow_permissions", "can_approve_pull_request_reviews"], "workflow_permissions")
	if token["default_workflow_permissions"] not in ("read", "write") or type(token["can_approve_pull_request_reviews"]) is not bool:
		raise PolicyError("Ugyldige workflow_permissions.")
	return {
		"rulesets": compile_entries(common["rulesets"]),
		"policies": compile_entries(common["actions_policies"], actions=True),
		"token": dict(token),
	}


def canonical(value):
	if isinstance(value, dict):
		return {key: canonical(item) for key, item in sorted(value.items())}
	if isinstance(value, list):
		return sorted((canonical(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
	return value


def comparable(actual, desired):
	# Fjern bare metadata paa toppnivaa; behold ukjente regelparametere.
	return canonical({key: actual.get(key) for key in desired})


def read_state(repo):
	base = f"repos/navikt/{repo}"
	metadata = github_api("GET", base)
	if metadata["archived"] or metadata.get("disabled"):
		raise PolicyError(f"{repo}: arkivert/deaktivert repository.")
	rulesets = pages(f"{base}/rulesets?includes_parents=true")
	local = []
	inherited = []
	for item in rulesets:
		if item["source_type"] == "Repository" and item["source"] == f"navikt/{repo}":
			detail = github_api("GET", f"{base}/rulesets/{item['id']}")
			if "bypass_actors" not in detail:
				raise PolicyError(f"{repo}: API skjuler bypass-listen; kontroller tokenets rettigheter.")
			local.append(detail)
		else:
			inherited.append(item)
	# Liste-endepunktet returnerer policies under policies-feltet.
	policies = []
	for item in pages(f"{base}/actions/policies?has_parents=true", key="policies"):
		if item["source_type"] == "Repository":
			policies.append(github_api("GET", f"{base}/actions/policies/{item['id']}"))
		else:
			inherited.append(item)
	branch = quote(metadata["default_branch"], safe="")
	classic = github_api("GET", f"{base}/branches/{branch}/protection", missing_ok=True)
	return {
		"rulesets": local, "policies": policies,
		"token": github_api("GET", f"{base}/actions/permissions/workflow"),
		"classic": classic, "inherited": inherited,
	}


def make_changes(repo, desired, state):
	base = f"repos/navikt/{repo}"
	changes = []
	for category, endpoint in (("rulesets", "rulesets"), ("policies", "actions/policies")):
		for wanted in desired[category]:
			matches = [item for item in state[category] if item["name"] == wanted["name"]]
			if len(matches) > 1:
				raise PolicyError(f"{repo}: flere regler heter {wanted['name']}; avklar manuelt.")
			current = matches[0] if matches else None
			if current is None or comparable(current, wanted) != canonical(wanted):
				changes.append({
					"name": wanted["name"], "method": "PUT" if current else "POST",
					"endpoint": f"{base}/{endpoint}" + (f"/{current['id']}" if current else ""),
					"before": current, "after": wanted,
				})
	if comparable(state["token"], desired["token"]) != canonical(desired["token"]):
		changes.append({
			"name": "GITHUB_TOKEN", "method": "PUT",
			"endpoint": f"{base}/actions/permissions/workflow",
			"before": state["token"], "after": desired["token"],
		})
	return changes


def show_changes(repo, changes, state, desired):
	owned = {item["name"] for item in desired["rulesets"]}
	unmanaged = [item["name"] for item in state["rulesets"] if item["name"] not in owned]
	if state["classic"] or state["inherited"] or unmanaged:
		print(f"{repo}: ADVARSEL: annen beskyttelse finnes og beholdes. "
			"Den kan blokkere bypass/automerge; samordnes manuelt.")
	if not changes:
		print(f"{repo}: UENDRET")
	for change in changes:
		print(f"{repo}: {'OPPRETT' if change['method'] == 'POST' else 'OPPDATER'} {change['name']}")


def apply_changes(repo, desired, initial, changes, backup_directory):
	if not changes:
		return
	if read_state(repo) != initial:
		raise PolicyError(f"{repo}: konfigurasjonen endret seg underveis; kjoer paa nytt.")
	backup_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
	fd, filename = tempfile.mkstemp(prefix=f"{repo}-", suffix=".json", dir=backup_directory)
	with os.fdopen(fd, "w") as output:
		json.dump({"repo": repo, "before": initial, "changes": changes}, output, indent=2)
	print(f"{repo}: tidligere konfigurasjon lagret i {filename}")
	for change in changes:
		response = github_api(change["method"], change["endpoint"], change["after"])
		endpoint = change["endpoint"]
		if change["method"] == "POST":
			endpoint += f"/{positive_id(response['id'], 'ressurs-ID')}"
		actual = github_api("GET", endpoint)
		if comparable(actual, change["after"]) != canonical(change["after"]):
			raise PolicyError(f"{repo}: tilbakelesing av {change['name']} avviker. "
				"Endringer kan allerede vaere utfoert; bruk sikkerhetskopien.")
		print(f"{repo}: UTFOERT {change['name']}")


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	selection = parser.add_mutually_exclusive_group(required=True)
	selection.add_argument("--repo", help="Kommaseparerte repo-navn, eller 'alle'.")
	selection.add_argument("--alle", action="store_true")
	selection.add_argument("--valider", action="store_true")
	parser.add_argument("--apply", action="store_true", help="Utfoer utrulling. Paakrevd ved API-kjoering.")
	parser.add_argument("--backup-dir", type=Path, default=ROOT / ".policy-backup")
	args = parser.parse_args()
	try:
		common, repositories = load_config()
		if args.valider:
			if args.apply:
				raise PolicyError("--valider kan ikke kombineres med andre operasjoner.")
			print("Policykonfigurasjonen er gyldig.")
			return 0
		names = select_repos(repositories, "alle" if args.alle else args.repo)
		if not args.apply:
			raise PolicyError("Utrulling krever --apply. Bruk --valider for lokal konfigurasjonsvalidering.")
		team_id = positive_id(int(os.environ.get("POLICY_TEAM_ID", "0")), "POLICY_TEAM_ID")
		app_id = positive_id(int(os.environ.get("AUTOMERGE_APP_ID", "0")), "AUTOMERGE_APP_ID")
		if not os.environ.get("GH_TOKEN"):
			raise PolicyError("GH_TOKEN maa settes til et installation token.")
		if os.environ.get("GITHUB_ACTIONS") == "true":
			if os.environ.get("GITHUB_REPOSITORY") != "navikt/dok-workflows" or (
				os.environ.get("GITHUB_REF") != f"refs/heads/{os.environ.get('POLICY_DEFAULT_BRANCH', '')}"
			):
				raise PolicyError("Apply er bare tillatt fra dok-workflows sin default branch.")
		for name in names:
			desired = desired_policy(common, repositories[name], team_id, app_id)
			state = read_state(name)
			changes = make_changes(name, desired, state)
			show_changes(name, changes, state, desired)
			apply_changes(name, desired, state, changes, args.backup_dir)
		return 0
	except (PolicyError, OSError, ValueError, KeyError, yaml.YAMLError, subprocess.TimeoutExpired) as error:
		print(f"FEIL: {error}", file=sys.stderr)
		if args.apply:
			print("Utrullingen er stoppet. Tidligere endringer er ikke automatisk tilbakefoert.", file=sys.stderr)
		return 1


if __name__ == "__main__":
	sys.exit(main())
