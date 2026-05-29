# Changelog

All notable changes to USB LAB are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Note: releases before 0.3.0 were not tagged. This file starts at the current
> baseline (0.3.0) and reconstructs the recent history from git; earlier detail
> lives in the commit log.

## [Unreleased]

### Added
- Project spine: `VERSION`, `CHANGELOG.md`, `TODO.md`, `_RUNBOOK.md`, and a
  filled-in `CLAUDE.md` (scaffolded from template schema 22, `cli` overlay).

## [0.3.0] — 2026-05-29

Baseline release. Core feature set is in place and the menu/settings work is done.

### Added
- Drive inspection (read-only): USB detection, filesystem/partition analysis.
- Installer/boot media detection (macOS / Linux / Windows / UEFI) via marker files.
- Speed testing: health check, sequential read/write, random 4K IOPS.
- SQLite persistence of results + test history at `~/.usb_lab/usb_lab.db`.
- Settings management via `~/.usb_lab/settings.json`.

### Fixed
- Mount flag handling during inspection.
- EFI/UEFI partition misclassification.
- Duplicate database entries.

### Changed
- Compact header with small mascot.
- Menu refactor and settings wiring; removed dead code and unimplemented
  feature claims.

[Unreleased]: https://github.com/<GITHUB_HANDLE>/usb_lab_macos/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/<GITHUB_HANDLE>/usb_lab_macos/releases/tag/v0.3.0
