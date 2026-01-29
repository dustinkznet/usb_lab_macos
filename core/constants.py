"""
Constants and configuration values for USB LAB.
"""

# Database configuration
DB_DIR_NAME = ".usb_lab"
DB_FILE_NAME = "usb_lab.db"

# Testing configuration
TEST_DIR_NAME = ".usb_lab_test"
DEFAULT_SEQUENTIAL_SIZE_MB = 100
DEFAULT_RANDOM_OPS = 1000
BLOCK_SIZE_4K = 4096
BLOCK_SIZE_1MB = 1024 * 1024

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

