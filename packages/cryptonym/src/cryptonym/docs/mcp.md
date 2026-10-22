# Cryptonym as an MCP server

Cryptonym ships a Model Context Protocol server so an agent (OpenCode, Claude Desktop,
any MCP client) can drive the same engine the CLI and the library use — no shell, no
copy-paste of JSON.

## Tools

| Tool | What it does |
|---|---|
| `assess_dossier(path)` | Re-derive the graded judgement for a saved dossier |
| `render_dossier(path)` | Render the markdown product |
| `export_dossier(path, format)` | Export STIX 2.1 / MISP Galaxy / TAXII 2.1 |
| `ingest_document(source, path)` | Normalise a source document into separate designations |
| `adjudicate_corpus(path, strict)` | Run the external-truth filter; report coverage and standards |
| `reconcile_linkages(linkages, minimum)` | Cluster designations at a confidence threshold, exposing the weakest link |
| `snapshot_verify(path)` | Re-check a source snapshot against its SHA-256 |
| `snapshot_source(url, allow_private)` | Fetch and capture a source (network, SSRF-validated) |
| `documentation(section)` | Return a method document (method, adjudication, architecture, data-model) |

Everything except `snapshot_source` is offline. Errors are returned as
`{"error": "..."}` rather than raised, so an agent can recover.

## Run it standalone

```bash
pip install -e '.[mcp]'
cryptonym-mcp            # stdio transport
```

## Register it in OpenCode

Add to `~/.config/opencode/opencode.json` under `mcp.servers`:

```json
"cryptonym": {
  "type": "local",
  "command": ["/root/.local/venvs/cryptonym-mcp/bin/cryptonym-mcp"],
  "timeout": { "startup": 30000 }
}
```

Then restart OpenCode. The tools appear namespaced as `cryptonym_*`.

## Why the repository can stay private

The server runs locally from an editable install, so nothing needs to be public. The
open-source form was a credibility asset; the private form is a personal capability. Both
are the same code.
