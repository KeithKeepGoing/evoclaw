# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.23] - 2026-03-12

### Fixed
- **Docker Image Dependencies**: Pre-installed system libraries (`libfreetype6`, `libpng16-16`, `zlib1g`) and Chinese fonts (`fonts-wqy-zenhei`) in `container/Dockerfile` to fix PPT/PDF generation failures.
- **Container Image Configuration**: Added support for `CONTAINER_IMAGE` environment variable in `host/config.py` to allow flexible Docker image tagging.

### Added
- **Documentation**:
  - `CHANGELOG.md`: Project changelog.
  - `RELEASE.md`: Standardized release procedure.
  - `ISSUES.md`: Known issues and PR plan tracking.
  - `.github/ISSUE_TEMPLATE/`: Templates for bug reports and feature requests.
  - `PULL_REQUEST_TEMPLATE.md`: Template for Pull Requests.
- **GitHub Workflow**: Initialized Git repository with proper commit messages and structure.

### Changed
- **README.md**: Updated with v1.10.23 release notes, `CONTAINER_IMAGE` configuration, and environment variable documentation.

## [1.10.22] - 2026-03-11
### Added
- Initial EvoClaw release with multi-channel support (Telegram, WhatsApp, etc.).
- Basic agent container isolation.
