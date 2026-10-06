package no.nav.dok.forvaltning;

import com.fasterxml.jackson.databind.JsonNode;

import java.math.BigInteger;
import java.util.List;

final class RulesetPublisher {
	private final GitHub github;

	RulesetPublisher(GitHub github) {
		this.github = github;
	}

	void publish(String repoName, List<PolicyLoader.Ruleset> rulesets) {
		var repoEndpoint = "repos/navikt/%s".formatted(repoName);
		var existingRulesets = github.fetchAllPages("%s/rulesets?includes_parents=false".formatted(repoEndpoint));
		var rulesetsEndpoint = "%s/rulesets".formatted(repoEndpoint);

		for (var ruleset : rulesets) {
			var existingRulesetId = findExistingId(repoName, ruleset.rulesetName(), existingRulesets);
			var httpMethod = existingRulesetId == null ? "POST" : "PUT";
			var targetEndpoint = existingRulesetId == null ? rulesetsEndpoint : rulesetsEndpoint + "/" + existingRulesetId;

			var apiResponse = github.callApi(httpMethod, targetEndpoint, ruleset.requestBody());
			System.out.printf("%s: %s %s%n", repoName, httpMethod, ruleset.rulesetName());

			if (!apiResponse.isNull()) {
				System.out.println(Json.stringify(apiResponse));
			}
		}
	}

	private static BigInteger findExistingId(String repoName, String rulesetName, List<JsonNode> existingRulesets) {
		var matchingRulesets = existingRulesets.stream()
			.filter(ruleset -> "Repository".equals(Json.requireText(ruleset.get("source_type"), "source_type"))
				&& rulesetName.equals(Json.requireText(ruleset.get("name"), "API policy-navn")))
			.limit(2)
			.toList();

		return switch (matchingRulesets.size()) {
			case 0 -> null;
			case 1 -> Json.requirePositiveId(matchingRulesets.getFirst().get("id"), "ressurs-ID");
			default -> throw new RulesetPublishException("%s: flere regler heter %s; avklar manuelt.".formatted(repoName, rulesetName));
		};
	}
}
