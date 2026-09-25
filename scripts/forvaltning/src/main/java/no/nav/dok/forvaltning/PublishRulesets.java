package no.nav.dok.forvaltning;

import java.io.IOException;

public final class PublishRulesets {
	void main() {
		try {
			var repositoryPolicies = PolicyLoader.loadRepositories();
			var rulesetPublisher = new RulesetPublisher(new GitHub());

			var repoNames = repositoryPolicies.stream().map(PolicyLoader.RepositoryPolicy::repoName).toList();
			System.out.println("Ruller ut felles regler til: " + String.join(", ", repoNames));
			repositoryPolicies.forEach(repository -> rulesetPublisher.publish(repository.repoName(), repository.rulesets()));

		} catch (RulesetPublishException | IOException exception) {
			System.err.println("FEIL: " + exception.getMessage());
			System.err.println("Utrullingen er stoppet. Tidligere endringer er ikke automatisk tilbakefoert.");
			System.exit(1);
		}
	}
}
