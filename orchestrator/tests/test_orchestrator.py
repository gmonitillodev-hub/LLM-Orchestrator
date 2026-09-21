import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pandas as pd

from classes.llm_client import LlmClient, LlmResponse
from classes.orchestrator import Orchestrator
from utils.file_handler import Error, ProcessedPath, ProcessingResult


def make_llm_side_effect(fail_operation: str | None = None):
    """Async side_effect for LlmClient.call_llm.

    All operations succeed unless their name matches `fail_operation`.
    """

    async def side_effect(content, operation, retry=0):
        if operation == fail_operation:
            return LlmResponse(is_failed=True, status_code=500, response={"error": "boom"}, operation=operation)
        return LlmResponse(is_failed=False, status_code=200, response={"result": operation}, operation=operation)

    return side_effect


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.model = "Active"
        LlmClient._instances = {}

    def test_orchestrator_initialization(self):
        orchestrator = Orchestrator(self.model, 2)
        self.assertIsNotNone(orchestrator)
        self.assertEqual(orchestrator.MAX_CONCURRENCY, 2)
        self.assertEqual(orchestrator.logger.name, "orchestrator_logger")

    @patch("classes.orchestrator.clear_terminal")
    @patch("classes.orchestrator.print_info")
    @patch("builtins.input")
    def test_orchestrator_requests_with_valid_input(self, mock_input, mock_print_info, mock_clear_terminal):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "document.txt"
            file_path.write_text("content")

            # Valid file path on the first try, then decline further requests
            mock_input.side_effect = [str(file_path), "n"]

            orchestrator = Orchestrator(self.model, 2)
            orchestrator.initialize_request_processor()

            self.assertEqual(len(orchestrator.requests), 1)
            self.assertEqual(len(orchestrator.file_to_process), 1)
            self.assertEqual(orchestrator.file_to_process[0].file_name, "document.txt")

    @patch("classes.orchestrator.clear_terminal")
    @patch("classes.orchestrator.print_info")
    @patch("builtins.input")
    def test_orchestrator_requests_retries_on_invalid_file_path(self, mock_input, mock_print_info, mock_clear_terminal):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "document.txt"
            file_path.write_text("content")

            # Empty file path is invalid (min_length=1) and triggers a retry
            # before a valid path is finally provided
            mock_input.side_effect = ["", str(file_path), "n"]

            orchestrator = Orchestrator(self.model, 2)
            orchestrator.initialize_request_processor()

            self.assertEqual(len(orchestrator.requests), 1)
            self.assertEqual(len(orchestrator.file_to_process), 1)
            self.assertEqual(orchestrator.file_to_process[0].file_name, "document.txt")

    @patch("classes.orchestrator.clear_terminal")
    @patch("classes.orchestrator.print_info")
    @patch("builtins.input")
    def test_orchestrator_requests_reprompts_on_invalid_confirmation(self, mock_input, mock_print_info, mock_clear_terminal):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "document.txt"
            file_path.write_text("content")

            # "maybe" is neither "y" nor "n": ask_new_request must reprompt
            mock_input.side_effect = [str(file_path), "maybe", "n"]

            orchestrator = Orchestrator(self.model, 2)
            orchestrator.initialize_request_processor()

            self.assertEqual(len(orchestrator.requests), 1)
            self.assertEqual(mock_input.call_count, 3)


class TestOrchestratorProcessRequests(unittest.TestCase):
    def setUp(self):
        LlmClient._instances = {}
        self.orchestrator = Orchestrator("Active", 2)
        self.file_a = ProcessedPath(file_path="a.txt", file_name="a.txt")
        self.file_b = ProcessedPath(file_path="b.txt", file_name="b.txt")
        self.orchestrator.file_to_process = [self.file_a, self.file_b]

    @patch("classes.orchestrator.clear_terminal")
    @patch("classes.orchestrator.read_text_file", return_value="dummy content")
    def test_process_requests_marks_all_files_successful(self, mock_read_text_file, mock_clear_terminal):
        self.orchestrator.llm_client.call_llm = AsyncMock(side_effect=make_llm_side_effect())

        asyncio.run(self.orchestrator.process_requests())

        for file in (self.file_a, self.file_b):
            self.assertIsNotNone(file.processing_results)
            self.assertFalse(file.processing_results.is_failed)
            self.assertEqual(len(file.processing_results.response), 3)
            self.assertEqual(len(file.processing_results.errors), 0)

        mock_read_text_file.assert_called()

    @patch("classes.orchestrator.clear_terminal")
    @patch("classes.orchestrator.read_text_file", return_value="dummy content")
    def test_process_requests_marks_file_failed_on_llm_error(self, mock_read_text_file, mock_clear_terminal):
        self.orchestrator.llm_client.call_llm = AsyncMock(side_effect=make_llm_side_effect(fail_operation="summarize"))

        asyncio.run(self.orchestrator.process_requests())

        for file in (self.file_a, self.file_b):
            self.assertIsNotNone(file.processing_results)
            self.assertTrue(file.processing_results.is_failed)
            self.assertEqual(len(file.processing_results.errors), 1)
            self.assertEqual(file.processing_results.errors[0].status_code, 500)
            self.assertEqual(len(file.processing_results.response), 2)


class TestOrchestratorPublishProcessingResult(unittest.TestCase):
    def setUp(self):
        LlmClient._instances = {}
        self.orchestrator = Orchestrator("Active", 2)

        success_file = ProcessedPath(file_path="ok.txt", file_name="ok.txt")
        success_file.processing_results = ProcessingResult(is_failed=False, response=["Operation classify successful"])

        failed_file = ProcessedPath(file_path="bad.txt", file_name="bad.txt")
        failed_file.processing_results = ProcessingResult(
            is_failed=True,
            errors=[Error(detail="Failed operation summarize - Details: boom", status_code=500)],
        )

        self.orchestrator.file_to_process = [success_file, failed_file]

    @patch("classes.orchestrator.clear_terminal")
    def test_publish_processing_result_writes_success_and_failed_files(self, mock_clear_terminal):
        with patch("pathlib.Path.home") as mock_home:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Redirect the user's "home" to a temp dir so we don't pollute the real one
                mock_home.return_value = Path(tmp_dir)

                self.orchestrator.publish_processing_result()

                result_dir = Path(tmp_dir) / "LLM Orchestrator result"

                success_files = list((result_dir / "success").glob("processing_success_*.xlsx"))
                failed_files = list((result_dir / "failed").glob("processing_error_*.xlsx"))

                self.assertEqual(len(success_files), 1)
                self.assertEqual(len(failed_files), 1)

                success_df = pd.read_excel(success_files[0])
                self.assertEqual(list(success_df["File name"]), ["ok.txt"])

                failed_df = pd.read_excel(failed_files[0])
                self.assertEqual(list(failed_df["File name"]), ["bad.txt"])
                self.assertEqual(list(failed_df["Error code"]), [500])


if __name__ == "__main__":
    unittest.main()
