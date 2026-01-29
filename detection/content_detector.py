"""
Content detection for identifying installer media and disk types.
"""

import os
from typing import Tuple, List
from ..core import DiskType
from ..core.constants import MACOS_LEGACY_MARKERS, MACOS_MODERN_MARKERS, LINUX_MARKERS, WINDOWS_MARKERS

class ContentDetector:
    """
    Detect disk content types by inspecting filesystem markers.
    
    This class implements read-only inspection of mount points to identify
    installer media, boot disks, and other special-purpose content.
    """
    
    # macOS installer markers (legacy HFS+ based)
    MACOS_LEGACY_MARKERS = [
        '.IABootFiles',
        '.IAProductInfo',
        'System/Library/CoreServices/boot.efi',
        'BaseSystem.dmg',
        'mach_kernel',
    ]
    
    # macOS installer markers (modern APFS/USB based)
    MACOS_MODERN_MARKERS = [
        'Install macOS',  # Folder prefix
        '.IAPhysicalMedia',
        'com_apple_MobileAsset_MacSoftwareUpdate',
    ]
    
    # Linux installer markers
    LINUX_MARKERS = [
        'casper',  # Ubuntu
        'isolinux',
        'syslinux',
        'EFI/BOOT/grubx64.efi',
        '.disk/info',
    ]
    
    # Windows installer markers
    WINDOWS_MARKERS = [
        'sources/install.wim',
        'sources/install.esd',
        'bootmgr',
        'setup.exe',
    ]
    
    @classmethod
    def detect_content_type(cls, mount_point: str) -> Tuple[DiskType, List[str]]:
        """
        Detect content type by inspecting filesystem.
        
        Args:
            mount_point: Path to mounted volume
        
        Returns:
            (DiskType, list of detected markers)
        """
        if not mount_point or not os.path.exists(mount_point):
            return DiskType.UNKNOWN, []
        
        detected_markers = []
        
        # Check for macOS legacy installer
        for marker in cls.MACOS_LEGACY_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            if os.path.exists(marker_path):
                detected_markers.append(marker)
        
        if detected_markers:
            return DiskType.MACOS_INSTALLER_LEGACY, detected_markers
        
        # Check for macOS modern installer
        for marker in cls.MACOS_MODERN_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            # Handle prefix matching for "Install macOS"
            if marker.startswith('Install macOS'):
                try:
                    items = os.listdir(mount_point)
                    if any(item.startswith('Install macOS') for item in items):
                        detected_markers.append(marker)
                except PermissionError:
                    pass
            elif os.path.exists(marker_path):
                detected_markers.append(marker)
        
        if detected_markers:
            return DiskType.MACOS_INSTALLER_MODERN, detected_markers
        
        # Check for Linux installer
        for marker in cls.LINUX_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            if os.path.exists(marker_path):
                detected_markers.append(marker)
        
        if detected_markers:
            return DiskType.LINUX_INSTALLER, detected_markers
        
        # Check for Windows installer
        for marker in cls.WINDOWS_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            if os.path.exists(marker_path):
                detected_markers.append(marker)
        
        if detected_markers:
            return DiskType.WINDOWS_INSTALLER, detected_markers
        
        # Check if volume appears empty but has hidden files
        try:
            all_files = os.listdir(mount_point)
            visible_files = [f for f in all_files if not f.startswith('.')]
            hidden_files = [f for f in all_files if f.startswith('.')]
            
            if not visible_files and hidden_files:
                detected_markers.extend(hidden_files[:5])  # Sample of hidden files
                return DiskType.DATA_DISK, detected_markers
        except PermissionError:
            pass
        
        return DiskType.DATA_DISK, []
    
    @classmethod
    def inspect_unmounted_partition(cls, partition_id: str) -> Tuple[DiskType, List[str]]:
        """
        Attempt to detect content type for unmounted partition.
        
        This is more limited than mounted inspection but can still
        detect some patterns from filesystem metadata.
        
        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')
        
        Returns:
            (DiskType, list of notes/findings)
        """
        notes = []
        
        # Get partition info
        info = DiskUtilBackend.get_partition_info(partition_id)
        if not info:
            return DiskType.UNKNOWN, ["Could not read partition metadata"]
        
        # Check filesystem type
        fs_type = info.get('FilesystemType', '')
        volume_name = info.get('VolumeName', '')
        
        # HFS+ with certain names often indicates installer
        if 'HFS' in fs_type:
            if any(name in volume_name for name in ['Install', 'Recovery', 'BaseSystem']):
                notes.append(f"Volume name suggests installer: {volume_name}")
                return DiskType.MACOS_INSTALLER_LEGACY, notes
        
        # ISO9660 often indicates installer media
        if 'ISO' in fs_type:
            notes.append(f"ISO9660 filesystem detected")
            return DiskType.LINUX_INSTALLER, notes
        
        notes.append(f"Filesystem: {fs_type}, Name: {volume_name}")
        notes.append("Partition is not mounted - limited inspection available")
        
        return DiskType.UNKNOWN, notes


# ============================================================================
# DISK INSPECTOR - MAIN LOGIC
# ============================================================================

class DiskInspector:
