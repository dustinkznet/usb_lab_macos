"""
Content detection for identifying installer media and disk types.
"""

import os
from typing import Tuple, List
from core.enums import DiskType
from core.constants import (
    MACOS_LEGACY_MARKERS,
    MACOS_MODERN_MARKERS,
    LINUX_MARKERS,
    WINDOWS_MARKERS
)
from backend.macos_diskutil import DiskUtilBackend


# macOS system directories that should be IGNORED (not treated as installer markers)
MACOS_SYSTEM_DIRS = {
    '.Spotlight-V100',
    '.fseventsd',
    '.Trashes',
    '.TemporaryItems',
    '.DocumentRevisions-V100',
    '.PKInstallSandboxManager',
    '.PKInstallSandboxManager-SystemSoftware',
    '.VolumeIcon.icns',
    '.vol',
    '.DS_Store',
    '.metadata_never_index',
    'Network Trash Folder',
    'Temporary Items',
    '$RECYCLE.BIN',
    'System Volume Information',
    '.apdisk',
}


class ContentDetector:
    """
    Detect disk content types by inspecting filesystem markers.

    This class implements read-only inspection of mount points to identify
    installer media, boot disks, and other special-purpose content.
    """

    @classmethod
    def _is_system_directory(cls, item_name: str) -> bool:
        """
        Check if an item is a macOS/system directory that should be ignored.

        Args:
            item_name: Name of file/directory to check

        Returns:
            True if this is a system directory to ignore
        """
        # Exact match against known system directories
        if item_name in MACOS_SYSTEM_DIRS:
            return True

        # Pattern matches
        if item_name.startswith('.') and any([
            'spotlight' in item_name.lower(),
            'fsevent' in item_name.lower(),
            'trash' in item_name.lower(),
            'temporary' in item_name.lower(),
        ]):
            return True

        return False

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
        for marker in MACOS_LEGACY_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            if os.path.exists(marker_path):
                detected_markers.append(marker)

        if detected_markers:
            return DiskType.MACOS_INSTALLER_LEGACY, detected_markers

        # Check for macOS modern installer
        for marker in MACOS_MODERN_MARKERS:
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
        for marker in LINUX_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            if os.path.exists(marker_path):
                detected_markers.append(marker)

        if detected_markers:
            return DiskType.LINUX_INSTALLER, detected_markers

        # Check for Windows installer
        for marker in WINDOWS_MARKERS:
            marker_path = os.path.join(mount_point, marker)
            if os.path.exists(marker_path):
                detected_markers.append(marker)

        if detected_markers:
            return DiskType.WINDOWS_INSTALLER, detected_markers

        # Check for UEFI partition LAST - many installer media (Windows, Linux)
        # also contain EFI dirs, so we only fall back to UEFI_PARTITION if no
        # OS-specific installer markers were found.
        efi_path = os.path.join(mount_point, 'EFI')
        if os.path.exists(efi_path) and os.path.isdir(efi_path):
            try:
                efi_subdirs = os.listdir(efi_path)
                if efi_subdirs:
                    for subdir in efi_subdirs[:3]:
                        detected_markers.append(f"EFI/{subdir}")
                    return DiskType.UEFI_PARTITION, detected_markers
            except PermissionError:
                pass

        # Check if volume appears empty but has hidden files
        # Filter out macOS system directories before determining if it's truly empty
        try:
            all_files = os.listdir(mount_point)
            visible_files = [f for f in all_files if not f.startswith('.')]
            hidden_files = [f for f in all_files if f.startswith('.')]

            # Filter hidden files to exclude system directories
            non_system_hidden_files = [
                f for f in hidden_files
                if not cls._is_system_directory(f)
            ]

            # Only treat as "has hidden files" if there are non-system hidden files
            if not visible_files and non_system_hidden_files:
                detected_markers.extend(non_system_hidden_files[:5])  # Sample of hidden files
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
        partition_type = info.get('PartitionType', '')

        # Check for EFI System Partition (UEFI boot partition)
        # Can be identified by partition type GUID without mounting
        if 'EFI' in partition_type or partition_type == 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B':
            notes.append(f"EFI System Partition detected")
            notes.append(f"Partition Type: {partition_type}")
            return DiskType.UEFI_PARTITION, notes

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