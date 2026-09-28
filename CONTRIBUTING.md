# Contributing

Use the numbered roadmap to keep changes focused. Discuss architectural changes and provider integrations in issues before making broad changes. Preserve local-only discovery and avoid analytics by default.

Run `python -m unittest discover -s tests -v`. Never commit user chats, SQLite data, credentials, downloaded model weights, or copied proprietary hub content. Add focused tests for data integrity and security boundaries when changing them. Clearly label planned connectors and capabilities; a registry entry is not a working integration.

When adding a source, record its identity, access method, terms/licensing review, credentials, limits, evidence format, and offline behavior. Treat fetched text as untrusted. When changing ranking, include examples showing the effect on recommendations and preserve hard constraints.
