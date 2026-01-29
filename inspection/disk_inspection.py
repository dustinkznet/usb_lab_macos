"""
Disk inspection coordinator.
"""

from typing import List, Optional
from ..core import PhysicalDisk, Partition, FilesystemType, DiskType
from ..backend import MacDiskUtilBackend  
from ..detection import ContentDetector

class DiskInspector:
    """
    Main disk inspection coordinator.
    
    This class orchestrates the inspection of USB drives, combining
    diskutil backend with content detection to classify disks.
    """
    
    def __init__(self):
        self.backend = DiskUtilBackend()
        self.detector = ContentDetector()
    
    def enumerate_external_disks(self) -> List[PhysicalDisk]:
        """
        Enumerate all external physical disks.
        
        Returns:
            List of PhysicalDisk objects representing external drives
        """
        all_disk_ids = self.backend.list_all_disks()
        external_disks = []
        
        for disk_id in all_disk_ids:
            disk = self._inspect_physical_disk(disk_id)
            if disk and disk.is_external:
                external_disks.append(disk)
        
        return external_disks
    
    def _inspect_physical_disk(self, disk_id: str) -> Optional[PhysicalDisk]:
        """
        Inspect a physical disk and build PhysicalDisk object.
        
        Args:
            disk_id: Disk identifier (e.g., 'disk2')
        
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
            partition = self._inspect_partition(part_id)
            if partition:
                disk.partitions.append(partition)
        
        # Classify disk based on partitions
        self._classify_disk(disk)
        
        return disk
    
    def _inspect_partition(self, partition_id: str) -> Optional[Partition]:
        """
        Inspect a partition and build Partition object.
        
        Args:
            partition_id: Partition identifier (e.g., 'disk2s1')
        
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
        
        # Detect content if mounted
        if partition.mount_point:
            disk_type, markers = self.detector.detect_content_type(partition.mount_point)
            partition.contains_installer_markers = len(markers) > 0
            partition.installer_type = disk_type if disk_type != DiskType.DATA_DISK else None
            partition.detected_markers = markers
        else:
            # Try limited unmounted detection
            disk_type, notes = self.detector.inspect_unmounted_partition(partition_id)
            if disk_type != DiskType.UNKNOWN:
                partition.installer_type = disk_type
                partition.detected_markers = notes
        
        return partition
    
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
            disk.disk_type = installer_types[0]
            disk.classification_confidence = "High"
            disk.classification_notes.append(
                f"Detected {len(installer_partitions)} installer partition(s)"
            )
            
            # Add marker details
            for part in installer_partitions:
                if part.detected_markers:
                    markers_str = ", ".join(part.detected_markers[:3])
                    disk.classification_notes.append(
                        f"  {part.identifier}: {markers_str}"
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
            else:
                disk.disk_type = DiskType.DATA_DISK
                disk.classification_confidence = "Medium"
                disk.classification_notes.append("No installer markers detected")


# ============================================================================
# DRIVE TESTING ENGINE
# ============================================================================

@dataclass
class TestResult:
