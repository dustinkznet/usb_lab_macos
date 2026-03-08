"""
Examine Drives menu - drive inspection and analysis.
ADDED: Alerts when known drives reconnect.
"""

from typing import Optional
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_success, print_warning, print_error
from ui.reporters import DiskReporter
from ui.drive_database import DriveDatabase


class ExamineDrivesMenu:
    """Menu for examining and inspecting USB drives."""

    def __init__(self, inspector: DiskInspector, db: DatabaseManager, settings):
        self.inspector = inspector
        self.db = db
        self.settings = settings
        self.drive_db = DriveDatabase(db)

    def show(self):
        """Display examine drives menu and handle user interaction."""
        clear_screen()
        print_header()

        print_section("Scanning for External USB Drives", Color.BRIGHT_CYAN)

        external_disks = self.inspector.enumerate_external_disks()

        if not external_disks:
            print_warning("No external USB drives detected")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
            return

        print_success(f"Found {len(external_disks)} external disk(s)\n")

        # ADDED: Check for known drives and alert
        self._check_known_drives(external_disks)

        self._display_drive_list(external_disks)

        print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")
        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select drive to examine: {Color.RESET}").strip().upper()

        if choice == 'B':
            return

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

    def _check_known_drives(self, disks):
        """Check if any detected drives are known and show alerts."""
        for disk in disks:
            # Get serial number
            info = self.inspector.backend.get_disk_info(disk.identifier)
            if info:
                serial = info.get('SerialNumber', disk.identifier)

                # Extract vendor/model
                if disk.name and disk.name != "Unknown":
                    name_parts = disk.name.split()
                    if len(name_parts) >= 2:
                        vendor = name_parts[0]
                        model = " ".join(name_parts[1:])
                    else:
                        vendor = disk.name
                        model = ""
                else:
                    vendor = "Unknown"
                    model = ""

                # Generate drive_id and check
                drive_id = self.db.generate_drive_id(vendor, model, serial)
                self.drive_db.check_for_known_drive(drive_id)

    def _display_drive_list(self, disks):
        """Display formatted list of drives."""
        print(f"{Color.BRIGHT_WHITE}Available Drives:{Color.RESET}\n")

        for i, disk in enumerate(disks, 1):
            mounted_count = sum(1 for p in disk.partitions if p.is_mounted)
            total_count = len(disk.partitions)

            if mounted_count == total_count and total_count > 0:
                mount_status = f"{Color.BRIGHT_GREEN}● MOUNTED{Color.RESET}"
            elif mounted_count > 0:
                mount_status = f"{Color.BRIGHT_YELLOW}◐ PARTIAL ({mounted_count}/{total_count}){Color.RESET}"
            else:
                mount_status = f"{Color.BRIGHT_RED}○ NOT MOUNTED{Color.RESET}"

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

        reporter = DiskReporter()
        reporter.display_disk_summary(disk)

        print(f"\n{Color.BRIGHT_GREEN}✓ Inspection logged to database{Color.RESET}")
        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to drive menu...{Color.RESET}")