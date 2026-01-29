"""
Platform-specific disk backends for USB LAB.
"""

from .base import DiskBackend
from .macos_diskutil import DiskUtilBackend

__all__ = ['DiskBackend', 'DiskUtilBackend']
