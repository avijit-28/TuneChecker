# MCP.md — Model Context Protocol Integration Policy

> Status: **Optional / Not required for the assessment MVP.**

## 1. Purpose

Model Context Protocol (MCP) can expose approved external tools to compatible AI clients. The Sales Call Quality Analysis Agent does not need MCP to upload audio, transcribe calls, diarize speakers, classify tone, or extract action items.

Do not add MCP merely for novelty. The local pipeline should work without MCP.

## 2. Recommended MVP decision

- MCP servers: none required.
- AI runtime: local Ollama through the application's backend service.
- Audio processing: local FFmpeg, Faster-Whisper, and pyannote adapters.
- Database access: through the application's SQLAlchemy service layer.
- Filesystem access: restricted to the configured audio storage directory.

## 3. Optional future MCP servers

Only consider these if a concrete user workflow requires them:

| MCP capability | Potential use | Default permission |
|---|---|---|
| Filesystem | Inspect approved project documentation | Read-only, scoped directory |
| GitHub | Read issues or create approved development issues | Read-only until explicitly authorized |
| Browser | Retrieve public technical documentation | Read-only |
| Database | Inspect development schema | Read-only; no production data |
| Documentation search | Search approved technical references | Read-only |

Do not configure a server unless its source, publisher, version, permissions, and security implications have been reviewed.

## 4. Tool permissions

Default to least privilege:
- Read-only access by default.
- No arbitrary shell execution.
- No arbitrary filesystem access.
- No unrestricted database writes.
- No access to `.env`, credentials, or private recordings.
- No network access to internal services unless explicitly required.
- Require human confirmation before destructive or externally visible actions.

## 5. Secrets and configuration

- Never place real API keys in this file.
- Use environment-variable placeholders.
- Do not commit tokens or private server configuration.
- Keep MCP credentials separate from model prompts.
- Rotate exposed credentials.

No concrete MCP server is selected for the MVP, so this document intentionally does not invent server package names or configuration snippets.

## 6. Testing future MCP connections

For each approved server:
1. Verify its source and version.
2. Review requested permissions.
3. Configure a test environment with dummy data.
4. Test read-only operations first.
5. Confirm denied operations are actually denied.
6. Test timeout and server-unavailable behavior.
7. Confirm secrets are not included in tool output or logs.
8. Document the approved tools and blocked tools.

## 7. Troubleshooting

- Server fails to start: verify runtime, command, and package version.
- Authentication fails: verify token scope and expiry; do not paste token into logs.
- Permission denied: check the explicitly scoped directory or resource.
- Tool timeout: reduce scope and set bounded timeouts.
- Unexpected write: disable the server and review its permissions immediately.

## 8. Final rule

The application must remain fully functional if all MCP integrations are absent. MCP is an optional developer-assistance capability, not a dependency of the call-analysis pipeline.
