package no.nav.dok.forvaltning;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;

import java.math.BigInteger;

final class Json {
	static final ObjectMapper MAPPER = JsonMapper.builder()
		.enable(
			DeserializationFeature.FAIL_ON_READING_DUP_TREE_KEY,
			DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
		.build();

	private Json() {}

	static JsonNode parse(String jsonContent) {
		try {
			var parsedJson = MAPPER.readTree(jsonContent);
			if (parsedJson == null) {
				throw new RulesetPublishException("Forventet JSON.");
			}
			return parsedJson;
		} catch (JsonProcessingException exception) {
			throw new RulesetPublishException("Ugyldig JSON (kontroller syntaks og dupliserte feltnavn).");
		}
	}

	static String stringify(Object jsonValue) {
		try {
			return MAPPER.writeValueAsString(jsonValue);
		} catch (JsonProcessingException exception) {
			throw new RulesetPublishException("Kunne ikke skrive JSON.");
		}
	}

	static ObjectNode requireObject(JsonNode jsonNode, String fieldLocation) {
		if (jsonNode instanceof ObjectNode objectNode) {
			return objectNode;
		}
		throw new RulesetPublishException(fieldLocation + ": forventer et objekt.");
	}

	static ArrayNode requireArray(JsonNode jsonNode, String fieldLocation) {
		if (jsonNode instanceof ArrayNode arrayNode) {
			return arrayNode;
		}
		throw new RulesetPublishException(fieldLocation + ": forventer en liste.");
	}

	static String requireText(JsonNode jsonNode, String fieldLocation) {
		if (jsonNode instanceof TextNode textNode) {
			return textNode.textValue();
		}
		throw new RulesetPublishException(fieldLocation + ": forventer en streng.");
	}

	static BigInteger requirePositiveId(JsonNode idNode, String fieldLocation) {
		if (idNode == null || !idNode.isIntegralNumber() || idNode.bigIntegerValue().signum() <= 0) {
			throw new RulesetPublishException(fieldLocation + ": forventer en positiv numerisk GitHub-ID.");
		}
		return idNode.bigIntegerValue();
	}
}
