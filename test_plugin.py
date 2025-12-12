import unittest
from unittest.mock import MagicMock, patch
import json
from client import AgentForgeClient

class TestAgentForgeClient(unittest.TestCase):
    def setUp(self):
        self.client = AgentForgeClient(relay_url="http://mock-server:5000")

    @patch('requests.Session.post')
    def test_send_command_success(self, mock_post):
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Execute
        result = self.client.send_command("test_action", {"key": "value"})

        # Assert
        self.assertEqual(result['status'], 'success')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['payload']['action'], "test_action")
        self.assertEqual(kwargs['json']['payload']['data'], {"key": "value"})

    @patch('requests.Session.post')
    def test_send_command_connection_error(self, mock_post):
        # Setup mock to raise exception
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        # Execute
        result = self.client.send_command("test_action")

        # Assert
        self.assertEqual(result['status'], 'error')
        self.assertIn("Connection refused", result['message'])

    @patch('requests.Session.get')
    def test_poll_responses_success(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {
                    "id": "1",
                    "sender": "gpt",
                    "payload_chunk": {
                        "content": "SGVsbG8gV29ybGQ=", # "Hello World" in base64
                        "is_base64": True
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # Execute
        msgs = self.client.poll_responses()

        # Assert
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['content'], "Hello World")

    @patch('requests.Session.get')
    def test_poll_responses_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": []}
        mock_get.return_value = mock_response

        msgs = self.client.poll_responses()
        self.assertEqual(len(msgs), 0)

if __name__ == '__main__':
    unittest.main()
