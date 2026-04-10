"""
Settings and configuration management for USB LAB.
"""

import json
from pathlib import Path
from typing import Dict, Any


class SettingsManager:
    """
    Manage user settings and preferences for USB LAB.
    Settings are stored in ~/.usb_lab/settings.json
    """

    DEFAULT_SETTINGS = {
        # Inspection Settings
        "default_inspection_mode": "smart_auto",  # smart_auto, metadata_only, mounted_readonly
        "auto_log_inspections": True,  # Automatically log all inspections to the database

        # Testing Settings
        "default_test_file_size_mb": 100,  # Size for sequential read/write tests
        "max_test_file_size_mb": 1000,  # Hard cap on test file size
        "confirm_before_testing": True,  # Ask user confirmation before every speed test
        "require_confirmation_data_drives": True,  # Always confirm before testing a drive with data
        "auto_log_tests": True,  # Persist test results to the database
        "cleanup_test_files": True,  # Delete the test directory after each run
    }

    def __init__(self, settings_path: str = None):
        """
        Initialize settings manager.

        Args:
            settings_path: Path to settings file. If None, uses default location.
        """
        if settings_path is None:
            home = Path.home()
            settings_dir = home / '.usb_lab'
            settings_dir.mkdir(exist_ok=True)
            settings_path = settings_dir / 'settings.json'

        self.settings_path = Path(settings_path)
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create with defaults"""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults (in case new settings were added)
                    settings = self.DEFAULT_SETTINGS.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
        else:
            # Create default settings file
            self._save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS.copy()

    def _save_settings(self, settings: Dict[str, Any] = None):
        """Save settings to file"""
        if settings is None:
            settings = self.settings

        try:
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")

    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save"""
        self.settings[key] = value
        self._save_settings()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self._save_settings()

    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()

    def export_settings(self, export_path: str):
        """Export settings to a file"""
        with open(export_path, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def import_settings(self, import_path: str):
        """Import settings from a file"""
        with open(import_path, 'r') as f:
            imported = json.load(f)
            self.settings.update(imported)
            self._save_settings()