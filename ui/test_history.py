"""
Test history viewer for USB LAB.
Displays historical test results and inspection data.
"""

from database.db_manager import DatabaseManager
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_warning, print_error


class TestHistoryViewer:
    """View and analyze test history from database"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def show_test_history_menu(self):
        """Main test history menu"""
        clear_screen()
        print_header()

        print_section("Test History", Color.BRIGHT_MAGENTA)

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

        print(f"{Color.BRIGHT_WHITE}Drives with Test History:{Color.RESET}\n")

        for i, drive in enumerate(drives, 1):
            drive_id = drive['drive_id']

            cursor.execute('SELECT COUNT(*) as count FROM test_runs WHERE drive_id = ?', (drive_id,))
            test_count = cursor.fetchone()['count']

            cursor.execute('SELECT COUNT(*) as count FROM inspection_history WHERE drive_id = ?', (drive_id,))
            inspection_count = cursor.fetchone()['count']

            capacity_gb = drive['capacity_bytes'] / (1024 ** 3)

            # FIXED: Smart vendor/model display
            vendor_model = f"{drive['vendor']} {drive['model']}" if drive['model'] else drive['vendor']

            print(f"  {Color.BRIGHT_YELLOW}[{i}]{Color.RESET} {Color.BRIGHT_CYAN}{vendor_model}{Color.RESET}")
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
                self.show_drive_history(drive_id)
        except ValueError:
            print_error("Invalid selection")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def show_drive_history(self, drive_id: str):
        """Display complete history for a specific drive"""
        clear_screen()
        print_header()

        history = self.db.get_drive_history(drive_id)

        if not history['drive']:
            print_error("Drive not found in database")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            return

        drive = history['drive']

        # FIXED: Smart vendor/model display
        vendor_model = f"{drive['vendor']} {drive['model']}" if drive['model'] else drive['vendor']

        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}DRIVE HISTORY: {vendor_model}{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}\n")

        print(f"{Color.BRIGHT_WHITE}Drive Information:{Color.RESET}")
        print(f"  ID: {drive['drive_id'][:16]}...")
        print(f"  Capacity: {drive['capacity_bytes'] / (1024 ** 3):.1f} GB")
        print(f"  Bus: {drive['bus_protocol']}")
        print(f"  First Seen: {drive['first_seen']}")
        print(f"  Last Seen: {drive['last_seen']}")
        print()

        if history['inspections']:
            print(f"{Color.BRIGHT_WHITE}Inspection History ({len(history['inspections'])}):{Color.RESET}")
            for inspection in history['inspections'][:5]:
                print(f"\n  {Color.CYAN}[{inspection['timestamp']}]{Color.RESET}")
                print(f"    Type: {inspection['disk_type']}")
                print(f"    Confidence: {inspection['classification_confidence']}")
                print(f"    Partitions: {inspection['num_partitions']}")

            if len(history['inspections']) > 5:
                print(f"\n  {Color.YELLOW}... and {len(history['inspections']) - 5} more{Color.RESET}")
            print()

        if history['tests']:
            print(f"{Color.BRIGHT_WHITE}Performance Test Results ({len(history['tests'])}):{Color.RESET}\n")

            test_types = {}
            for test in history['tests']:
                test_type = test['test_type']
                if test_type not in test_types:
                    test_types[test_type] = []
                test_types[test_type].append(test)

            for test_type, tests in test_types.items():
                print(f"  {Color.BRIGHT_CYAN}{test_type.replace('_', ' ').title()}:{Color.RESET}")

                latest = tests[0]

                # FIXED: Only show speed if it exists (health checks have no speed)
                if latest.get('speed_mbps') is not None:
                    avg_speed = sum(t['speed_mbps'] or 0 for t in tests) / len(tests)
                    print(f"    Latest: {latest['speed_mbps']:.2f} MB/s ({latest['timestamp']})")

                    if latest.get('adapter_info'):
                        print(f"    Adapter: {Color.BRIGHT_YELLOW}{latest['adapter_info']}{Color.RESET}")

                    if len(tests) > 1:
                        print(f"    Average: {avg_speed:.2f} MB/s ({len(tests)} test runs)")
                else:
                    # Health check or other non-speed test
                    print(f"    Completed: {latest['timestamp']}")
                    if latest.get('adapter_info'):
                        print(f"    Adapter: {Color.BRIGHT_YELLOW}{latest['adapter_info']}{Color.RESET}")

                if latest.get('iops'):
                    avg_iops = sum(t['iops'] or 0 for t in tests) / len(tests)
                    print(f"    Latest IOPS: {latest['iops']:.1f}")
                    if len(tests) > 1:
                        print(f"    Average IOPS: {avg_iops:.1f}")
                print()
        else:
            print(f"{Color.YELLOW}No performance tests recorded yet{Color.RESET}\n")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return to test history...{Color.RESET}")