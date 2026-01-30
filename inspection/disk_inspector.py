"""
Disk inspection coordinator with two-phase inspection.
"""

from typing import List, Optional, Tuple
from core.models import PhysicalDisk, Partition
from core.enums import FilesystemType, DiskType, InspectionMode
from backend.macos_diskutil import DiskUtilBackend
from detection.content_detector import ContentDetector
from inspection.mount_helper import MountHelper


class DiskInspector:
    """
    Main disk inspection coordinator with two-phase inspection.

    Phase 1: Metadata-only (safe, no mounting)
    - Lists all external drives
    - Shows hardware specs (USB controller, size, etc.)
    - Detects what's possible from partition metadata
    - Shows mount status

    Phase 2: Mounted inspection (user chooses, read-only)
    - Mounts partitions read-only
    - Detects installer markers, UEFI, etc.
    - Unmounts when done
    """

    def __init__(self):
        self.backend = DiskUtilBackend()
        self.detector = ContentDetector()
        self.mount_helper = MountHelper()

    def enumerate_external_disks(self, mode: InspectionMode = InspectionMode.METADATA_ONLY) -> List[PhysicalDisk]:
        """
        Enumerate all external physical disks.

        Args:
            mode: Inspection mode (METADATA_ONLY or MOUNTED_READONLY)

        Returns:
            List of PhysicalDisk objects representing external drives
        """
        all_disk_ids = self.backend.list_all_disks()
        external_disks = []

        for disk_id in all_disk_ids:
            disk = self._inspect_physical_disk(disk_id, mode)
            if disk and disk.is_external:
                external_disks.append(disk)

        return external_disks

    def _inspect_physical_disk(self, disk_id: str, mode: InspectionMode) -> Optional[PhysicalDisk]:
        """
        Inspect a physical disk and build PhysicalDisk object.

        Args:
            disk_id: Disk identifier (e.g., 'disk2')
            mode: Inspection mode

        Returns:
            PhysicalDisk object or None if inspection failed
        """
        info = self.backend.get_disk_info(disk_id)
        if not info:
            return None

        # Extract basic disk information
        disk = PhysicalDisk(
            identifier=disk_id,
            name=info.get('MediaName', 'Unknown'),
            size_bytes=info.get('TotalSize', 0),
            bus_protocol=info.get('BusProtocol', 'Unknown'),
            device_location=info.get('DeviceLocation', 'Unknown'),
            removable=info.get('Removable', False),
            partition_scheme=info.get('Content', 'Unknown')
        )

        # Inspect partitions
        partition_ids = self.backend.list_partitions(disk_id)
        for part_id in partition_ids:
            partition = self._inspect_partition(part_id, mode)
            if partition:
                disk.partitions.append(partition)

        # Classify disk based on partitions
        self._classify_disk(disk)

        return disk

    def _inspect_partition(self, partition_id: str, mode: InspectionMode) -> Optional[Partition]:
        """
        Inspect a partition and build Partition object.

        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')
            mode: Inspection mode

        Returns:
            Partition object or None if inspection failed
        """
        info = self.backend.get_partition_info(partition_id)
        if not info:
            return None

        # Map filesystem type
        fs_type_str = info.get('FilesystemType', 'Unknown')
        fs_type = self._map_filesystem_type(fs_type_str)

        partition = Partition(
            identifier=partition_id,
            name=info.get('VolumeName', 'Untitled'),
            size_bytes=info.get('TotalSize', 0),
            filesystem=fs_type,
            mount_point=info.get('MountPoint'),
            volume_name=info.get('VolumeName'),
            is_mounted=info.get('MountPoint') is not None
        )

        # Detect content based on mode
        if mode == InspectionMode.METADATA_ONLY:
            # Phase 1: Metadata-only detection (no mounting required)
            disk_type, notes = self.detector.inspect_unmounted_partition(partition_id)
            if disk_type != DiskType.UNKNOWN:
                partition.installer_type = disk_type
                partition.detected_markers = notes

        elif mode == InspectionMode.MOUNTED_READONLY:
            # Phase 2: Mounted detection (requires mounting)
            if partition.mount_point:
                # Already mounted - inspect it
                disk_type, markers = self.detector.detect_content_type(partition.mount_point)
                partition.contains_installer_markers = len(markers) > 0
                partition.installer_type = disk_type if disk_type != DiskType.DATA_DISK else None
                partition.detected_markers = markers
            else:
                # Not mounted - could mount read-only if needed
                # This would be triggered by user choice in CLI
                pass

        return partition

    def deep_inspect_partition(self, partition_id: str) -> Tuple[Optional[Partition], bool, str]:
        """
        Perform deep inspection on a single partition.
        Mounts read-only if needed, inspects, then unmounts.

        Args:
            partition_id: Partition identifier

        Returns:
            (partition: Optional[Partition], mounted_by_us: bool, message: str)
        """
        # Check current mount status
        was_already_mounted, existing_mount = self.mount_helper.is_mounted(partition_id)
        mounted_by_us = False

        try:
            # Get partition info first
            partition = self._inspect_partition(partition_id, InspectionMode.METADATA_ONLY)
            if not partition:
                return None, False, f"Failed to get partition info for {partition_id}"

            # If not mounted, mount it read-only
            mount_point = existing_mount
            if not was_already_mounted:
                success, mount_point, msg = self.mount_helper.mount_readonly(partition_id)
                if not success:
                    return partition, False, f"Failed to mount: {msg}"
                mounted_by_us = True
                partition.mount_point = mount_point
                partition.is_mounted = True

            # Perform deep content detection
            disk_type, markers = self.detector.detect_content_type(mount_point)
            partition.contains_installer_markers = len(markers) > 0
            partition.installer_type = disk_type if disk_type != DiskType.DATA_DISK else None
            partition.detected_markers = markers

            return partition, mounted_by_us, "Deep inspection complete"

        except Exception as e:
            return partition if 'partition' in locals() else None, mounted_by_us, f"Error during inspection: {e}"

    def cleanup_deep_inspect(self, partition_id: str, mount_point: Optional[str] = None):
        """
        Clean up after deep inspection (unmount if we mounted it).

        Args:
            partition_id: Partition identifier
            mount_point: Mount point to clean up
        """
        self.mount_helper.unmount(partition_id, mount_point)

    def _map_filesystem_type(self, fs_str: str) -> FilesystemType:
        """Map diskutil filesystem string to FilesystemType enum"""
        fs_upper = fs_str.upper()

        if 'APFS' in fs_upper:
            return FilesystemType.APFS
        elif 'JHFS+' in fs_upper or 'JOURNALED HFS+' in fs_upper:
            return FilesystemType.JHFS_PLUS
        elif 'HFS+' in fs_upper:
            return FilesystemType.HFS_PLUS
        elif 'EXFAT' in fs_upper:
            return FilesystemType.EXFAT
        elif 'FAT32' in fs_upper or 'MSDOS' in fs_upper:
            return FilesystemType.FAT32
        elif 'NTFS' in fs_upper:
            return FilesystemType.NTFS
        elif 'EXT4' in fs_upper:
            return FilesystemType.EXT4
        elif 'ISO' in fs_upper:
            return FilesystemType.ISO9660
        elif 'UDF' in fs_upper:
            return FilesystemType.UDF
        elif 'FREE' in fs_upper:
            return FilesystemType.FREE_SPACE
        else:
            return FilesystemType.UNKNOWN

    def _classify_disk(self, disk: PhysicalDisk):
        """
        Classify disk type based on partition analysis.

        This method updates disk.disk_type, disk.classification_confidence,
        and disk.classification_notes in-place.
        """
        if not disk.partitions:
            disk.disk_type = DiskType.EMPTY
            disk.classification_confidence = "High"
            disk.classification_notes.append("No partitions found")
            return

        # Check if any partition contains installer markers
        installer_partitions = [p for p in disk.partitions if p.installer_type]

        if installer_partitions:
            # Use the most specific installer type found
            installer_types = [p.installer_type for p in installer_partitions]

            # Prioritize non-UEFI types (UEFI is usually just the boot partition)
            non_uefi_types = [t for t in installer_types if t != DiskType.UEFI_PARTITION]
            if non_uefi_types:
                disk.disk_type = non_uefi_types[0]
            else:
                disk.disk_type = installer_types[0]

            disk.classification_confidence = "High"
            disk.classification_notes.append(
                f"Detected {len(installer_partitions)} installer partition(s)"
            )

            # Add marker details (but limit to avoid logging file contents)
            for part in installer_partitions:
                if part.detected_markers:
                    # Show count of markers, not full list
                    disk.classification_notes.append(
                        f"  {part.identifier}: {part.installer_type.value} ({len(part.detected_markers)} markers)"
                    )
        else:
            # Check for unmounted or inaccessible partitions
            unmounted = [p for p in disk.partitions if not p.is_mounted]

            if unmounted:
                disk.disk_type = DiskType.UNKNOWN
                disk.classification_confidence = "Low"
                disk.classification_notes.append(
                    f"{len(unmounted)} partition(s) not mounted - limited inspection"
                )
                disk.classification_notes.append(
                    "Suggestion: Mount read-only for detailed detection"
                )
            else:
                disk.disk_type = DiskType.DATA_DISK
                disk.classification_confidence = "Medium"
                disk.classification_notes.append("No installer markers detected")