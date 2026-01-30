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
        clear_screen()
        print_header()

        print_section("Test History", Color.BRIGHT_MAGENTA)

        # Get all drives from database
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT drive_id, vendor, model, capacity_bytes, last_seen 
            FROM drives 
            ORDER BY last_seen DESC
        ''')
        drives = cursor.fetchall()

        if not drives:
            print_warning("No drives in database yet")
            print(f"\n{Color.CYAN}Inspect or test a drive to start logging data.{Color.RESET}")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")
            return

        # Display drives with test history
        print(f"{Color.BRIGHT_WHITE}Drives with Test History:{Color.RESET}\n")

        for i, drive in enumerate(drives, 1):
            drive_id = drive['drive_id']

            # Count tests for this drive
            cursor.execute('SELECT COUNT(*) as count FROM test_runs WHERE drive_id = ?', (drive_id,))
            test_count = cursor.fetchone()['count']

            # Count inspections
            cursor.execute('SELECT COUNT(*) as count FROM inspection_history WHERE drive_id = ?', (drive_id,))
            inspection_count = cursor.fetchone()['count']

            capacity_gb = drive['capacity_bytes'] / (1024**3)

            print(f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{drive['vendor']} {drive['model']}{Color.RESET}")
            print(f"      {capacity_gb:.1f} GB | Last seen: {drive['last_seen']}")
            print(f"      {Color.CYAN}{inspection_count} inspection(s), {test_count} test(s){Color.RESET}")
            print()

        print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")

        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select drive to view history: {Color.RESET}").strip().upper()

        if choice == 'B':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(drives):
                drive_id = drives[index]['drive_id']
                self._display_drive_history(drive_id)
        except ValueError:
            print_error("Invalid selection")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _display_drive_history(self, drive_id: str):
        """Display complete history for a specific drive"""
        clear_screen()
        print_header()

        # Get drive history
        history = self.db.get_drive_history(drive_id)

        if not history['drive']:
            print_error("Drive not found in database")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            return

        drive = history['drive']

        # Display drive info
        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}DRIVE HISTORY: {drive['vendor']} {drive['model']}{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}\n")

        print(f"{Color.BRIGHT_WHITE}Drive Information:{Color.RESET}")
        print(f"  ID: {drive['drive_id'][:16]}...")
        print(f"  Capacity: {drive['capacity_bytes'] / (1024**3):.1f} GB")
        print(f"  Bus: {drive['bus_protocol']}")
        print(f"  First Seen: {drive['first_seen']}")
        print(f"  Last Seen: {drive['last_seen']}")
        print()

        # Display inspection history
        if history['inspections']:
            print(f"{Color.BRIGHT_WHITE}Inspection History ({len(history['inspections'])}):{Color.RESET}")
            for inspection in history['inspections'][:5]:  # Show last 5
                print(f"\n  {Color.CYAN}[{inspection['timestamp']}]{Color.RESET}")
                print(f"    Type: {inspection['disk_type']}")
                print(f"    Confidence: {inspection['classification_confidence']}")
                print(f"    Partitions: {inspection['num_partitions']}")

            if len(history['inspections']) > 5:
                print(f"\n  {Color.YELLOW}... and {len(history['inspections']) - 5} more{Color.RESET}")
            print()

        # Display test results
        if history['tests']:
            print(f"{Color.BRIGHT_WHITE}Performance Test Results ({len(history['tests'])}):{Color.RESET}\n")

            # Group by test type
            test_types = {}
            for test in history['tests']:
                test_type = test['test_type']
                if test_type not in test_types:
                    test_types[test_type] = []
                test_types[test_type].append(test)

            for test_type, tests in test_types.items():
                print(f"  {Color.BRIGHT_CYAN}{test_type.replace('_', ' ').title()}:{Color.RESET}")

                # Show latest result and average
                latest = tests[0]
                avg_speed = sum(t['speed_mbps'] or 0 for t in tests) / len(tests)

                print(f"    Latest: {latest['speed_mbps']:.2f} MB/s ({latest['timestamp']})")
                if len(tests) > 1:
                    print(f"    Average: {avg_speed:.2f} MB/s ({len(tests)} test runs)")

                if latest.get('iops'):
                    avg_iops = sum(t['iops'] or 0 for t in tests) / len(tests)
                    print(f"    Latest IOPS: {latest['iops']:.1f}")
                    if len(tests) > 1:
                        print(f"    Average IOPS: {avg_iops:.1f}")
                print()
        else:
            print(f"{Color.YELLOW}No performance tests recorded yet{Color.RESET}\n")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to test history...{Color.RESET}")

    def database_menu(self):
        """Submenu for drive database management"""
        clear_screen()
        print_header()

        print_section("Drive Database", Color.BRIGHT_BLUE)

        # Get database statistics
        cursor = self.db.conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM drives')
        drive_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM test_runs')
        test_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM inspection_history')
        inspection_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(DISTINCT drive_id) as count FROM test_runs')
        tested_drive_count = cursor.fetchone()['count']

        # Display statistics
        print(f"{Color.BRIGHT_WHITE}Database Statistics:{Color.RESET}\n")
        print(f"  Total Drives Registered: {Color.BRIGHT_CYAN}{drive_count}{Color.RESET}")
        print(f"  Total Inspections: {Color.BRIGHT_CYAN}{inspection_count}{Color.RESET}")
        print(f"  Total Test Runs: {Color.BRIGHT_CYAN}{test_count}{Color.RESET}")
        print(f"  Drives with Test Data: {Color.BRIGHT_CYAN}{tested_drive_count}{Color.RESET}")
        print()

        print(f"  Database Location: {Color.CYAN}{self.db.db_path}{Color.RESET}")
        print()

        # Show recent activity
        print(f"{Color.BRIGHT_WHITE}Recent Activity:{Color.RESET}\n")

        cursor.execute('''
            SELECT d.vendor, d.model, d.last_seen, 
                   (SELECT COUNT(*) FROM test_runs WHERE drive_id = d.drive_id) as test_count
            FROM drives d
            ORDER BY d.last_seen DESC
            LIMIT 5
        ''')
        recent_drives = cursor.fetchall()

        if recent_drives:
            for drive in recent_drives:
                print(f"  {Color.CYAN}{drive['vendor']} {drive['model']}{Color.RESET}")
                print(f"    Last seen: {drive['last_seen']} | Tests: {drive['test_count']}")
                print()
        else:
            print(f"  {Color.YELLOW}No drives in database yet{Color.RESET}\n")

        # Menu options
        print(f"\n{Color.BRIGHT_WHITE}Options:{Color.RESET}\n")
        print(f"  {Color.BRIGHT_YELLOW}[1]{Color.RESET} View all drives")
        print(f"  {Color.BRIGHT_YELLOW}[2]{Color.RESET} Export database (coming soon)")
        print(f"  {Color.BRIGHT_YELLOW}[3]{Color.RESET} Clear database (coming soon)")
        print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")

        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select option: {Color.RESET}").strip().upper()

        if choice == '1':
            self._view_all_drives()
        elif choice == 'B':
            return
        else:
            print_warning("Option not yet implemented")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _view_all_drives(self):
        """View all drives in database"""
        clear_screen()
        print_header()

        print_section("All Registered Drives", Color.BRIGHT_BLUE)

        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT drive_id, vendor, model, serial_number, capacity_bytes, 
                   bus_protocol, first_seen, last_seen
            FROM drives
            ORDER BY last_seen DESC
        ''')
        drives = cursor.fetchall()

        if not drives:
            print_warning("No drives in database")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return...{Color.RESET}")
            return

        print(f"{Color.BRIGHT_WHITE}Total Drives: {len(drives)}{Color.RESET}\n")

        for i, drive in enumerate(drives, 1):
            print(f"{Color.BRIGHT_YELLOW}[{i}] {drive['vendor']} {drive['model']}{Color.RESET}")
            print(f"    Serial: {drive['serial_number']}")
            print(f"    Capacity: {drive['capacity_bytes'] / (1024**3):.1f} GB")
            print(f"    Bus: {drive['bus_protocol']}")
            print(f"    First seen: {drive['first_seen']}")
            print(f"    Last seen: {drive['last_seen']}")

            # Get test count
            cursor.execute('SELECT COUNT(*) as count FROM test_runs WHERE drive_id = ?',
                          (drive['drive_id'],))
            test_count = cursor.fetchone()['count']
            print(f"    {Color.CYAN}Tests recorded: {test_count}{Color.RESET}")
            print()

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return...{Color.RESET}")

    def settings_menu(self):
        """Submenu for settings"""
        clear_screen()
        print_header()

        print_section("Settings & Configuration", Color.BRIGHT_CYAN)
        print(f"{Color.BRIGHT_RED}⚠ COMING SOON{Color.RESET}")
        print(f"{Color.WHITE}Configuration options will be implemented next.{Color.RESET}\n")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to main menu...{Color.RESET}")