# EvoClaw Release Procedure

This document outlines the standard procedure for releasing a new version of EvoClaw.

## Pre-Release Checklist

- [ ] All issues for the milestone are closed or deferred.
- [ ] `CHANGELOG.md` is updated with the new version number, date, and changes.
- [ ] `README.md` is updated with the latest version number and any relevant notes.
- [ ] All tests pass locally and in CI (if applicable).
- [ ] Docker image builds successfully with the new tag.

## Release Steps

1. **Bump Version**: Update version numbers in relevant files (e.g., `README.md`, `CHANGELOG.md`).
2. **Commit Changes**: Commit all changes with a message like `chore: release v1.10.23`.
3. **Create Tag**: Create a Git tag for the release (e.g., `v1.10.23`).
   ```bash
   git tag v1.10.23
   git push origin v1.10.23
   ```
4. **Build Docker Image**: Build and push the Docker image with the new version tag.
   ```bash
   docker build -t evoclaw-agent:1.10.23 -t evoclaw-agent:latest container/
   docker push evoclaw-agent:1.10.23
   docker push evoclaw-agent:latest
   ```
5. **Create GitHub Release**: Go to the GitHub Releases page, create a new release using the tag, and copy the changelog entry.
6. **Announce**: Announce the release in relevant channels (e.g., Telegram group, Discord).

## Post-Release

- [ ] Verify the new Docker image works as expected.
- [ ] Monitor logs for any immediate issues.
- [ ] Update any documentation or deployment scripts if necessary.
