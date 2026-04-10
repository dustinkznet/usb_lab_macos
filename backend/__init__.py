"""
Platform-specific disk backends for USB LAB.
"""

from .macos_diskutil import DiskUtilBackend

__all__ = ['DiskUtilBackend']
