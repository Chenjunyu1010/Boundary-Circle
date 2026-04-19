# OpenAI-Compatible Freedom Tags Design

Date: 2026-04-18

## Goal

Enable the existing freedom-tags feature to use a real OpenAI-compatible LLM endpoint for keyword extraction while preserving the current fallback behavior and matching contract.

## Scope

This change will cover:

- runtime configuration for an OpenAI-compatible provider
- a concrete extractor implementation behind the existing extraction interface
- save-path integration for user freedom profiles and team freedom requirements
- tests that verify configured extraction and unconfigured fallback behavior

This change will not cover:

- `traits` or `domains` expansion
- natural-language matching explanations
- asynchronous extraction
- changes to matching score semantics

## Approach

Keep the current `FreedomProfileExtractor` abstraction and add one concrete provider implementation for OpenAI-compatible chat completions. The API save paths will ask a factory for the current extractor. When configuration is missing, the factory returns `None`, so the existing empty-keyword fallback remains unchanged.

This keeps the system deterministic at the matching layer. The LLM remains responsible only for extraction, while parsing, normalization, and failure handling stay in backend code.

## Configuration

Add these settings:

- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`

Activation rule:

- only enable real extraction when `LLM_PROVIDER=openai_compatible` and the key/model/base URL are all present
- otherwise return no extractor and keep the current fallback behavior

## Provider Contract

The provider will call an OpenAI-compatible `POST /chat/completions` endpoint and request JSON output in the shape:

```json
{"keywords": ["..."]}
```

The provider will:

- send a strict system prompt
- parse the first assistant message content
- accept plain JSON string output
- normalize through the existing backend normalization path
- return empty keywords on any HTTP, parsing, or schema error

## Integration Points

Update these save paths to use the extractor factory:

- `PUT /circles/{circle_id}/profile`
- `POST /teams`

No changes are needed in matching or frontend display because they already consume stored keyword JSON.

## Testing

Add focused tests for:

- extractor factory returns `None` when config is absent
- extractor factory returns provider when config is present
- provider parses a valid OpenAI-compatible response
- provider falls back on malformed JSON
- circle profile save uses configured extractor output
- team creation uses configured extractor output

## Success Criteria

- existing no-provider behavior still passes
- configured extraction stores non-empty keyword profiles
- matching continues to work without contract changes
