"""
Enumerations for USB LAB classification and testing.
"""

from enum import Enum


class DiskType(Enum):
    """Classification of disk purpose/content"""
    UNKNOWN = "Unknown"
    EMPTY = "Empty/Unformatted"
    DATA_DISK = "Data Storage"
    MACOS_INSTALLER_LEGACY = "macOS Installer (Legacy/HFS+)"
    MACOS_INSTALLER_MODERN = "macOS Installer (Modern/APFS)"
    LINUX_INSTALLER = "Linux Installer"
    WINDOWS_INSTALLER = "Windows Installer"
    UEFI_PARTITION = "UEFI System Partition"
    BOOT_RECOVERY = "Boot/Recovery Media"
    HYBRID_MULTIBOOT = "Hybrid/Multi-boot"
    CORRUPTED = "Corrupted/Damaged"


class TestType(Enum):
    """Types of performance/health tests"""
    # Health & Integrity Tests
    HEALTH_CHECK = "health_check"
    READ_VERIFY = "read_verify"

    # Sequential Performance Tests
    SEQUENTIAL_READ = "sequential_read"
    SEQUENTIAL_WRITE = "sequential_write"

    # Random Performance Tests
    RANDOM_4K_READ = "random_4k_read"
    RANDOM_4K_WRITE = "random_4k_write"
    RANDOM_4K_MIXED = "random_4k_mixed"

    # Sustained Performance Tests
    SUSTAINED_WRITE = "sustained_write"
    THERMAL_THROTTLE = "thermal_throttle"

    # Real-World Workload Tests
    SMALL_FILES_READ = "small_files_read"
    SMALL_FILES_WRITE = "small_files_write"
    LARGE_FILES_COPY = "large_files_copy"
    MIXED_WORKLOAD = "mixed_workload"


class FilesystemType(Enum):
    """Known filesystem types"""
    UNKNOWN = "Unknown"
    APFS = "APFS"
    HFS_PLUS = "HFS+"
    JHFS_PLUS = "Journaled HFS+"
    EXFAT = "exFAT"
    FAT32 = "FAT32"
    NTFS = "NTFS"
    EXT4 = "ext4"
    ISO9660 = "ISO 9660"
    UDF = "UDF"
    FREE_SPACE = "Free Space"


class InspectionMode(Enum):
    """Mode of disk inspection"""
    METADATA_ONLY = "metadata_only"      # Safe, no mounting, limited detection
    MOUNTED_READONLY = "mounted_readonly"  # Detailed, read-only filesystem scan
    SMART_AUTO = "smart_auto"            # Automatically choose based on mount status
    FULL_ACCESS = "full_access"          # For speed tests, read-write