"""
macOS diskutil backend for USB LAB.
"""

import subprocess
import plistlib
import re
from typing import List, Dict, Optional
from .base import DiskBackend
from ..ui import print_error

class DiskUtilBackend:
    """
    macOS diskutil interface for read-only disk inspection.
    
    This backend interrogates disk structure using diskutil commands.
    All operations are read-only by design.
    """
    
    @staticmethod
    def run_command(cmd: List[str]) -> Tuple[bool, str, str]:
        """
        Execute a command safely and return success, stdout, stderr.
        
        Returns:
            (success: bool, stdout: str, stderr: str)
        """
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
        List all disk identifiers.
        
        Returns:
            List of disk identifiers (e.g., ['disk0', 'disk2', 'disk3'])
        """
        success, stdout, _ = cls.run_command(['diskutil', 'list', '-plist'])
        if not success:
            return []
        
        try:
            # diskutil list -plist returns XML plist
            import plistlib
            data = plistlib.loads(stdout.encode())
            
            # Extract physical disks only (diskX, not diskXsY)
            all_disks = data.get('AllDisksAndPartitions', [])
            physical_disks = []
            
            for disk_info in all_disks:
                disk_id = disk_info.get('DeviceIdentifier', '')
                if disk_id and re.match(r'^disk\d+$', disk_id):
                    physical_disks.append(disk_id)
            
            return physical_disks
        except Exception as e:
            print_error(f"Failed to parse disk list: {e}")
            return []
    
    @classmethod
    def get_disk_info(cls, disk_id: str) -> Optional[Dict]:
        """
        Get detailed information about a disk.
        
        Args:
            disk_id: Disk identifier (e.g., 'disk2')
        
        Returns:
            Dictionary of disk information or None if failed
        """
        success, stdout, _ = cls.run_command(['diskutil', 'info', '-plist', disk_id])
        if not success:
            return None
        
        try:
            import plistlib
            return plistlib.loads(stdout.encode())
        except Exception as e:
            print_error(f"Failed to parse disk info for {disk_id}: {e}")
            return None
    
    @classmethod
    def get_partition_info(cls, partition_id: str) -> Optional[Dict]:
        """
        Get detailed information about a partition.
        
        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')
        
        Returns:
            Dictionary of partition information or None if failed
        """
        return cls.get_disk_info(partition_id)
    
    @classmethod
    def list_partitions(cls, disk_id: str) -> List[str]:
        """
        List all partitions for a given disk.
        
        Args:
            disk_id: Disk identifier (e.g., 'disk2')
        
        Returns:
            List of partition identifiers (e.g., ['disk2s1', 'disk2s2'])
        """
        success, stdout, _ = cls.run_command(['diskutil', 'list', '-plist', disk_id])
        if not success:
            return []
        
        try:
            import plistlib
            data = plistlib.loads(stdout.encode())
            
            partitions = []
            for disk_info in data.get('AllDisksAndPartitions', []):
                if disk_info.get('DeviceIdentifier') == disk_id:
                    for part in disk_info.get('Partitions', []):
                        part_id = part.get('DeviceIdentifier', '')
                        if part_id:
                            partitions.append(part_id)
            
            return partitions
        except Exception as e:
            print_error(f"Failed to parse partition list for {disk_id}: {e}")
            return []


# ============================================================================
# CONTENT DETECTION & CLASSIFICATION
# ============================================================================

class ContentDetector:
