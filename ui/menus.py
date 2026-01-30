"""
Menu system for USB LAB.
"""

from typing import Optional
from pathlib import Path
from core.models import PhysicalDisk
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector
from testing.test_engine import DriveTestEngine
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_success, print_warning, print_error
from ui.reporters import DiskReporter
from ui.test_history import TestHistoryViewer
from ui.drive_database import DriveDatabase
from ui.settings_menu import SettingsMenu

class MenuSystem:
    """
    Interactive menu system for USB LAB.

    Provides navigation between different tool functions.
    """

    def __init__(self, inspector: 'DiskInspector', db: DatabaseManager, settings):
        self.inspector = inspector
        self.db = db
        self.settings = settings
        self.test_history = TestHistoryViewer(db)
        self.drive_db = DriveDatabase(db)
        self.settings_ui = SettingsMenu(settings)

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
            ("1", "Examine Drives", "Inspect USB drives (read-only, auto-detect)"),
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

        # Use SMART_AUTO mode - automatically scans mounted partitions
        external_disks = self.inspector.enumerate_external_disks()

        if not external_disks:
            print_warning("No external USB drives detected")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
            return

        print_success(f"Found {len(external_disks)} external disk(s)\n")

        # Display drive list with mount status
        print(f"{Color.BRIGHT_WHITE}Available Drives:{Color.RESET}\n")
        for i, disk in enumerate(external_disks, 1):
            # Calculate mount status
            mounted_count = sum(1 for p in disk.partitions if p.is_mounted)
            total_count = len(disk.partitions)

            if mounted_count == total_count and total_count > 0:
                mount_status = f"{Color.BRIGHT_GREEN}● MOUNTED{Color.RESET}"
            elif mounted_count > 0:
                mount_status = f"{Color.BRIGHT_YELLOW}◐ PARTIAL ({mounted_count}/{total_count}){Color.RESET}"
            else:
                mount_status = f"{Color.BRIGHT_RED}○ NOT MOUNTED{Color.RESET}"

            print(f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{disk.identifier}{Color.RESET} - {Color.WHITE}{disk.name}{Color.RESET} {mount_status}")
            print(f"      {disk.size_human} | {disk.bus_protocol} | {total_count} partition(s)")
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

        # Display inspection results (already logged by inspector)
        reporter = DiskReporter()
        reporter.display_disk_summary(disk)

        print(f"\n{Color.BRIGHT_GREEN}✓ Inspection logged to database{Color.RESET}")
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

        print(f"{Color.BRIGHT_GREEN}✓ All results logged to database{Color.RESET}")
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to menu...{Color.RESET}")

    def test_history_menu(self):
        """Submenu for viewing test history"""
        self.test_history.show_test_history_menu()

    def database_menu(self):
        """Submenu for drive database management"""
        self.drive_db.show_database_menu()

    def settings_menu(self):
        """Settings and configuration menu"""
        self.settings_ui.show_settings_menu()