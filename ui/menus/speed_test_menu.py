"""
Speed Test menu - drive performance testing.
"""

from typing import Optional, List
from core.models import PhysicalDisk
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector
from testing.test_engine import DriveTestEngine
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_success, print_warning, print_error


class SpeedTestMenu:
    """Menu for performance testing USB drives."""

    def __init__(self, inspector: DiskInspector, db: DatabaseManager, settings):
        self.inspector = inspector
        self.db = db
        self.settings = settings
        self.test_engine = DriveTestEngine(db, settings)

    def show(self):
        """Display speed test menu and handle user interaction. Loops until user backs out."""
        while True:
            clear_screen()
            print_header()

            print_section("Read/Write Speed Testing", Color.BRIGHT_YELLOW)

            external_disks = self.inspector.enumerate_external_disks()

            if not external_disks:
                print_warning("No external USB drives detected")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
                return

            print_success(f"Found {len(external_disks)} external disk(s)\n")

            testable_disks = self._display_drive_list_with_safety(external_disks)

            if not testable_disks:
                print_error("No drives are safe to test")
                print(f"{Color.YELLOW}Installer/Boot drives are protected from testing.{Color.RESET}")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
                return

            print(f"  {Color.BRIGHT_YELLOW}[R]{Color.RESET} Rescan drives")
            print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")
            print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
            choice = input(f"{Color.BRIGHT_GREEN}Select drive to test: {Color.RESET}").strip().upper()

            if choice == 'B':
                return
            if choice == 'R':
                continue

            try:
                index = int(choice) - 1
                if 0 <= index < len(external_disks):
                    self._handle_drive_test(external_disks[index])
                else:
                    print_error("Invalid selection")
                    input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            except ValueError:
                print_error("Invalid selection")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _display_drive_list_with_safety(self, disks) -> List[PhysicalDisk]:
        """Display drives with safety assessment. Returns list of testable disks."""
        print(f"{Color.BRIGHT_WHITE}Available Drives:{Color.RESET}\n")
        testable_disks = []

        for i, disk in enumerate(disks, 1):
            can_test, reason = self.test_engine.should_test_drive(disk)

            status_color = Color.BRIGHT_GREEN if can_test else Color.BRIGHT_RED
            status_icon = "✓" if can_test else "✗"

            # Get volume name
            volume_name = self._get_volume_name(disk)

            # Use volume name as primary label when available
            display_name = volume_name if volume_name else disk.name

            print(
                f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{disk.identifier}{Color.RESET} - {Color.BRIGHT_WHITE}{display_name}{Color.RESET}")
            print(f"      {Color.WHITE}{disk.name}{Color.RESET} | {disk.size_human} | Type: {disk.disk_type.value}")

            print(f"      {status_color}{status_icon} {reason}{Color.RESET}")
            print()

            if can_test:
                testable_disks.append(disk)

        return testable_disks

    def _get_volume_name(self, disk) -> Optional[str]:
        """Extract volume name from disk partitions."""
        for partition in disk.partitions:
            if partition.volume_name:
                return partition.volume_name
        return None

    def _handle_drive_test(self, disk: PhysicalDisk):
        """Handle testing for a selected drive."""
        # Check if this disk is testable
        can_test, reason = self.test_engine.should_test_drive(disk)

        if not can_test:
            print_error(f"Cannot test this drive: {reason}")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            return

        # Confirm before testing if either:
        #   - confirm_before_testing is enabled in settings (always ask), OR
        #   - drive has data and require_confirmation_data_drives is enabled
        always_confirm = self.settings.get('confirm_before_testing', True)
        confirm_data = self.settings.get('require_confirmation_data_drives', True)
        has_data = "confirmation required" in reason.lower()

        if always_confirm or (has_data and confirm_data):
            if has_data:
                print_warning(reason)
            confirm = input(
                f"\n{Color.BRIGHT_YELLOW}Continue with testing? This will create test files. (yes/no): {Color.RESET}").strip().lower()
            if confirm != 'yes':
                print(f"{Color.CYAN}Testing cancelled.{Color.RESET}")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
                return

        self._run_comprehensive_tests(disk)

    def _run_comprehensive_tests(self, disk: PhysicalDisk):
        """Run comprehensive test suite on a disk."""
        clear_screen()
        print_header()

        # Register drive (pass serial so it matches the inspection record)
        drive_id = self.db.register_drive(disk, disk.serial_number)

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

        # Honor user-configured test file size, capped to max_test_file_size_mb
        file_size_mb = int(self.settings.get('default_test_file_size_mb', 100))
        max_size = int(self.settings.get('max_test_file_size_mb', 1000))
        if file_size_mb > max_size:
            file_size_mb = max_size
        print(f"{Color.WHITE}Test file size: {file_size_mb} MB{Color.RESET}")

        # Run test suite
        results = self.test_engine.run_comprehensive_test_suite(
            testable_partition, drive_id, file_size_mb=file_size_mb
        )

        # Display summary
        self._display_test_summary(results)

        print(f"{Color.BRIGHT_GREEN}✓ All results logged to database{Color.RESET}")
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to menu...{Color.RESET}")

    def _display_test_summary(self, results):
        """Display test results summary."""
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