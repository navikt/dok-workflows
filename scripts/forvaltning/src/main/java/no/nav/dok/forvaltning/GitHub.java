package no.nav.dok.forvaltning;

import com.fasterxml.jackson.databind.JsonNode;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

final class GitHub {
	private static final Duration TIMEOUT = Duration.ofSeconds(120);
	private static final Duration STOP_TIMEOUT = Duration.ofSeconds(5);
	private static final Pattern HTTP_STATUS_PATTERN = Pattern.compile("\\(HTTP (\\d{3})\\)");

	JsonNode callApi(String httpMethod, String endpoint) {
		return callApi(httpMethod, endpoint, null);
	}

	JsonNode callApi(String httpMethod, String endpoint, String requestBody) {
		var apiCommand = new ArrayList<>(List.of("gh", "api", "--hostname", "github.com",
			"--method", httpMethod, "-H", "Accept: application/vnd.github+json",
			"-H", "X-GitHub-Api-Version: 2026-03-10", endpoint));

		try {
			return execute(apiCommand, endpoint, requestBody);
		} catch (InterruptedException exception) {
			Thread.currentThread().interrupt();
			throw new RulesetPublishException("GitHub API-kallet ble avbrutt for %s.".formatted(endpoint), exception);
		} catch (IOException exception) {
			throw new RulesetPublishException("Kunne ikke kjoere gh for %s. Kontroller at GitHub CLI er installert.".formatted(endpoint), exception);
		}
	}

	private JsonNode execute(List<String> apiCommand, String endpoint, String requestBody) throws IOException, InterruptedException {
		boolean apiCallSucceeded = false;

		try (var processFiles = new ProcessFiles(Files.createTempDirectory("dok-gh-"))) {
			if (requestBody != null) {
				Files.writeString(processFiles.inputFile(), requestBody);
				apiCommand.addAll(List.of("--input", processFiles.inputFile().toString()));
			}

			try (var managedProcess = new ManagedProcess(new ProcessBuilder(apiCommand)
					.redirectOutput(processFiles.stdout().toFile())
					.redirectError(processFiles.stderr().toFile())
					.start())) {

				var ghProcess = managedProcess.process();
				ghProcess.getOutputStream().close();

				if (!ghProcess.waitFor(TIMEOUT)) {
					throw new RulesetPublishException("GitHub API tidsavbrudd etter %s sekunder for %s.".formatted(TIMEOUT.toSeconds(), endpoint));
				}

				if (ghProcess.exitValue() != 0) {
					var httpStatusMatcher = HTTP_STATUS_PATTERN.matcher(Files.readString(processFiles.stderr()));
					String httpStatus = httpStatusMatcher.find() ? httpStatusMatcher.group(1) : "ukjent";
					// Ikke skriv feilrespons, stderr eller token fra gh til logger.
					throw new RulesetPublishException("GitHub API feilet for %s (HTTP %s).".formatted(endpoint, httpStatus));
				}

				apiCallSucceeded = true;
				var responseBody = Files.readString(processFiles.stdout());
				return responseBody.isBlank() ? Json.MAPPER.nullNode() : Json.parse(responseBody);
			}
		} catch (IOException exception) {
			if (apiCallSucceeded) {
				throw new RulesetPublishException("GitHub API-kallet for %s lyktes, men lesing av respons eller opprydding feilet. Eventuelle endringer paa GitHub er allerede utfoert.".formatted(endpoint), exception);
			}
			throw exception;
		}
	}

	List<JsonNode> fetchAllPages(String endpoint) {
		var allItems = new ArrayList<JsonNode>();
		String querySeparator = endpoint.contains("?") ? "&" : "?";

		for (int pageNumber = 1; ; pageNumber++) {
			var apiResponse = callApi("GET", "%s%sper_page=100&page=%d".formatted(endpoint, querySeparator, pageNumber));
			var pageItems = Json.requireArray(apiResponse, "Liste fra %s".formatted(endpoint));

			pageItems.forEach(allItems::add);

			if (pageItems.size() < 100) {
				return List.copyOf(allItems);
			}
		}
	}

	private record ManagedProcess(Process process) implements AutoCloseable {
		@Override
		public void close() throws InterruptedException {
			if (process.isAlive()) {
				process.destroyForcibly();
				try {
					if (!process.waitFor(STOP_TIMEOUT)) {
						throw new RulesetPublishException("Kunne ikke stoppe gh-prosessen innen fem sekunder.");
					}
				} catch (InterruptedException exception) {
					Thread.currentThread().interrupt();
					throw exception;
				}
			}
		}
	}

	private record ProcessFiles(Path tempDirectory) implements AutoCloseable {
		Path stdout() {
			return tempDirectory.resolve("stdout");
		}

		Path stderr() {
			return tempDirectory.resolve("stderr");
		}

		Path inputFile() {
			return tempDirectory.resolve("input.json");
		}

		@Override
		public void close() throws IOException {
			IOException cleanupException = null;
			for (var cleanupPath : List.of(stdout(), stderr(), inputFile(), tempDirectory)) {
				try {
					Files.deleteIfExists(cleanupPath);
				} catch (IOException exception) {
					if (cleanupException == null) {
						cleanupException = exception;
					} else {
						cleanupException.addSuppressed(exception);
					}
				}
			}
			if (cleanupException != null) {
				throw cleanupException;
			}
		}
	}
}
