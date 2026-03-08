"""
Safe mounting helper for disk inspection.
"""

import subprocess
import tempfile
import os
from typing import Optional, Tuple
from backend.macos_diskutil import DiskUtilBackend


class MountHelper:
    """
    Helper class for safe read-only mounting operations.
    
    All mounts are read-only by default to prevent accidental modifications.
    """
    
    @staticmethod
    def mount_readonly(partition_id: str) -> Tuple[bool, Optional[str], str]:
        """
        Mount a partition read-only.
        
        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')
        
        Returns:
            (success: bool, mount_point: Optional[str], message: str)
        """
        # Check if already mounted
        info = DiskUtilBackend.get_partition_info(partition_id)
        if not info:
            return False, None, f"Failed to get info for {partition_id}"
        
        existing_mount = info.get('MountPoint')
        if existing_mount:
            return True, existing_mount, f"Already mounted at {existing_mount}"
        
        # Create temporary mount point
        try:
            mount_point = tempfile.mkdtemp(prefix=f"usb_lab_{partition_id}_")
        except Exception as e:
            return False, None, f"Failed to create mount point: {e}"
        
        # Mount read-only
        success, stdout, stderr = DiskUtilBackend.run_command([
            'diskutil', 'mount', '-mountPoint', mount_point,
            'readOnly', partition_id
        ])
        
        if success:
            return True, mount_point, f"Mounted read-only at {mount_point}"
        else:
            # Clean up temp directory if mount failed
            try:
                os.rmdir(mount_point)
            except:
                pass
            return False, None, f"Mount failed: {stderr}"
    
    @staticmethod
    def unmount(partition_id: str, mount_point: Optional[str] = None) -> Tuple[bool, str]:
        """
        Unmount a partition.
        
        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')
            mount_point: Optional mount point to clean up
        
        Returns:
            (success: bool, message: str)
        """
        success, stdout, stderr = DiskUtilBackend.run_command([
            'diskutil', 'unmount', partition_id
        ])
        
        # Clean up temporary mount point if it was created by us
        if mount_point and mount_point.startswith('/tmp/usb_lab_'):
            try:
                os.rmdir(mount_point)
            except Exception as e:
                # Not critical if cleanup fails
                pass
        
        if success:
            return True, f"Unmounted {partition_id}"
        else:
            return False, f"Unmount failed: {stderr}"
    
    @staticmethod
    def is_mounted(partition_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a partition is currently mounted.
        
        Args:
            partition_id: Partition identifier
        
        Returns:
            (is_mounted: bool, mount_point: Optional[str])
        """
        info = DiskUtilBackend.get_partition_info(partition_id)
        if not info:
            return False, None
        
        mount_point = info.get('MountPoint') or None
        return bool(mount_point), mount_point
