"""
Menu system for USB LAB.
"""

from typing import Optional
from core.models import PhysicalDisk
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector  
from testing.test_engine import DriveTestEngine
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_success, print_warning, print_error
from ui.reporters import DiskReporter

class MenuSystem:
    """
    Interactive menu system for USB LAB.
    
    Provides navigation between different tool functions.
    """
    
    def __init__(self, inspector: 'DiskInspector', db: DatabaseManager):
        self.inspector = inspector
        self.db = db
    
    def display_main_menu(self) -> Optional[str]:
        """
        Display main menu and get user choice.
        
        Returns:
            Menu choice or None to exit
        """
        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}MAIN MENU{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}\n")
        
        menu_items = [
            ("1", "Examine Drives", "Inspect USB drives (read-only)"),
            ("2", "Read/Write Speed Tests", "Benchmark drive performance"),
            ("3", "View Test History", "Review past test results"),
            ("4", "Drive Database", "Manage drive records"),
            ("5", "Settings", "Configure USB LAB"),
            ("Q", "Quit", "Exit USB LAB"),
        ]
        
        for key, title, desc in menu_items:
            print(f"  {Color.BRIGHT_YELLOW}[{key}]{Color.RESET} {Color.BRIGHT_WHITE}{title}{Color.RESET}")
            print(f"      {Color.CYAN}{desc}{Color.RESET}\n")
        
        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select option: {Color.RESET}").strip().upper()
        
        return choice if choice else None
    
    def examine_drives_menu(self):
        """Submenu for drive examination"""
        clear_screen()
        print_header()
        
        print_section("Scanning for External USB Drives", Color.BRIGHT_CYAN)
        
        external_disks = self.inspector.enumerate_external_disks()
        
        if not external_disks:
            print_warning("No external USB drives detected")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
            return
        
        print_success(f"Found {len(external_disks)} external disk(s)\n")
        
        # Display drive list
        print(f"{Color.BRIGHT_WHITE}Available Drives:{Color.RESET}\n")
        for i, disk in enumerate(external_disks, 1):
            print(f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{disk.identifier}{Color.RESET} - {Color.WHITE}{disk.name}{Color.RESET}")
            print(f"      Size: {disk.size_human} | Protocol: {disk.bus_protocol}")
            print()
        
        print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")
        
        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select drive to examine: {Color.RESET}").strip().upper()
        
        if choice == 'B':
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(external_disks):
                self._display_drive_inspection(external_disks[index])
        except ValueError:
            print_error("Invalid selection")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
    
    def _display_drive_inspection(self, disk: 'PhysicalDisk'):
        """Display detailed inspection of a single drive"""
        clear_screen()
        print_header()
        
        # Register drive in database
        drive_id = self.db.register_drive(disk)
        self.db.log_inspection(drive_id, disk)
        
        # Display inspection results
        reporter = DiskReporter()
        reporter.display_disk_summary(disk)
        
        print(f"\n{Color.BRIGHT_GREEN}✓ Inspection logged to database (ID: {drive_id[:8]}...){Color.RESET}")
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to drive menu...{Color.RESET}")
    
    def speed_test_menu(self):
        """Submenu for speed testing"""
        clear_screen()
        print_header()
        
        print_section("Read/Write Speed Testing", Color.BRIGHT_YELLOW)
        
        # Enumerate drives
        external_disks = self.inspector.enumerate_external_disks()
        
        if not external_disks:
            print_warning("No external USB drives detected")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
            return
        
        print_success(f"Found {len(external_disks)} external disk(s)\n")
        
        # Display drives with safety assessment
        print(f"{Color.BRIGHT_WHITE}Available Drives:{Color.RESET}\n")
        testable_disks = []
        
        for i, disk in enumerate(external_disks, 1):
            can_test, reason = DriveTestEngine(self.db).should_test_drive(disk)
            
            status_color = Color.BRIGHT_GREEN if can_test else Color.BRIGHT_RED
            status_icon = "✓" if can_test else "✗"
            
            print(f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{disk.identifier}{Color.RESET} - {Color.WHITE}{disk.name}{Color.RESET}")
            print(f"      Size: {disk.size_human} | Type: {disk.disk_type.value}")
            print(f"      {status_color}{status_icon} {reason}{Color.RESET}")
            print()
            
            if can_test:
                testable_disks.append((i, disk))
        
        if not testable_disks:
            print_error("No drives are safe to test")
            print(f"{Color.YELLOW}Installer/Boot drives are protected from testing.{Color.RESET}")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
            return
        
        print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")
        
        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select drive to test: {Color.RESET}").strip().upper()
        
        if choice == 'B':
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(external_disks):
                selected_disk = external_disks[index]
                
                # Check if this disk is testable
                test_engine = DriveTestEngine(self.db)
                can_test, reason = test_engine.should_test_drive(selected_disk)
                
                if not can_test:
                    print_error(f"Cannot test this drive: {reason}")
                    input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
                    return
                
                # If drive has data, confirm with user
                if "confirmation required" in reason.lower():
                    print_warning(reason)
                    confirm = input(f"\n{Color.BRIGHT_YELLOW}Continue with testing? This will create test files. (yes/no): {Color.RESET}").strip().lower()
                    if confirm != 'yes':
                        print(f"{Color.CYAN}Testing cancelled.{Color.RESET}")
                        input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
                        return
                
                self._run_comprehensive_tests(selected_disk)
        except ValueError:
            print_error("Invalid selection")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
    
    def _run_comprehensive_tests(self, disk: 'PhysicalDisk'):
        """Run comprehensive test suite on a disk"""
        clear_screen()
        print_header()
        
        # Register drive
        drive_id = self.db.register_drive(disk)
        
        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}TESTING: {disk.identifier} - {disk.name}{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        
        # Find first mounted, writable partition
        testable_partition = None
        for part in disk.partitions:
            if part.is_mounted and part.mount_point:
                testable_partition = part
                break
        
        if not testable_partition:
            print_error("No mounted partition found for testing")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            return
        
        print(f"\n{Color.WHITE}Testing partition: {testable_partition.identifier}{Color.RESET}")
        print(f"{Color.WHITE}Filesystem: {testable_partition.filesystem.value}{Color.RESET}")
        print(f"{Color.WHITE}Mount point: {testable_partition.mount_point}{Color.RESET}")
        
        # Run test suite
        test_engine = DriveTestEngine(self.db)
        results = test_engine.run_comprehensive_test_suite(testable_partition, drive_id)
        
        # Display summary
        print(f"\n{Color.BRIGHT_MAGENTA}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}TEST SUMMARY{Color.RESET}")
        print(f"{Color.BRIGHT_MAGENTA}{'═' * 80}{Color.RESET}\n")
        
        for result in results:
            if result.success:
                print(f"{Color.BRIGHT_GREEN}✓{Color.RESET} {result.test_type.value}")
                if result.speed_mbps:
                    print(f"  Speed: {Color.BRIGHT_CYAN}{result.speed_mbps:.2f} MB/s{Color.RESET}")
                if result.iops:
                    print(f"  IOPS: {Color.BRIGHT_CYAN}{result.iops:.1f}{Color.RESET}")
                if result.notes:
                    for note in result.notes:
                        print(f"  {Color.CYAN}{note}{Color.RESET}")
            else:
                print(f"{Color.BRIGHT_RED}✗{Color.RESET} {result.test_type.value}")
                if result.error_message:
                    print(f"  Error: {Color.RED}{result.error_message}{Color.RESET}")
            print()
        
        print(f"{Color.BRIGHT_GREEN}✓ All results logged to database (Drive ID: {drive_id[:8]}...){Color.RESET}")
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to menu...{Color.RESET}")
    
    def test_history_menu(self):
        """Submenu for viewing test history"""
        clear_screen()
        print_header()
        
        print_section("Test History & Drive Database", Color.BRIGHT_MAGENTA)
        print(f"{Color.BRIGHT_RED}⚠ COMING SOON{Color.RESET}")
        print(f"{Color.WHITE}History viewing and comparison tools will be implemented next.{Color.RESET}\n")
        
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
    
    def database_menu(self):
        """Submenu for drive database management"""
        clear_screen()
        print_header()
        
        print_section("Drive Database Management", Color.BRIGHT_BLUE)
        print(f"{Color.BRIGHT_RED}⚠ COMING SOON{Color.RESET}")
        print(f"{Color.WHITE}Database query and export tools will be implemented next.{Color.RESET}\n")
        
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
    
    def settings_menu(self):
        """Submenu for settings"""
        clear_screen()
        print_header()
        
        print_section("Settings & Configuration", Color.BRIGHT_CYAN)
        print(f"{Color.BRIGHT_RED}⚠ COMING SOON{Color.RESET}")
        print(f"{Color.WHITE}Configuration options will be implemented next.{Color.RESET}\n")
        
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")


# ============================================================================
# DISK CLASSIFICATION & DETECTION
# ============================================================================
