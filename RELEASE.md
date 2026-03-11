# Release Process

This document describes the release process for EvoClaw.

## Pre-release Checklist

Before creating a new release, ensure:

- [ ] All new features are documented in `CHANGELOG.md`
- [ ] `README.md` version banner is updated
- [ ] All tests pass (`python -m pytest tests/`)
- [ ] No critical bugs in the issue tracker
- [ ] Version number is updated in relevant files

## Release Steps

### 1. Update Documentation

**Update `CHANGELOG.md`:**
- Add new version section with date
- List all changes under `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
- Move `[Unreleased]` changes to the new version

**Update `README.md`:**
- Update version banner (e.g., `**v1.10.1**`)
- Ensure feature list is current

### 2. Commit Changes

```bash
git add CHANGELOG.md README.md
git commit -m "chore: prepare release v1.10.1"
```

### 3. Create Git Tag

```bash
# Create annotated tag
git tag -a v1.10.1 -m "Release version 1.10.1"

# Verify tag
git tag -l
git show v1.10.1
```

### 4. Push to Remote

```bash
# Push commits
git push origin main

# Push tag
git push origin v1.10.1
```

### 5. Create GitHub Release

1. Go to [GitHub Releases](https://github.com/KeithKeepGoing/evoclaw/releases)
2. Click "Draft a new release"
3. Select the tag `v1.10.1`
4. Use the following template:

```markdown
## 🎉 What's New

### 🐛 Bug Fixes
- Fixed critical bug in Telegram channel where binary files would fail to send

### 📝 Documentation
- Updated CHANGELOG.md with new format
- Added RELEASE.md for release process

## 📦 Installation

```bash
git clone https://github.com/KeithKeepGoing/evoclaw.git
cd evoclaw
git checkout v1.10.1
python setup/setup.py
```

## 🔗 Links
- [Full Changelog](https://github.com/KeithKeepGoing/evoclaw/blob/main/CHANGELOG.md)
- [Documentation](https://github.com/KeithKeepGoing/evoclaw#readme)
```

5. Click "Publish release"

### 6. Notify Users

- Post in project discussions/announcements
- Update any relevant community channels

## Version Numbering

EvoClaw follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.10.1)
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Examples

- `1.10.0` → `1.10.1`: Bug fix patch
- `1.10.1` → `1.11.0`: New feature (minor)
- `1.11.0` → `2.0.0`: Breaking change (major)

## Hotfix Process

For critical bugs requiring immediate fix:

1. Create hotfix branch from tag: `git checkout -b hotfix/v1.10.1-fix v1.10.1`
2. Apply fix and commit
3. Update version to `1.10.2`
4. Follow release steps above
5. Merge hotfix back to main

## Release Notes Template

```markdown
## [VERSION] - YYYY-MM-DD

### Added
- New features here

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```

## Verification

After release, verify:

- [ ] Tag is visible on GitHub
- [ ] Release notes are correct
- [ ] Installation from tag works
- [ ] All features function as expected
- [ ] Documentation is accessible

---

**Last Updated:** 2026-03-11 (v1.10.7)
