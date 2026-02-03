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
        # Look for lines like "/dev/disk2 (external, physical):"
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

        # Parse each line like "   Key Name:   Value"
        for line in stdout.split('\n'):
            line = line.strip()
            if ':' not in line:
                continue

            # Split on first colon
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Store with normalized key names
            info[key] = value

        # Map to standardized field names for compatibility
        standardized = {
            'DeviceIdentifier': info.get('Device Identifier', disk_id),
            'MediaName': info.get('Device / Media Name', info.get('Media Name', 'Unknown')),
            'VolumeName': info.get('Volume Name', ''),
            'Mounted': info.get('Mounted', 'No') == 'Yes',
            'MountPoint': info.get('Mount Point', ''),
            'TotalSize': cls._parse_size(info.get('Disk Size', info.get('Total Size', '0'))),
            'FilesystemType': info.get('File System Personality', info.get('Type (Bundle)', 'Unknown')),
            'BusProtocol': info.get('Protocol', info.get('Device Location', 'Unknown')),
            'DeviceLocation': info.get('Device Location', 'Unknown'),
            'Removable': info.get('Removable Media', 'No') == 'Yes',
            'Content': info.get('Content (IOContent)', info.get('Partition Type', 'Unknown')),
            'PartitionType': info.get('Partition Type', ''),
        }

        return standardized

    @classmethod
    def _parse_size(cls, size_str: str) -> int:
        """
        Parse size string like '14.5 GB' to bytes.

        Args:
            size_str: Size string from diskutil

        Returns:
            Size in bytes
        """
        if not size_str or size_str == '0':
            return 0

        # Extract number and unit
        match = re.match(r'([\d.]+)\s*([KMGT]?B)', size_str, re.IGNORECASE)
        if not match:
            return 0

        value = float(match.group(1))
        unit = match.group(2).upper()

        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
            'TB': 1024 ** 4,
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

        # Parse lines like:
        # "   0:      GUID_partition_scheme                        *15.5 GB    disk2"
        # "   1:       EFI EFI                     209.7 MB   disk2s1"
        # "   2: Microsoft Basic Data OFFLINECRED  14.3 GB   disk2s2"
        # OR for whole disk:
        # "   0:                            OFFLINECRED            *15.6 GB    disk2"

        for line in stdout.split('\n'):
            # Look for partition entries (have a number, colon, and disk identifier)
            if re.search(r'\s+\d+:', line):
                # Skip partition scheme lines (line 0 usually)
                if 'scheme' in line.lower():
                    continue

                # Extract the disk identifier from the end of the line
                match = re.search(r'(disk\d+(?:s\d+)?)\s*$', line)
                if match:
                    partitions.append(match.group(1))

        return partitions