"""
USB hardware logging for device characterization.

This module logs technical specifications of USB drives for evaluation purposes.
It does NOT log file contents or directory listings.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from core.models import PhysicalDisk, Partition
from core.enums import DiskType, FilesystemType


class USBLogger:
    """
    Logger for USB drive hardware specifications.
    
    Captures technical details for device evaluation:
    - USB controller specs (2.0, 3.0, 3.1, etc.)
    - Physical characteristics
    - Partition layouts
    - Filesystem metadata
    - Detection results
    
    Does NOT log:
    - File contents
    - Directory listings
    - User data
    """
    
    def __init__(self, log_dir: str = ".usb_lab/logs"):
        """
        Initialize logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_disk_inspection(self, disk: PhysicalDisk, inspection_mode: str) -> str:
        """
        Log a disk inspection event.
        
        Args:
            disk: PhysicalDisk object with inspection results
            inspection_mode: "metadata_only" or "mounted_readonly"
        
        Returns:
            Path to created log file
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "inspection_mode": inspection_mode,
            "hardware": self._extract_hardware_info(disk),
            "partitions": self._extract_partition_info(disk.partitions),
            "classification": self._extract_classification_info(disk),
        }
        
        # Create log filename based on disk identifier and timestamp
        log_filename = f"{disk.identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path = self.log_dir / log_filename
        
        # Write log file
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        return str(log_path)
    
    def _extract_hardware_info(self, disk: PhysicalDisk) -> Dict:
        """Extract hardware specifications (USB controller, bus, etc.)"""
        return {
            "identifier": disk.identifier,
            "device_name": disk.name,
            "size_bytes": disk.size_bytes,
            "size_human": disk.size_human,
            "bus_protocol": disk.bus_protocol,
            "device_location": disk.device_location,
            "removable_flag": disk.removable,
            "is_external": disk.is_external,
            "partition_scheme": disk.partition_scheme,
            "usb_speed": self._classify_usb_speed(disk.bus_protocol),
        }
    
    def _classify_usb_speed(self, bus_protocol: str) -> str:
        """Classify USB speed from bus protocol string"""
        protocol_upper = bus_protocol.upper()
        
        if 'USB 3.2' in protocol_upper or 'USB 3.1 GEN 2' in protocol_upper:
            return "USB 3.2 Gen 2 (10 Gbps)"
        elif 'USB 3.1' in protocol_upper or 'USB 3.0' in protocol_upper:
            return "USB 3.1 Gen 1 / 3.0 (5 Gbps)"
        elif 'USB 2.0' in protocol_upper:
            return "USB 2.0 (480 Mbps)"
        elif 'USB 1.1' in protocol_upper:
            return "USB 1.1 (12 Mbps)"
        else:
            return f"Unknown ({bus_protocol})"
    
    def _extract_partition_info(self, partitions: List[Partition]) -> List[Dict]:
        """Extract partition metadata (NO file contents)"""
        partition_data = []
        
        for partition in partitions:
            partition_data.append({
                "identifier": partition.identifier,
                "name": partition.name,
                "size_bytes": partition.size_bytes,
                "size_human": partition.size_human,
                "filesystem": partition.filesystem.value,
                "volume_name": partition.volume_name,
                "is_mounted": partition.is_mounted,
                "mount_point": partition.mount_point,
                "installer_type": partition.installer_type.value if partition.installer_type else None,
                "contains_installer_markers": partition.contains_installer_markers,
                "marker_count": len(partition.detected_markers),
                # Note: We log marker COUNT, not the actual markers (which could include filenames)
            })
        
        return partition_data
    
    def _extract_classification_info(self, disk: PhysicalDisk) -> Dict:
        """Extract classification results"""
        return {
            "disk_type": disk.disk_type.value,
            "confidence": disk.classification_confidence,
            "notes": disk.classification_notes,
        }
    
    def create_summary_report(self) -> Dict:
        """
        Create a summary report of all logged USB drives.
        
        Returns:
            Dictionary with statistics and common configurations
        """
        log_files = list(self.log_dir.glob("*.json"))
        
        if not log_files:
            return {"total_drives": 0, "message": "No drives logged yet"}
        
        # Aggregate statistics
        usb_speeds = {}
        filesystems = {}
        disk_types = {}
        sizes = []
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                data = json.load(f)
            
            # USB speed distribution
            usb_speed = data["hardware"]["usb_speed"]
            usb_speeds[usb_speed] = usb_speeds.get(usb_speed, 0) + 1
            
            # Filesystem distribution
            for partition in data["partitions"]:
                fs = partition["filesystem"]
                filesystems[fs] = filesystems.get(fs, 0) + 1
            
            # Disk type distribution
            disk_type = data["classification"]["disk_type"]
            disk_types[disk_type] = disk_types.get(disk_type, 0) + 1
            
            # Size tracking
            sizes.append(data["hardware"]["size_bytes"])
        
        return {
            "total_drives": len(log_files),
            "usb_speed_distribution": usb_speeds,
            "filesystem_distribution": filesystems,
            "disk_type_distribution": disk_types,
            "average_size_gb": sum(sizes) / len(sizes) / (1024**3) if sizes else 0,
            "largest_drive_gb": max(sizes) / (1024**3) if sizes else 0,
            "smallest_drive_gb": min(sizes) / (1024**3) if sizes else 0,
        }
