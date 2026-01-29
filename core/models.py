"""
Data models for USB LAB.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .enums import FilesystemType, DiskType, TestType


@dataclass
class Partition:
    """Represents a single partition on a disk"""
    identifier: str  # e.g., disk2s1
    name: str
    size_bytes: int
    filesystem: FilesystemType
    mount_point: Optional[str] = None
    volume_name: Optional[str] = None
    is_mounted: bool = False
    
    # Content detection
    contains_installer_markers: bool = False
    installer_type: Optional[DiskType] = None
    detected_markers: List[str] = field(default_factory=list)
    
    @property
    def size_human(self) -> str:
        """Human-readable size"""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


@dataclass
class PhysicalDisk:
    """Represents a physical USB disk"""
    identifier: str  # e.g., disk2
    name: str
    size_bytes: int
    bus_protocol: str
    device_location: str
    removable: bool  # Note: unreliable metadata
    
    partitions: List[Partition] = field(default_factory=list)
    partition_scheme: Optional[str] = None
    disk_type: DiskType = DiskType.UNKNOWN
    
    # Classification metadata
    classification_confidence: str = "Unknown"  # Low/Medium/High
    classification_notes: List[str] = field(default_factory=list)
    
    @property
    def size_human(self) -> str:
        """Human-readable size"""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    @property
    def is_external(self) -> bool:
        """
        Determine if disk is external based on multiple signals.
        Don't trust 'Removable' flag alone.
        """
        external_indicators = [
            'USB' in self.bus_protocol.upper(),
            'EXTERNAL' in self.device_location.upper(),
            self.removable,
        ]
        return any(external_indicators)


@dataclass
class TestResult:
    """Results from a single test run"""
    test_type: TestType
    success: bool
    duration_seconds: float
    speed_mbps: Optional[float] = None
    iops: Optional[float] = None
    bytes_transferred: int = 0
    error_message: Optional[str] = None
    notes: List[str] = field(default_factory=list)
