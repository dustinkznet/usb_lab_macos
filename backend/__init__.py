"""
Platform-specific disk backends for USB LAB.
"""

from .base import DiskBackend
from .macos_diskutil import MacDiskUtilBackend

__all__ = ['DiskBackend', 'MacDiskUtilBackend']
