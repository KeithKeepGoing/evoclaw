# Changelog

All notable changes to EvoClaw will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.8] - 2026-03-11

### Added — Dynamic Container Tool Hot-swap (Skills 2.0)

Solves the core Docker limitation for DevEngine-generated skills: new Python tools can now be installed into running containers without rebuilding the image.

#### Architecture: `data/dynamic_tools/` volume mount
- `host/container_runner.py`: `_build_volume_mounts()` now mounts `{DATA_DIR}/dynamic_tools/` → `/app/dynamic_tools:ro` in **every** container (both main and regular groups)
- `container/agent-runner/agent.py`: new `_load_dynamic_tools()` function — scans `/app/dynamic_tools/*.py` at startup and dynamically imports each file via `importlib.util`; `register_dynamic_tool` is injected into each module's namespace
- Drop a `.py` file into `data/dynamic_tools/`, next container run picks it up automatically — no `docker build` needed

#### Dynamic Tool Registry (`agent.py`)
- `_dynamic_tools: dict` — global in-process registry: `{name → {fn, schema, description}}`
- `register_dynamic_tool(name, description, schema, fn)` — appends to **all three** provider declaration lists (Gemini `TOOL_DECLARATIONS`, `CLAUDE_TOOL_DECLARATIONS`, `OPENAI_TOOL_DECLARATIONS`) and registers the dispatch function
- `_json_schema_to_gemini()` — converts JSON Schema properties dict to Gemini `types.Schema` at runtime (supports string, integer, boolean, object, array types)
- `_execute_tool_inner()` — falls back to `_dynamic_tools` dispatch after all built-in tools

#### Skills Engine: `container_tools:` manifest field
- `skills_engine/types.py`: `SkillManifest` dataclass gains `container_tools: list[str]` field (default `[]`)
- `skills_engine/manifest.py`: `read_manifest()` reads `container_tools:` from YAML
- `skills_engine/apply.py`: after `adds:` processing, copies `container_tools` files from `skill/add/` → `{DATA_DIR}/dynamic_tools/` (flattened by filename)
- `skills_engine/uninstall.py`: before replay, locates skill dir, reads manifest, removes its `container_tools` files from `dynamic_tools/`
- `dynamic_tools/.gitkeep` — git-tracked directory placeholder

### Example `manifest.yaml` with `container_tools:`
```yaml
skill: my-skill
version: "1.0.0"
adds:
  - docs/superpowers/my-skill/SKILL.md
container_tools:
  - dynamic_tools/my_tool.py   # injected at /app/dynamic_tools/my_tool.py
```

### Example dynamic tool file
```python
# dynamic_tools/my_tool.py  (inside skill add/ directory)
def _my_tool(args: dict) -> str:
    return f"Result: {args['input']}"

register_dynamic_tool(
    name="my_tool",
    description="Does something useful",
    schema={"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]},
    fn=_my_tool,
)
```

### Files Changed
- `host/container_runner.py` (dynamic_tools mount in `_build_volume_mounts`)
- `container/agent-runner/agent.py` (`_dynamic_tools` registry, `register_dynamic_tool`, `_load_dynamic_tools`, `_execute_tool_inner` fallback)
- `skills_engine/types.py` (`container_tools` field on `SkillManifest`)
- `skills_engine/manifest.py` (`container_tools` deserialization)
- `skills_engine/apply.py` (`container_tools` copy to `dynamic_tools/`)
- `skills_engine/uninstall.py` (`container_tools` cleanup before replay)
- `dynamic_tools/.gitkeep` (new)

---

## [1.10.7] - 2026-03-11

### Fixed
- **Telegram File Send Optimization**: Refined v1.10.1 binary file fix by removing redundant `disable_content_type_detection` parameter that caused compatibility issues.
- **Debug Log Delivery**: Enhanced error reporting to send debug logs directly to user's Telegram instead of writing to container-internal files (solving persistence issues in Docker).
- **Documentation Sync**: Ensured `CHANGELOG.md`, `README.md`, and `RELEASE.md` are properly synchronized with actual code changes.


## [1.10.6] - 2026-03-11

### Fixed (Code Review Findings)
- CRASH: .env shadow mount no longer double-prefixes `-v` flag (containers were failing to start on Linux/macOS)
- ERROR: run_container_agent now catches asyncio.CancelledError and calls _stop_container (outer timeout no longer creates zombie containers)
- ERROR: /api/dev/resume now writes IPC file to correct group folder path (DevEngine resume was silently broken)
- WARNING: cleanup_orphans now awaits proc.wait() after docker rm
- Minor: send_file tool schema — chat_jid removed from required[] (auto-detected from input)
- Minor: _resolve_container_path guards against empty group_folder
- Minor: TelegramChannel.send_file removes redundant filename parameter

## [1.10.5] - 2026-03-11

### Added
- **Comprehensive Container Agent Logging**: Added `_log(tag, msg)` helper with millisecond timestamps to `container/agent-runner/agent.py` for structured stderr logging throughout the agent lifecycle.
  - Startup: process ID logged at container boot (`🚀 START`).
  - Input parsed: JID, group folder, and message count (`📥 INPUT`).
  - Last message preview for quick debugging (`💬 MSG`).
  - Model/provider selection before first LLM call (`🤖 MODEL`).
  - Per-turn LLM call and response with stop reason (`🧠 LLM →/←`).
  - Tool dispatch with name and truncated args (`🔧 TOOL`).
  - Tool result preview (`🔧 RESULT`).
  - IPC file writes for messages, tasks, and files (`📨 IPC`).
  - File send path and existence check (`📎 FILE`).
  - Output size in chars before emit (`📤 OUTPUT`).
  - Exception type and message with full traceback to stderr (`❌ ERROR`).
  - Completion with success flag (`🏁 DONE`).
- **Noisy SDK log suppression**: `httpx`, `httpcore`, `google`, and `urllib3` loggers clamped to WARNING level.
- **Host stderr elevation**: `host/container_runner.py` `_stream_stderr()` now promotes emoji-tagged agent log lines from DEBUG to INFO so they appear in production logs without `--debug`.

## [1.10.1] - 2026-03-11

### Fixed
- **Telegram Channel**: Fixed critical bug in `send_file()` where binary files (e.g., `.pptx`, `.pdf`, `.jpg`) would fail to send due to incorrect encoding handling (`cp950 codec can't decode` error).
  - Changed file reading to explicitly use binary mode (`rb`) and read entire content before sending.
  - Now uses `telegram.InputFile` to ensure binary data is properly transmitted.
  - Added MIME type detection with fallback to `application/octet-stream`.
  - Set `disable_content_type_detection=True` to prevent Telegram from re-encoding files.
  - Improved error logging for file sending failures.

## [1.10.0] - 2026-03-10

### Added
- **Evolution Engine**: Full genome evolution with formality, technical_depth, and responsiveness genes.
- **Health Monitor**: Real-time system health tracking with automatic alerts.
- **DevEngine**: 7-stage automated development pipeline (Analyze → Design → Implement → Test → Review → Document → Deploy).
- **Web Dashboard**: 7-tab monitoring interface with Subagent hierarchy visualization.
- **Superpowers Integration**: 12 workflow skill packages from Superpowers methodology.

### Changed
- Replaced `threading.Lock` with `asyncio.Lock` for better async compatibility.
- GroupQueue now serializes container execution per group.
- WebPortal session timeout reduced to 1 hour.

### Fixed
- `_stop_container` now properly waits for `proc.wait()` to complete.
- `/api/env` now uses key whitelist for security.
- DevEngine JID fallback now provides clear error messages.
- macOS compatibility fixes for `.env` file handling.

## [1.9.0] - 2026-02-15

### Added
- **Immune System Enhancement**: 22 injection pattern detections.
- **Adaptive Evolution**: Epigenetic adaptation based on system load and time of day.
- **Evolution Log**: Complete history of genome changes in `evolution_log` table.

### Changed
- Improved container isolation and security.
- Enhanced error reporting in dashboard.

## [1.8.0] - 2026-02-01

### Added
- **Skills Engine**: Plugin system for adding new capabilities.
- **WhatsApp Support**: Optional skill for WhatsApp integration.
- **Multi-model Support**: Gemini, OpenAI-compatible, and Claude.

### Changed
- Refactored channel architecture for better modularity.

---

## Version History Summary

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.10.1 | 2026-03-11 | Fixed Telegram binary file sending bug |
| 1.10.0 | 2026-03-10 | Full evolution engine, DevEngine, Health Monitor |
| 1.9.0 | 2026-02-15 | Enhanced immune system, adaptive evolution |
| 1.8.0 | 2026-02-01 | Skills engine, WhatsApp support |
