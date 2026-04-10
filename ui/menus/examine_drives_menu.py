"""
Examine Drives menu - drive inspection and analysis.
"""

from typing import Optional
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_success, print_warning, print_error
from ui.reporters import DiskReporter


class ExamineDrivesMenu:
    """Menu for examining and inspecting USB drives."""

    def __init__(self, inspector: DiskInspector, db: DatabaseManager, settings):
        self.inspector = inspector
        self.db = db
        self.settings = settings

    def show(self):
        """Display examine drives menu and handle user interaction. Loops until user backs out."""
        while True:
            clear_screen()
            print_header()

            print_section("Scanning for External USB Drives", Color.BRIGHT_CYAN)

            # Scan for drives
            external_disks = self.inspector.enumerate_external_disks()

            if not external_disks:
                print_warning("No external USB drives detected")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
                return

            print_success(f"Found {len(external_disks)} external disk(s)\n")

            # Display drive list
            self._display_drive_list(external_disks)

            # Get user choice
            print(f"  {Color.BRIGHT_YELLOW}[R]{Color.RESET} Rescan drives")
            print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")
            print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
            choice = input(f"{Color.BRIGHT_GREEN}Select drive to examine: {Color.RESET}").strip().upper()

            if choice == 'B':
                return
            if choice == 'R':
                continue

            try:
                index = int(choice) - 1
                if 0 <= index < len(external_disks):
                    self._display_drive_inspection(external_disks[index])
                else:
                    print_error("Invalid selection")
                    input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            except ValueError:
                print_error("Invalid selection")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _display_drive_list(self, disks):
        """Display formatted list of drives."""
        print(f"{Color.BRIGHT_WHITE}Available Drives:{Color.RESET}\n")

        for i, disk in enumerate(disks, 1):
            # Calculate mount status
            mounted_count = sum(1 for p in disk.partitions if p.is_mounted)
            total_count = len(disk.partitions)

            if mounted_count == total_count and total_count > 0:
                mount_status = f"{Color.BRIGHT_GREEN}● MOUNTED{Color.RESET}"
            elif mounted_count > 0:
                mount_status = f"{Color.BRIGHT_YELLOW}◐ PARTIAL ({mounted_count}/{total_count}){Color.RESET}"
            else:
                mount_status = f"{Color.BRIGHT_RED}○ NOT MOUNTED{Color.RESET}"

            # Get volume name from first partition
            volume_name = self._get_volume_name(disk)

            # Use volume name as primary label when available (adapter names like
            # "SABRENT Media" are meaningless - the volume name is what identifies the drive)
            display_name = volume_name if volume_name else disk.name

            print(
                f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{disk.identifier}{Color.RESET} - {Color.BRIGHT_WHITE}{display_name}{Color.RESET} {mount_status}")
            print(f"      {Color.WHITE}{disk.name}{Color.RESET} | {disk.size_human} | {disk.bus_protocol} | {total_count} partition(s)")

            print()

    def _get_volume_name(self, disk) -> Optional[str]:
        """Extract volume name from disk partitions."""
        for partition in disk.partitions:
            if partition.volume_name:
                return partition.volume_name
        return None

    def _display_drive_inspection(self, disk):
        """Display detailed inspection of a single drive."""
        clear_screen()
        print_header()

        # Display inspection results
        reporter = DiskReporter()
        reporter.display_disk_summary(disk)

        print(f"\n{Color.BRIGHT_GREEN}✓ Inspection logged to database{Color.RESET}")
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to drive menu...{Color.RESET}")