"""
Drive testing engine for health checks and performance benchmarks.
REWRITTEN to use dd and Unix tools for accurate, reliable results.

Test Order (CORRECT):
1. Health Check - verify drive is functional
2. Sequential Write - create test file with dd
3. Sequential Read - read back test file (with cache clearing)
4. Cleanup - remove test files
"""

import os
import re
import subprocess
import shutil
from datetime import datetime
from typing import Optional, List, Tuple
from pathlib import Path

from core.models import PhysicalDisk, Partition, TestResult
from core.enums import TestType, DiskType
from core.constants import TEST_DIR_NAME
from database.db_manager import DatabaseManager
from ui.colors import Color


class DriveTestEngine:
    """
    Drive testing engine using dd and Unix tools.

    All I/O operations use dd for accuracy and consistency.
    Python just orchestrates and parses results.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.test_dir_name = TEST_DIR_NAME

    def should_test_drive(self, disk: PhysicalDisk) -> tuple[bool, str]:
        """Determine if a drive is safe to test."""
        installer_types = [
            DiskType.MACOS_INSTALLER_LEGACY,
            DiskType.MACOS_INSTALLER_MODERN,
            DiskType.LINUX_INSTALLER,
            DiskType.WINDOWS_INSTALLER,
            DiskType.BOOT_RECOVERY
        ]

        if disk.disk_type in installer_types:
            return False, f"Drive contains {disk.disk_type.value} - testing not recommended"

        data_partitions = []
        for part in disk.partitions:
            if part.is_mounted and part.mount_point:
                try:
                    files = os.listdir(part.mount_point)
                    visible_files = [f for f in files if not f.startswith('.')]
                    if visible_files:
                        data_partitions.append(part.identifier)
                except (PermissionError, OSError):
                    pass

        if data_partitions:
            return True, f"Drive has data on {len(data_partitions)} partition(s) - user confirmation required"

        if disk.disk_type in [DiskType.EMPTY, DiskType.DATA_DISK]:
            return True, "Drive appears safe for testing"

        if disk.disk_type == DiskType.UNKNOWN:
            return True, "Drive type unknown - user confirmation required"

        return False, "Drive type not recognized for testing"

    def run_health_check(self, partition: Partition, drive_id: str, adapter_info: str = None) -> TestResult:
        """Run basic health check on a partition."""
        print(f"\n{Color.BRIGHT_CYAN}Running health check on {partition.identifier}...{Color.RESET}")

        if not partition.is_mounted:
            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                success=False,
                duration_seconds=0,
                error_message="Partition not mounted"
            )

        start_time = datetime.now()
        notes = []

        try:
            print(f"  {Color.CYAN}[1/3] Checking read access...{Color.RESET}", end=" ", flush=True)
            files = os.listdir(partition.mount_point)
            print(f"{Color.BRIGHT_GREEN}✓{Color.RESET}")
            notes.append(f"Read access verified ({len(files)} items)")

            print(f"  {Color.CYAN}[2/3] Checking write access...{Color.RESET}", end=" ", flush=True)
            test_dir = os.path.join(partition.mount_point, self.test_dir_name)

            try:
                os.makedirs(test_dir, exist_ok=True)
                print(f"{Color.BRIGHT_GREEN}✓{Color.RESET}")
                notes.append("Write access verified")
            except PermissionError:
                print(f"{Color.BRIGHT_YELLOW}✗ Read-only{Color.RESET}")
                notes.append("Partition is read-only")
                duration = (datetime.now() - start_time).total_seconds()
                return TestResult(
                    test_type=TestType.HEALTH_CHECK,
                    success=False,
                    duration_seconds=duration,
                    error_message="Partition is read-only - cannot run write tests",
                    notes=notes
                )

            print(f"  {Color.CYAN}[3/3] Verifying data integrity...{Color.RESET}", end=" ", flush=True)
            test_file = os.path.join(test_dir, "health_check.dat")

            result = subprocess.run(
                ['dd', 'if=/dev/zero', f'of={test_file}', 'bs=1m', 'count=1'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception("Write verification failed")

            result = subprocess.run(
                ['dd', f'if={test_file}', 'of=/dev/null', 'bs=1m'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception("Read verification failed")

            os.remove(test_file)

            print(f"{Color.BRIGHT_GREEN}✓{Color.RESET}")
            notes.append("Data integrity verified")

            duration = (datetime.now() - start_time).total_seconds()

            self.db.log_test_run(
                drive_id=drive_id,
                test_type=TestType.HEALTH_CHECK.value,
                filesystem_tested=partition.filesystem.value,
                mount_point=partition.mount_point,
                partition_identifier=partition.identifier,
                duration_seconds=duration,
                adapter_info=adapter_info,
                success=True,
                notes="; ".join(notes)
            )

            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                success=True,
                duration_seconds=duration,
                notes=notes
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )

    def _parse_dd_output(self, stderr: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse dd output to extract bytes transferred and speed."""
        match = re.search(r'(\d+) bytes transferred in ([\d.]+) secs \(([\d.]+) bytes/sec\)', stderr)

        if match:
            bytes_transferred = int(match.group(1))
            duration = float(match.group(2))
            bytes_per_sec = float(match.group(3))
            speed_mbps = bytes_per_sec / (1024 * 1024)
            return bytes_transferred, speed_mbps

        return None, None

    def run_sequential_write_test(self, partition: Partition, drive_id: str,
                                  file_size_mb: int = 100, adapter_info: str = None) -> TestResult:
        """Run sequential write test using dd."""
        if not partition.is_mounted:
            return TestResult(
                test_type=TestType.SEQUENTIAL_WRITE,
                success=False,
                duration_seconds=0,
                error_message="Partition not mounted"
            )

        test_dir = os.path.join(partition.mount_point, self.test_dir_name)
        test_file = os.path.join(test_dir, f"write_test_{file_size_mb}mb.dat")

        try:
            os.makedirs(test_dir, exist_ok=True)
        except PermissionError:
            return TestResult(
                test_type=TestType.SEQUENTIAL_WRITE,
                success=False,
                duration_seconds=0,
                error_message="No write permission"
            )

        print(f"\n{Color.BRIGHT_YELLOW}Testing sequential write ({file_size_mb}MB)...{Color.RESET}")

        try:
            result = subprocess.run(
                ['dd', 'if=/dev/zero', f'of={test_file}', 'bs=1m', f'count={file_size_mb}', 'oflag=sync'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"dd failed: {result.stderr}")

            bytes_transferred, speed_mbps = self._parse_dd_output(result.stderr)

            if speed_mbps is None:
                raise Exception("Failed to parse dd output")

            print(f"  {Color.BRIGHT_GREEN}✓ Write speed: {speed_mbps:.2f} MB/s{Color.RESET}")

            self.db.log_test_run(
                drive_id=drive_id,
                test_type=TestType.SEQUENTIAL_WRITE.value,
                filesystem_tested=partition.filesystem.value,
                mount_point=partition.mount_point,
                partition_identifier=partition.identifier,
                file_size_bytes=bytes_transferred,
                block_size_bytes=1024 * 1024,
                duration_seconds=0,
                bytes_transferred=bytes_transferred,
                speed_mbps=speed_mbps,
                adapter_info=adapter_info,
                success=True
            )

            return TestResult(
                test_type=TestType.SEQUENTIAL_WRITE,
                success=True,
                duration_seconds=0,
                speed_mbps=speed_mbps,
                bytes_transferred=bytes_transferred
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_type=TestType.SEQUENTIAL_WRITE,
                success=False,
                duration_seconds=0,
                error_message="Test timed out (>5 minutes)"
            )
        except Exception as e:
            return TestResult(
                test_type=TestType.SEQUENTIAL_WRITE,
                success=False,
                duration_seconds=0,
                error_message=str(e)
            )

    def run_sequential_read_test(self, partition: Partition, drive_id: str,
                                 file_size_mb: int = 100, adapter_info: str = None) -> TestResult:
        """Run sequential read test using dd."""
        if not partition.is_mounted:
            return TestResult(
                test_type=TestType.SEQUENTIAL_READ,
                success=False,
                duration_seconds=0,
                error_message="Partition not mounted"
            )

        test_dir = os.path.join(partition.mount_point, self.test_dir_name)
        test_file = os.path.join(test_dir, f"write_test_{file_size_mb}mb.dat")

        if not os.path.exists(test_file):
            return TestResult(
                test_type=TestType.SEQUENTIAL_READ,
                success=False,
                duration_seconds=0,
                error_message="Test file not found - run write test first"
            )

        print(f"\n{Color.BRIGHT_YELLOW}Testing sequential read ({file_size_mb}MB)...{Color.RESET}")

        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BRIGHT_WHITE}Cache Clearing Required for Accurate Results{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"\n{Color.CYAN}Without clearing the disk cache, the read test will measure{Color.RESET}")
        print(f"{Color.CYAN}RAM speed (~7000 MB/s) instead of actual USB drive speed.{Color.RESET}")
        print(f"\n{Color.YELLOW}You will be prompted for your password to run: sudo purge{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}\n")

        cache_cleared = self._clear_disk_cache()

        if not cache_cleared:
            print(f"\n{Color.BRIGHT_RED}✗ Cache clearing failed or was cancelled{Color.RESET}")
            print(f"{Color.YELLOW}Read test results will be INACCURATE (measuring RAM cache).{Color.RESET}")

            response = input(f"\n{Color.BRIGHT_GREEN}Continue with inaccurate read test? (y/n): {Color.RESET}").strip().lower()
            if response != 'y':
                return TestResult(
                    test_type=TestType.SEQUENTIAL_READ,
                    success=False,
                    duration_seconds=0,
                    error_message="Cache clearing failed - test cancelled by user"
                )
        else:
            print(f"{Color.BRIGHT_GREEN}✓ Disk cache cleared successfully{Color.RESET}")

        try:
            result = subprocess.run(
                ['dd', f'if={test_file}', 'of=/dev/null', 'bs=1m'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                raise Exception(f"dd failed: {result.stderr}")

            bytes_transferred, speed_mbps = self._parse_dd_output(result.stderr)

            if speed_mbps is None:
                raise Exception("Failed to parse dd output")

            note = None
            if not cache_cleared:
                note = "⚠ INACCURATE: Cache not cleared - measured RAM speed, not disk speed"
                print(f"  {Color.BRIGHT_RED}✗ Read speed: {speed_mbps:.2f} MB/s (RAM CACHE - NOT ACCURATE){Color.RESET}")
            elif speed_mbps > 2000:
                note = "⚠ WARNING: Speed > 2000 MB/s suggests RAM cache, not disk"
                print(f"  {Color.BRIGHT_YELLOW}⚠ Read speed: {speed_mbps:.2f} MB/s (unusually high - possible cache){Color.RESET}")
            else:
                print(f"  {Color.BRIGHT_GREEN}✓ Read speed: {speed_mbps:.2f} MB/s{Color.RESET}")

            self.db.log_test_run(
                drive_id=drive_id,
                test_type=TestType.SEQUENTIAL_READ.value,
                filesystem_tested=partition.filesystem.value,
                mount_point=partition.mount_point,
                partition_identifier=partition.identifier,
                file_size_bytes=bytes_transferred,
                block_size_bytes=1024 * 1024,
                duration_seconds=0,
                bytes_transferred=bytes_transferred,
                speed_mbps=speed_mbps,
                adapter_info=adapter_info,
                success=True,
                notes=note
            )

            return TestResult(
                test_type=TestType.SEQUENTIAL_READ,
                success=True,
                duration_seconds=0,
                speed_mbps=speed_mbps,
                bytes_transferred=bytes_transferred,
                notes=[note] if note else []
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_type=TestType.SEQUENTIAL_READ,
                success=False,
                duration_seconds=0,
                error_message="Test timed out (>5 minutes)"
            )
        except Exception as e:
            return TestResult(
                test_type=TestType.SEQUENTIAL_READ,
                success=False,
                duration_seconds=0,
                error_message=str(e)
            )

    def _clear_disk_cache(self) -> bool:
        """Clear disk cache using 'purge' command (macOS)."""
        try:
            result = subprocess.run(['sudo', 'purge'], timeout=60)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"\n{Color.BRIGHT_RED}✗ Timeout waiting for password{Color.RESET}")
            return False
        except KeyboardInterrupt:
            print(f"\n{Color.BRIGHT_YELLOW}✗ Cancelled by user{Color.RESET}")
            return False
        except Exception as e:
            print(f"\n{Color.BRIGHT_RED}✗ Error: {e}{Color.RESET}")
            return False

    def cleanup_test_files(self, partition: Partition):
        """Clean up test files and directory."""
        if not partition.is_mounted:
            return

        test_dir = os.path.join(partition.mount_point, self.test_dir_name)

        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
                print(f"\n{Color.CYAN}✓ Test files cleaned up{Color.RESET}")
            except Exception as e:
                print(f"\n{Color.YELLOW}⚠ Could not clean up test files: {e}{Color.RESET}")

    def run_comprehensive_test_suite(self, partition: Partition, drive_id: str,
                                    file_size_mb: int = 100, adapter_info: str = None) -> List[TestResult]:
        """Run the full test suite on a partition."""
        results = []

        print(f"\n{Color.BRIGHT_MAGENTA}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}COMPREHENSIVE TEST SUITE{Color.RESET}")
        print(f"{Color.BRIGHT_MAGENTA}{'═' * 80}{Color.RESET}")

        print(f"\n{Color.BRIGHT_CYAN}[TEST 1/3] Health & Integrity Check{Color.RESET}")
        result = self.run_health_check(partition, drive_id, adapter_info)
        results.append(result)

        if not result.success:
            print(f"\n{Color.BRIGHT_RED}✗ Health check failed. Aborting test suite.{Color.RESET}")
            return results

        print(f"\n{Color.BRIGHT_CYAN}[TEST 2/3] Sequential Write Performance{Color.RESET}")
        result = self.run_sequential_write_test(partition, drive_id, file_size_mb, adapter_info)
        results.append(result)

        if not result.success:
            print(f"\n{Color.BRIGHT_YELLOW}⚠ Write test failed. Skipping read test.{Color.RESET}")
            self.cleanup_test_files(partition)
            return results

        print(f"\n{Color.BRIGHT_CYAN}[TEST 3/3] Sequential Read Performance{Color.RESET}")
        result = self.run_sequential_read_test(partition, drive_id, file_size_mb, adapter_info)
        results.append(result)

        self.cleanup_test_files(partition)

        return results