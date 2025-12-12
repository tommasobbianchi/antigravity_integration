
import unittest
from unittest.mock import MagicMock, patch
from client import AgentForgeClient

class TestAgentForgeClient(unittest.TestCase):
    def setUp(self):
        self.client = AgentForgeClient(relay_url="http://mock-relay:5000")

    @patch('client.requests.Session.post')
    def test_send_command_success(self, mock_post):
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Call method
        result = self.client.send_command("test_action", {"key": "value"})

        # Assertions
        self.assertEqual(result['status'], 'success')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['payload']['action'], "test_action")
        self.assertEqual(kwargs['json']['sender'], "chatgpt")

    @patch('client.requests.Session.post')
    def test_send_command_connection_error(self, mock_post):
        # Configure mock to raise connection error
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        # Call method
        result = self.client.send_command("test_action", {})

        # Assertions
        self.assertEqual(result['status'], 'error')
        self.assertIn("Connection refused", result['message'])

    @patch('client.requests.Session.get')
    def test_poll_responses_success(self, mock_get):
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {
                    "id": "1",
                    "timestamp": 100,
                    "sender": "executor",
                    "payload_chunk": {"content": "dGVzdA==", "is_base64": True} # "test" base64
                }
            ]
        }
        mock_get.return_value = mock_response

        # Call method
        messages = self.client.poll_responses(min_timestamp=0)

        # Assertions
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['sender'], "executor")
        self.assertEqual(messages[0]['content'], "test")

if __name__ == '__main__':
    unittest.main()
