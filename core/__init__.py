"""
Core data structures and enumerations for USB LAB.
"""

from .enums import DiskType, TestType, FilesystemType
from .models import Partition, PhysicalDisk, TestResult
from .constants import *

__all__ = [
    'DiskType',
    'TestType', 
    'FilesystemType',
    'Partition',
    'PhysicalDisk',
    'TestResult',
]
