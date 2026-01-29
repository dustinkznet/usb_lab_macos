"""
Abstract backend interface for disk operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class DiskBackend(ABC):
    """Abstract base class for platform-specific disk backends"""
    
    @abstractmethod
    def run_command(self, cmd: List[str]) -> tuple[bool, str, str]:
        """Execute a command safely and return success, stdout, stderr"""
        pass
    
    @abstractmethod
    def list_all_disks(self) -> List[str]:
        """List all disk identifiers"""
        pass
    
    @abstractmethod
    def get_disk_info(self, disk_id: str) -> Optional[Dict]:
        """Get detailed information about a disk"""
        pass
    
    @abstractmethod
    def get_partition_info(self, partition_id: str) -> Optional[Dict]:
        """Get detailed information about a partition"""
        pass
    
    @abstractmethod
    def list_partitions(self, disk_id: str) -> List[str]:
        """List all partitions for a given disk"""
        pass
