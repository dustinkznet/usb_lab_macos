"""
Disk inspection coordinator with two-phase inspection.
Updated with SMART_AUTO mode and database logging.
FIXED: Improved NTFS filesystem detection.
FIXED: Extract and use serial numbers for unique drive identification.
"""

from typing import List, Optional, Tuple
from core.models import PhysicalDisk, Partition
from core.enums import FilesystemType, DiskType, InspectionMode
from backend.macos_diskutil import DiskUtilBackend
from detection.content_detector import ContentDetector
from inspection.mount_helper import MountHelper
from database.db_manager import DatabaseManager


class DiskInspector:
    """
    Main disk inspection coordinator with two-phase inspection.

    Phase 1: Metadata-only (safe, no mounting)
    Phase 2: Mounted inspection (read-only filesystem scan)
    SMART_AUTO: Automatically choose based on mount status
    """

    def __init__(self, db: Optional[DatabaseManager] = None, settings=None):
        self.backend = DiskUtilBackend()
        self.detector = ContentDetector()
        self.mount_helper = MountHelper()
        self.db = db
        self.settings = settings

    def enumerate_external_disks(self, mode: InspectionMode = None) -> List[PhysicalDisk]:
        """
        Enumerate all external physical disks.

        Args:
            mode: Inspection mode (defaults to setting or SMART_AUTO)

        Returns:
            List of PhysicalDisk objects representing external drives
        """
        if mode is None:
            if self.settings:
                mode_str = self.settings.get('default_inspection_mode', 'smart_auto')
                mode = InspectionMode.SMART_AUTO
                if mode_str == 'metadata_only':
                    mode = InspectionMode.METADATA_ONLY
                elif mode_str == 'mounted_readonly':
                    mode = InspectionMode.MOUNTED_READONLY
            else:
                mode = InspectionMode.SMART_AUTO

        all_disk_ids = self.backend.list_all_disks()
        external_disks = []

        for disk_id in all_disk_ids:
            disk = self._inspect_physical_disk(disk_id, mode)
            if disk and disk.is_external:
                if self.db and (not self.settings or self.settings.get('auto_log_inspections', True)):
                    drive_id = self.db.register_drive(disk, disk.serial_number)
                    self.db.log_inspection(drive_id, disk)

                external_disks.append(disk)

        return external_disks

    def _inspect_physical_disk(self, disk_id: str, mode: InspectionMode) -> Optional[PhysicalDisk]:
        """
        Inspect a physical disk and build PhysicalDisk object.

        Args:
            disk_id: Disk identifier (e.g., 'disk2')
            mode: Inspection mode

        Returns:
            PhysicalDisk object, or None if inspection failed
        """
        info = self.backend.get_disk_info(disk_id)
        if not info:
            return None

        disk = PhysicalDisk(
            identifier=disk_id,
            name=info.get('MediaName', 'Unknown'),
            size_bytes=info.get('TotalSize', 0),
            bus_protocol=info.get('BusProtocol', 'Unknown'),
            device_location=info.get('DeviceLocation', 'Unknown'),
            removable=info.get('Removable', False),
            partition_scheme=info.get('Content', 'Unknown')
        )

        # Extract serial number - prefer device serial, fall back to Volume UUID
        serial = info.get('SerialNumber')
        if not serial or serial == disk_id:
            partition_ids_for_serial = self.backend.list_partitions(disk_id)
            if partition_ids_for_serial:
                first_part_info = self.backend.get_partition_info(partition_ids_for_serial[0])
                if first_part_info:
                    serial = first_part_info.get('VolumeUUID') or disk_id
        disk.serial_number = serial or disk_id

        # Inspect partitions
        partition_ids = self.backend.list_partitions(disk_id)
        for part_id in partition_ids:
            partition = self._inspect_partition(part_id, mode)
            if partition:
                disk.partitions.append(partition)

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

        fs_type_str = info.get('FilesystemType', 'Unknown')
        content_str = info.get('Content', 'Unknown')
        fs_type = self._map_filesystem_type(fs_type_str, content_str)

        mount_point = info.get('MountPoint', '')
        is_mounted = info.get('Mounted', False)

        if mount_point and mount_point.startswith('/dev/'):
            mount_point = None
            is_mounted = False
        elif not mount_point or mount_point == '':
            is_mounted = False

        partition = Partition(
            identifier=partition_id,
            name=info.get('VolumeName', 'Untitled'),
            size_bytes=info.get('TotalSize', 0),
            filesystem=fs_type,
            mount_point=mount_point,
            volume_name=info.get('VolumeName'),
            is_mounted=is_mounted
        )

        if mode == InspectionMode.SMART_AUTO:
            effective_mode = InspectionMode.MOUNTED_READONLY if partition.is_mounted else InspectionMode.METADATA_ONLY
        else:
            effective_mode = mode

        if effective_mode == InspectionMode.METADATA_ONLY:
            disk_type, notes = self.detector.inspect_unmounted_partition(partition_id)
            if disk_type != DiskType.UNKNOWN:
                partition.installer_type = disk_type
                partition.detected_markers = notes

        elif effective_mode == InspectionMode.MOUNTED_READONLY:
            if partition.mount_point:
                disk_type, markers = self.detector.detect_content_type(partition.mount_point)
                partition.contains_installer_markers = len(markers) > 0
                partition.installer_type = disk_type if disk_type != DiskType.DATA_DISK else None
                partition.detected_markers = markers

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
        was_already_mounted, existing_mount = self.mount_helper.is_mounted(partition_id)
        mounted_by_us = False

        try:
            partition = self._inspect_partition(partition_id, InspectionMode.METADATA_ONLY)
            if not partition:
                return None, False, f"Failed to get partition info for {partition_id}"

            mount_point = existing_mount
            if not was_already_mounted:
                success, mount_point, msg = self.mount_helper.mount_readonly(partition_id)
                if not success:
                    return partition, False, f"Failed to mount: {msg}"
                mounted_by_us = True
                partition.mount_point = mount_point
                partition.is_mounted = True

            disk_type, markers = self.detector.detect_content_type(mount_point)
            partition.contains_installer_markers = len(markers) > 0
            partition.installer_type = disk_type if disk_type != DiskType.DATA_DISK else None
            partition.detected_markers = markers

            return partition, mounted_by_us, "Deep inspection complete"

        except Exception as e:
            return partition if 'partition' in locals() else None, mounted_by_us, f"Error during inspection: {e}"

    def cleanup_deep_inspect(self, partition_id: str, mount_point: Optional[str] = None):
        """Clean up after deep inspection (unmount if we mounted it)."""
        self.mount_helper.unmount(partition_id, mount_point)

    def _map_filesystem_type(self, fs_str: str, content_str: str = '') -> FilesystemType:
        """Map diskutil filesystem string to FilesystemType enum."""
        fs_upper = fs_str.upper()
        content_upper = content_str.upper()
        combined = f"{fs_upper} {content_upper}"

        if 'NTFS' in combined or 'WINDOWS_NTFS' in fs_upper:
            return FilesystemType.NTFS
        if 'APFS' in combined:
            return FilesystemType.APFS
        # ExFAT before FAT32 (ExFAT contains 'FAT')
        if 'EXFAT' in fs_upper or 'EXFAT' in content_upper:
            return FilesystemType.EXFAT
        if 'JHFS+' in combined or 'JOURNALED HFS+' in combined or 'JOURNAL' in combined:
            return FilesystemType.JHFS_PLUS
        if 'HFS+' in combined or 'HFS PLUS' in combined:
            return FilesystemType.HFS_PLUS
        if fs_upper == 'HFS' or 'APPLE_HFS' in content_upper:
            return FilesystemType.HFS_PLUS
        if 'FAT32' in combined or 'MSDOS' in combined or 'FAT' in combined:
            return FilesystemType.FAT32
        if 'EXT4' in combined or 'EXT3' in combined or 'EXT2' in combined:
            return FilesystemType.EXT4
        if 'ISO' in combined or '9660' in combined:
            return FilesystemType.ISO9660
        if 'UDF' in combined:
            return FilesystemType.UDF
        if 'FREE' in combined or 'UNFORMATTED' in combined:
            return FilesystemType.FREE_SPACE

        return FilesystemType.UNKNOWN

    def _classify_disk(self, disk: PhysicalDisk):
        """Classify disk type based on partition analysis."""
        if not disk.partitions:
            disk.disk_type = DiskType.EMPTY
            disk.classification_confidence = "High"
            disk.classification_notes.append("No partitions found")
            return

        # Check if any partition contains installer markers
        # Exclude EFI partitions - they're standard infrastructure on any bootable drive,
        # not a signal that the disk is installer media.
        installer_partitions = [
            p for p in disk.partitions
            if p.installer_type and p.installer_type != DiskType.UEFI_PARTITION
        ]

        if installer_partitions:
            installer_types = [p.installer_type for p in installer_partitions]
            disk.disk_type = installer_types[0]

            disk.classification_confidence = "High"
            disk.classification_notes.append(f"Detected {len(installer_partitions)} installer partition(s)")

            for part in installer_partitions:
                if part.detected_markers:
                    disk.classification_notes.append(
                        f"  {part.identifier}: {part.installer_type.value} ({len(part.detected_markers)} markers)"
                    )
        else:
            unmounted = [p for p in disk.partitions if not p.is_mounted]

            if unmounted:
                disk.disk_type = DiskType.UNKNOWN
                disk.classification_confidence = "Low"
                disk.classification_notes.append(f"{len(unmounted)} partition(s) not mounted - limited inspection")
                disk.classification_notes.append("Mount partitions for full detection")
            else:
                disk.disk_type = DiskType.DATA_DISK
                disk.classification_confidence = "High"
                disk.classification_notes.append(
                    f"All {len(disk.partitions)} partition(s) inspected - appears to be data storage"
                )