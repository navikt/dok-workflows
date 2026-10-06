package no.nav.dok.forvaltning;

import com.fasterxml.jackson.databind.JsonNode;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;

final class PolicyLoader {
	private static final Path POLICY_DIRECTORY = Path.of("policy");
	private static final String REPOSITORIES_FILE = "repoer.json";
	private PolicyLoader() {}

	static List<RepositoryPolicy> loadRepositories() throws IOException {
		var configuration = Json.requireObject(Json.parse(Files.readString(POLICY_DIRECTORY.resolve(REPOSITORIES_FILE))), REPOSITORIES_FILE);
		var commonRulesetNames = readRulesetNames(configuration.get("fellesregler"), "fellesregler");
		var repositoriesJson = Json.requireArray(configuration.get("repoer"), "repoer");

		if (repositoriesJson.isEmpty()) {
			throw new RulesetPublishException("%s maa inneholde minst ett repo.".formatted(REPOSITORIES_FILE));
		}

		var loadedRulesets = new HashMap<String, Ruleset>();
		var repositoryPolicies = new ArrayList<RepositoryPolicy>();
		for (var repositoryJson : repositoriesJson) {
			var repository = Json.requireObject(repositoryJson, "repoer");
			var repoName = Json.requireText(repository.get("navn"), "repoer: navn");
			var selectedRulesetNames = new LinkedHashSet<>(commonRulesetNames);

			if (repository.has("tilleggsregler")) {
				selectedRulesetNames.addAll(readRulesetNames(repository.get("tilleggsregler"), repoName + ": tilleggsregler"));
			}

			var selectedRulesets = new ArrayList<Ruleset>();
			for (var rulesetName : selectedRulesetNames) {
				var ruleset = loadedRulesets.get(rulesetName);
				if (ruleset == null) {
					ruleset = loadRuleset(rulesetName);
					loadedRulesets.put(rulesetName, ruleset);
				}
				selectedRulesets.add(ruleset);
			}

			repositoryPolicies.add(new RepositoryPolicy(repoName, List.copyOf(selectedRulesets)));
		}

		return List.copyOf(repositoryPolicies);
	}

	private static List<String> readRulesetNames(JsonNode rulesetNamesJson, String fieldLocation) {
		return Json.requireArray(rulesetNamesJson, fieldLocation).valueStream()
			.map(rulesetNameNode -> Json.requireText(rulesetNameNode, fieldLocation))
			.toList();
	}

	private static Ruleset loadRuleset(String rulesetName) throws IOException {
		if (!rulesetName.matches("dok-[a-z0-9-]+")) {
			throw new RulesetPublishException("%s: forventer et dok-navn.".formatted(rulesetName));
		}
		var rulesetPath = POLICY_DIRECTORY.resolve("rulesets").resolve(rulesetName + ".json");
		var rulesetJson = Json.requireObject(Json.parse(Files.readString(rulesetPath)), rulesetPath.toString());
		if (!rulesetName.equals(Json.requireText(rulesetJson.get("name"), rulesetPath + ": name"))) {
			throw new RulesetPublishException("%s: name maa samsvare med filnavnet.".formatted(rulesetPath));
		}
		return new Ruleset(rulesetName, Json.stringify(rulesetJson));
	}

	record RepositoryPolicy(String repoName, List<Ruleset> rulesets) {}
	record Ruleset(String rulesetName, String requestBody) {}
}
