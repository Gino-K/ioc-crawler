import unittest
from unittest.mock import patch, MagicMock

from scheduler import task_manager


class TestTaskManager(unittest.TestCase):

    # --- Test für das Windows-Szenario ---
    @patch('sys.platform', 'win32')
    @patch('scheduler.task_manager.subprocess.run')
    def test_setup_on_windows(self, mock_subprocess_run):
        """Testet, ob auf Windows der korrekte schtasks-Befehl generiert wird."""
        print("\n[Scheduler-Test] Szenario 1: Windows")

        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")

        success = task_manager.setup_scheduled_task("Dienstag", "09:30")

        self.assertTrue(success)
        mock_subprocess_run.assert_called_once()

        called_command = mock_subprocess_run.call_args[0][0]

        self.assertIn('schtasks /Create', called_command)
        self.assertIn('/TN "IOC_Webcrawler_Scheduled_Run"', called_command)
        self.assertIn('/SC WEEKLY /D TUE /ST 09:30', called_command)
        self.assertIn('/F /RL HIGHEST', called_command)
        self.assertIn(task_manager.MAIN_SCRIPT_PATH, called_command)

    # --- Test für das Linux-Szenario ---
    @patch('sys.platform', 'linux')
    @patch('scheduler.task_manager.subprocess.run')
    def test_setup_on_linux(self, mock_subprocess_run):
        """Testet, ob auf Linux der korrekte cron-Job generiert wird."""
        print("\n[Scheduler-Test] Szenario 2: Linux")

        mock_crontab_list_result = MagicMock(returncode=0, stdout="0 1 * * 5 /some/other/task # OTHER_TASK\n",
                                             stderr="")
        mock_crontab_write_result = MagicMock(returncode=0)

        mock_subprocess_run.side_effect = [mock_crontab_list_result, mock_crontab_write_result]

        success = task_manager.setup_scheduled_task("Freitag", "22:00")

        self.assertTrue(success)
        self.assertEqual(mock_subprocess_run.call_count, 2)

        written_content = mock_subprocess_run.call_args.kwargs['input']

        self.assertIn("0 22 * * 5", written_content)  # Korrekte Zeit für Freitag 22:00
        self.assertIn(task_manager.MAIN_SCRIPT_PATH, written_content)
        self.assertIn(task_manager.CRON_JOB_MARKER, written_content)  # Unser Marker ist da
        self.assertIn("0 1 * * 5 /some/other/task # OTHER_TASK", written_content)  # Der alte Job ist noch da

    # --- Test für das macOS-Szenario ---
    @patch('sys.platform', 'darwin')
    @patch('builtins.print')
    def test_setup_on_macos(self, mock_print):
        """Testet, ob auf macOS die korrekte "nicht unterstützt"-Meldung kommt."""
        print("\n[Scheduler-Test] Szenario 3: macOS")

        success = task_manager.setup_scheduled_task("Samstag", "12:00")

        self.assertFalse(success)
        mock_print.assert_any_call(
            "HINWEIS: macOS wird derzeit für die automatische Erstellung von geplanten Aufgaben nicht unterstützt.")

    # --- Test für ein unbekanntes System ---
    @patch('sys.platform', 'sunos')
    @patch('builtins.print')
    def test_setup_on_unsupported_os(self, mock_print):
        """Testet das Verhalten auf einem gänzlich unbekannten Betriebssystem."""
        print("\n[Scheduler-Test] Szenario 4: Unbekanntes OS")

        success = task_manager.setup_scheduled_task("Sonntag", "20:00")

        self.assertFalse(success)
        mock_print.assert_any_call("FEHLER: Unbekanntes Betriebssystem 'sunos' wird nicht unterstützt.")


if __name__ == '__main__':
    unittest.main()