import asyncio
import configparser
import unittest
from unittest.mock import patch, MagicMock

from classes.llm_client import LlmClient, LlmResponse


def make_config():
    # Minimal config with the "Active" provider host, as a user would set it in config.ini
    config = configparser.ConfigParser()
    config["LLM Client Active"] = {"host_name": "http://127.0.0.1:8000"}
    return config


def make_response(status_code, json_data):
    # Fake HTTP response as returned by requests.post
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    return mock_response


def llm_success(*args, **kwargs):
    # Provider answers successfully
    return make_response(200, {"result": "ok"})


def llm_down(*args, **kwargs):
    # Provider is unreachable / erroring out
    return make_response(500, {})


class TestLLMClient(unittest.TestCase):
    def setUp(self):
        # LlmClient is a singleton; clear cached instances so each test starts fresh
        LlmClient._instances = {}

    def test_llm_client_initialization(self):
        """Client picks up the host configured for the chosen provider."""
        client = LlmClient("Active", make_config())

        self.assertIsNotNone(client)
        self.assertIsInstance(client, LlmClient)
        self.assertEqual(client.host_name, "http://127.0.0.1:8000")

    @patch("classes.llm_client.requests.post", side_effect=llm_success)
    def test_llm_client_call_success(self, mock_post):
        """Happy path: provider answers straight away, response is not marked as failed."""
        client = LlmClient("Active", make_config())

        response = asyncio.run(client.call_llm("Hello, how are you?", "classify"))

        self.assertIsInstance(response, LlmResponse)
        self.assertFalse(response.is_failed)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.response, {"result": "ok"})
        self.assertEqual(response.operation, "classify")
        mock_post.assert_called_once()

    @patch("classes.llm_client.asyncio.sleep", return_value=None)
    @patch("classes.llm_client.requests.post", side_effect=llm_down)
    def test_llm_client_call_failure_retries_then_fails(self, mock_post, mock_sleep):
        """Provider keeps failing: client retries twice before giving up."""
        client = LlmClient("Active", make_config())

        response = asyncio.run(client.call_llm("Hello", "summarize"))

        self.assertIsInstance(response, LlmResponse)
        self.assertTrue(response.is_failed)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.operation, "summarize")
        # 1 initial attempt + 2 retries
        self.assertEqual(mock_post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
