"""
Reporting utilities for displaying disk inspection results.
"""

from ..core import PhysicalDisk, Partition, DiskType
from .colors import Color
from .display import print_info


class DiskReporter:
    """Generate human-readable reports of disk inspection results"""
    
    @staticmethod
    def display_disk_summary(disk: PhysicalDisk):
        """Display comprehensive summary of a single disk"""
        
        # Disk header
        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_YELLOW}DISK: {disk.identifier} - {disk.name}{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        
        # Basic information
        print(f"\n{Color.BRIGHT_WHITE}Physical Disk Information:{Color.RESET}")
        print_info("Size", disk.size_human, indent=1)
        print_info("Bus Protocol", disk.bus_protocol, indent=1)
        print_info("Device Location", disk.device_location, indent=1)
        print_info("Partition Scheme", disk.partition_scheme, indent=1)
        print_info("Removable Flag", str(disk.removable), indent=1)
        
        # Classification
        print(f"\n{Color.BRIGHT_WHITE}Classification:{Color.RESET}")
        
        # Color-code disk type
        type_color = Color.BRIGHT_GREEN
        if disk.disk_type == DiskType.UNKNOWN:
            type_color = Color.BRIGHT_YELLOW
        elif disk.disk_type == DiskType.EMPTY:
            type_color = Color.BRIGHT_MAGENTA
        elif disk.disk_type == DiskType.CORRUPTED:
            type_color = Color.BRIGHT_RED
        
        print_info("Type", f"{type_color}{disk.disk_type.value}{Color.RESET}", indent=1)
        print_info("Confidence", disk.classification_confidence, indent=1)
        
        if disk.classification_notes:
            print(f"  {Color.CYAN}Notes:{Color.RESET}")
            for note in disk.classification_notes:
                print(f"    {Color.WHITE}• {note}{Color.RESET}")
        
        # Partitions
        if disk.partitions:
            print(f"\n{Color.BRIGHT_WHITE}Partitions ({len(disk.partitions)}):{Color.RESET}")
            
            for i, part in enumerate(disk.partitions, 1):
                DiskReporter.display_partition_summary(part, i)
        else:
            print(f"\n{Color.BRIGHT_MAGENTA}No partitions found{Color.RESET}")
    
    @staticmethod
    def display_partition_summary(partition: Partition, index: int):
        """Display summary of a single partition"""
        
        # Partition header
        mount_status = f"{Color.BRIGHT_GREEN}MOUNTED{Color.RESET}" if partition.is_mounted else f"{Color.BRIGHT_RED}NOT MOUNTED{Color.RESET}"
        print(f"\n  {Color.BRIGHT_CYAN}[{index}] {partition.identifier}{Color.RESET} - {mount_status}")
        
        # Basic info
        print_info("Name", partition.volume_name or "Untitled", indent=2)
        print_info("Size", partition.size_human, indent=2)
        print_info("Filesystem", partition.filesystem.value, indent=2)
        
        if partition.mount_point:
            print_info("Mount Point", partition.mount_point, indent=2)
        
        # Content detection results
        if partition.contains_installer_markers:
            print(f"    {Color.BRIGHT_YELLOW}⚡ Installer Media Detected{Color.RESET}")
            if partition.installer_type:
                print_info("Installer Type", partition.installer_type.value, indent=3)
            
            if partition.detected_markers:
                print(f"      {Color.CYAN}Detected Markers:{Color.RESET}")
                for marker in partition.detected_markers[:5]:  # Limit to 5
                    print(f"        {Color.WHITE}• {marker}{Color.RESET}")
        elif not partition.is_mounted:
            print(f"    {Color.YELLOW}⚠ Not mounted - content inspection limited{Color.RESET}")
