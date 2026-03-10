# Changelog

All notable changes to EvoClaw will be documented in this file.

## [1.3.0] — 2026-03-10

### New Features

**Web Dashboard** (`host/dashboard.py`, default port 8765)
- Pure Python stdlib — no external dependencies
- Dark theme dashboard with 9 sections: Groups, Scheduled Tasks, Task Run Logs, Sessions, Messages, Evolution Stats, Evolution Log, Immune Threats
- HTTP Basic Auth via env vars `DASHBOARD_USER` / `DASHBOARD_PASSWORD`
- `/health` endpoint — checks DB + Docker, returns JSON 200/503
- `/metrics` endpoint — Prometheus-format row counts
- Auto-refresh every 10 seconds

**Web Portal** (`host/webportal.py`, default port 8766)
- Browser-based chat interface (polling-based, no WebSocket dependency)
- Group selector, scrollable chat, 1-second polling
- `deliver_reply()` function for pushing bot responses to browser

**Evolution Process Logging**
- New `evolution_log` DB table records every evolution event with full before/after genome snapshot
- 5 event types: `genome_evolved`, `genome_unchanged`, `cycle_start`, `cycle_end`, `skipped_low_samples`
- Dashboard shows last 30 evolution events with color-coded event types

**Agent Tools: list_tasks + cancel_task**
- Container agent can now call `list_tasks()` to see all scheduled tasks
- Container agent can call `cancel_task(task_id)` to cancel a task
- Scheduled tasks are exposed to the agent via `scheduledTasks` in the input payload

**Task Status Tracking**
- Scheduled tasks now have a `status` field: `active`, `error`, `cancelled`
- Orphan tasks (empty `chat_jid`) auto-cleaned on startup
- Scheduler marks tasks `error` when group not found — prevents infinite retry loop

**IPC chat_jid Defensive Fallback**
- `ipc_watcher.py` now resolves `chat_jid` from registered groups by folder name if missing from payload
- Makes old Docker images compatible without rebuild

### New Environment Variables

```
DASHBOARD_PORT=8765        # Web dashboard port
DASHBOARD_USER=admin       # Dashboard Basic Auth username
DASHBOARD_PASSWORD=        # Dashboard Basic Auth password (empty = no auth)
WEBPORTAL_ENABLED=false    # Enable browser chat interface
WEBPORTAL_PORT=8766        # Web portal port
WEBPORTAL_HOST=127.0.0.1  # Web portal bind host
```

### Bug Fixes

- Fixed `[DEBUG]` log messages using `log.info()` instead of `log.debug()`
- Fixed `_running` flags that were set True but never reset to False (changed to `while True:`)
- Fixed `IPC_POLL_INTERVAL` env var parsing (now uses `_env_int()` helper)
- Fixed scheduler infinite warning loop for tasks with empty `chat_jid`
- Fixed `conversation_history` kwarg compatibility in container runner

---

## [1.2.0](https://github.com/qwibitai/evoclaw/compare/v1.1.6...v1.2.0)

[BREAKING] WhatsApp removed from core, now a skill. Run `/add-whatsapp` to re-add (existing auth/groups preserved).
- **fix:** Prevent scheduled tasks from executing twice when container runtime exceeds poll interval (#138, #669)
