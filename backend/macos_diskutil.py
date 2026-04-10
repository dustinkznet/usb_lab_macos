"""
macOS diskutil backend for USB LAB - SIMPLIFIED VERSION
Just parse the human-readable output instead of dealing with plist complexity.
"""

import subprocess
import re
from typing import List, Dict, Optional, Tuple


class DiskUtilBackend:
    """
    macOS diskutil interface - SIMPLIFIED to parse text output.
    """

    @staticmethod
    def run_command(cmd: List[str]) -> Tuple[bool, str, str]:
        """Execute a command safely and return success, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    @classmethod
    def list_all_disks(cls) -> List[str]:
        """
        List all physical disk identifiers.

        Returns:
            List of disk identifiers (e.g., ['disk0', 'disk2', 'disk3'])
        """
        success, stdout, _ = cls.run_command(['diskutil', 'list'])
        if not success:
            return []

        disks = []
        for line in stdout.split('\n'):
            match = re.match(r'^/dev/(disk\d+)\s+\(', line)
            if match:
                disks.append(match.group(1))

        return disks

    @classmethod
    def get_disk_info(cls, disk_id: str) -> Optional[Dict]:
        """
        Get detailed information about a disk by parsing diskutil info output.

        Args:
            disk_id: Disk identifier (e.g., 'disk2' or 'disk2s1')

        Returns:
            Dictionary of disk information
        """
        success, stdout, _ = cls.run_command(['diskutil', 'info', disk_id])
        if not success:
            return None

        info = {}

        for line in stdout.split('\n'):
            line = line.strip()
            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            info[key] = value

        fs_type_from_list = cls._get_filesystem_from_list(disk_id)

        # FIXED: Extract actual device serial number
        serial_number = info.get('Device / Media Serial Number',
                                info.get('Disk / Partition UUID', disk_id))

        # FIXED: Prioritize File System Personality (more accurate than diskutil list)
        fs_personality = info.get('File System Personality', info.get('Type (Bundle)', ''))

        standardized = {
            'DeviceIdentifier': info.get('Device Identifier', disk_id),
            'MediaName': info.get('Device / Media Name', info.get('Media Name', 'Unknown')),
            'VolumeName': info.get('Volume Name', ''),
            'Mounted': info.get('Mounted', 'No') == 'Yes',
            'MountPoint': info.get('Mount Point', ''),
            'TotalSize': cls._parse_size(info.get('Disk Size', info.get('Total Size', '0'))),
            'FilesystemType': fs_personality or fs_type_from_list or 'Unknown',
            'BusProtocol': info.get('Protocol', info.get('Device Location', 'Unknown')),
            'DeviceLocation': info.get('Device Location', 'Unknown'),
            'Removable': info.get('Removable Media', 'No') == 'Yes',
            'Content': info.get('Content (IOContent)', info.get('Partition Type', 'Unknown')),
            'PartitionType': info.get('Partition Type', ''),
            'SerialNumber': serial_number,
            'VolumeUUID': info.get('Volume UUID', ''),
        }

        return standardized

    @classmethod
    def _get_filesystem_from_list(cls, partition_id: str) -> Optional[str]:
        """
        Get filesystem type from diskutil list output.
        This is more reliable than diskutil info for some filesystems like NTFS.

        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')

        Returns:
            Filesystem type string or None
        """
        match = re.match(r'(disk\d+)', partition_id)
        if not match:
            return None

        disk_id = match.group(1)

        success, stdout, _ = cls.run_command(['diskutil', 'list', disk_id])
        if not success:
            return None

        for line in stdout.split('\n'):
            if partition_id in line and re.search(r'\s+\d+:', line):
                match = re.search(r'\s+\d+:\s+(\S+)', line)
                if match:
                    return match.group(1)

        return None

    @classmethod
    def _parse_size(cls, size_str: str) -> int:
        """
        Parse a diskutil size string to bytes.

        diskutil output looks like: "16.0 GB (16005464064 Bytes)"
        Prefer the exact byte count in parentheses when present, since the
        rounded human-readable value loses precision and uses decimal units
        (16.0 GB ≠ 16 * 1024^3 bytes).
        """
        if not size_str or size_str == '0':
            return 0

        # Prefer the exact "(N Bytes)" form
        bytes_match = re.search(r'\((\d+)\s*Bytes?\)', size_str, re.IGNORECASE)
        if bytes_match:
            return int(bytes_match.group(1))

        # Fall back to the human-readable value (decimal units, as diskutil reports)
        match = re.match(r'([\d.]+)\s*([KMGT]?B)', size_str, re.IGNORECASE)
        if not match:
            return 0

        value = float(match.group(1))
        unit = match.group(2).upper()

        multipliers = {
            'B': 1,
            'KB': 1000,
            'MB': 1000 ** 2,
            'GB': 1000 ** 3,
            'TB': 1000 ** 4,
        }

        return int(value * multipliers.get(unit, 1))

    @classmethod
    def get_partition_info(cls, partition_id: str) -> Optional[Dict]:
        """Get detailed information about a partition."""
        return cls.get_disk_info(partition_id)

    @classmethod
    def list_partitions(cls, disk_id: str) -> List[str]:
        """
        List all partitions for a given disk.

        HANDLES TWO CASES:
        1. Partitioned disk: disk2s1, disk2s2, etc.
        2. Whole disk format (no partition table): just disk2 itself

        Args:
            disk_id: Disk identifier (e.g., 'disk2')

        Returns:
            List of partition identifiers (e.g., ['disk2s1', 'disk2s2'] or ['disk2'])
        """
        success, stdout, _ = cls.run_command(['diskutil', 'list', disk_id])
        if not success:
            return []

        partitions = []

        for line in stdout.split('\n'):
            if re.search(r'\s+\d+:', line):
                if 'scheme' in line.lower():
                    continue

                match = re.search(r'(disk\d+(?:s\d+)?)\s*$', line)
                if match:
                    partitions.append(match.group(1))

        return partitions