# USB LAB

USB Drive Analysis, Testing & Benchmarking Suite for macOS

## Overview

USB LAB is a command-line tool for inspecting USB flash drives and measuring their performance. It provides read-only drive inspection, installer media detection, and comprehensive speed testing with persistent SQLite logging.

## Requirements

- macOS 10.14 or later
- Python 3.8+
- No external dependencies (standard library only)

## Installation

```bash
chmod +x usb_lab.py
./usb_lab.py
```

Optional: Create system-wide command

```bash
sudo ln -s "$(pwd)/usb_lab.py" /usr/local/bin/usb-lab
```

## Features

**Drive Inspection**
- Automatic detection of external USB drives
- Filesystem and partition analysis
- Installer media detection (macOS, Linux, Windows)
- UEFI partition recognition

**Performance Testing**
- Health checks and integrity verification
- Sequential read/write benchmarks
- Random 4K IOPS testing
- Configurable test parameters

**Data Management**
- SQLite database for all test results
- Test history and performance tracking
- Drive registry and inspection logs
- Configurable settings

## Usage

```bash
./usb_lab.py
```

Main menu options:
1. Examine Drives - Inspect USB drives (read-only)
2. Read/Write Speed Tests - Benchmark performance
3. View Test History - Review past results
4. Drive Database - Manage drive records
5. Settings - Configure application
Q. Quit

## Safety Features

- All inspections are read-only by default
- Automatic protection of installer and boot media
- User confirmation required before write operations
- Automatic cleanup of test files

## Data Storage

- Database: `~/.usb_lab/usb_lab.db`
- Settings: `~/.usb_lab/settings.json`
- Logs: `~/.usb_lab/logs/`

## Architecture

```
backend/        Platform-specific disk operations (macOS diskutil)
core/           Data models and enumerations
database/       SQLite database management
detection/      Installer media detection
inspection/     Disk examination and mounting
settings/       Configuration management
testing/        Performance testing engine
ui/             Terminal interface and menus
```

## Example Output

```
DISK: disk2 - SanDisk Ultra USB 3.0

Physical Disk Information:
  Size: 58.4 GB
  Bus Protocol: USB 3.1
  Partition Scheme: GUID_partition_scheme

Classification:
  Type: Data Storage
  Confidence: High

Partitions (1):
  [1] disk2s1 - MOUNTED
      Filesystem: exFAT
      Size: 58.4 GB
```

Performance test results:
```
Health Check: PASS
Sequential Read: 127.45 MB/s
Sequential Write: 89.23 MB/s
Random 4K Read: 3421.2 IOPS (13.37 MB/s)
Random 4K Write: 1876.5 IOPS (7.33 MB/s)
```

## Configuration

Settings can be modified through the Settings menu or by editing `~/.usb_lab/settings.json`

Key settings:
- Default inspection mode (smart_auto, metadata_only, mounted_readonly)
- Test file sizes and operation counts
- Safety guards and confirmation requirements
- Display options

## Roadmap

**Version 0.4.0**
- Database export (JSON/CSV)
- Additional test types (sustained write, thermal throttle)

**Version 0.5.0**
- Linux support
- Cross-platform backend abstraction

**Version 1.0.0**
- Windows support
- SMART data integration
- Advanced analytics

## License

Released under the MIT License.

## Documentation

- CHANGELOG.md - Version history
