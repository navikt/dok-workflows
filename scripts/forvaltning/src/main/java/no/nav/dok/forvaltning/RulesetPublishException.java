package no.nav.dok.forvaltning;

final class RulesetPublishException extends RuntimeException {
	RulesetPublishException(String message) {
		super(message);
	}

	RulesetPublishException(String message, Throwable cause) {
		super(message, cause);
	}
}
