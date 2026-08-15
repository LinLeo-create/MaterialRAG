import socket
import unittest
from unittest.mock import Mock

from backend.launcher import find_available_port, open_browser_when_ready


class LauncherTestCase(unittest.TestCase):
    def test_skips_an_occupied_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            port = occupied.getsockname()[1]
            selected = find_available_port("127.0.0.1", port, 20)
            self.assertNotEqual(selected, port)

    def test_opens_browser_after_server_starts(self):
        server = Mock(started=True, should_exit=False)
        opener = Mock()
        open_browser_when_ready(server, "http://127.0.0.1:8000", opener, timeout=0.1)
        opener.assert_called_once_with("http://127.0.0.1:8000")

    def test_does_not_open_browser_after_shutdown(self):
        server = Mock(started=False, should_exit=True)
        opener = Mock()
        open_browser_when_ready(server, "http://127.0.0.1:8000", opener, timeout=0.1)
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
