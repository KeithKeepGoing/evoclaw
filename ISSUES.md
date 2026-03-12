# EvoClaw Known Issues & PR Plan

This document tracks known issues, their status, and the plan for Pull Requests (PRs).

## Critical Issues (Fixed)

| # | Issue | Status | PR | Notes |
|---|-------|--------|-----|-------|
| 1 | Docker image missing system libraries for PPT/PDF generation | ✅ Fixed | #1 | Added `libfreetype6`, `libpng16-16`, `zlib1g`, `fonts-wqy-zenhei` to `container/Dockerfile`. |
| 2 | Missing `CONTAINER_IMAGE` environment variable support | ✅ Fixed | #1 | `host/config.py` now reads `CONTAINER_IMAGE` from env. |
| 3 | Missing standardized release documentation | ✅ Fixed | #1 | Added `RELEASE.md`. |
| 4 | Missing Changelog maintenance | ✅ Fixed | #1 | Added `CHANGELOG.md`. |

## High Priority Issues (Open)

| # | Issue | Status | PR | Notes |
|---|-------|--------|-----|-------|
| 5 | File sending race condition | 📝 Open | - | Host may try to send file before it's fully written. Needs file lock or size check. |
| 6 | Dashboard missing container image version display | 📝 Open | - | Dashboard should show which image version is running. |

## Medium Priority Issues (Open)

| # | Issue | Status | PR | Notes |
|---|-------|--------|-----|-------|
| 7 | Missing CI/CD automation | 📝 Open | - | Need automated testing and Docker build on push. |
| 8 | Missing container resource limits | 📝 Open | - | `CONTAINER_MEMORY` and `CONTAINER_CPUS` env vars added but not enforced in all runners. |
| 9 | Evolution engine persistence | 📝 Open | - | Genome updates should be persisted more robustly. |
| 10 | Web portal file upload | 📝 Open | - | Web portal lacks file upload capability for RAG. |

## How to Contribute

1. Pick an issue from the list above.
2. Create a new branch: `git checkout -b fix/issue-<number>-<description>`.
3. Make your changes and commit with a clear message.
4. Open a Pull Request referencing the issue number.
5. Wait for review and merge.
