import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from classes.request import Request, OperationEnum


class TestRequestInitialization(unittest.TestCase):
    def setUp(self):
        # Simulate a user's working folder with a real document to process
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

        self.tmp_path = Path(self.tmp_dir.name)
        self.file_path = self.tmp_path / "document.txt"
        self.file_path.write_text("content")

    def test_request_with_valid_file_populates_file_data(self):
        """Pointing to an existing file: the request must find it and prepare it for processing."""
        request = Request(file_path=str(self.file_path))

        self.assertIsInstance(request.request_id, UUID)
        self.assertEqual(request.file_path, str(self.file_path))
        self.assertEqual(len(request.file_data), 1)
        self.assertEqual(request.file_data[0].file_path, str(self.file_path))
        self.assertEqual(request.file_data[0].file_name, "document.txt")

    def test_request_with_valid_folder_populates_all_files(self):
        """Pointing to a folder: every file inside it must be picked up."""
        (self.tmp_path / "other.txt").write_text("content")

        request = Request(file_path=str(self.tmp_path))

        file_names = sorted(f.file_name for f in request.file_data)
        self.assertEqual(file_names, ["document.txt", "other.txt"])

    def test_request_with_nonexistent_path_keeps_empty_file_data(self):
        """A wrong path must not crash the app: file_data simply stays empty."""
        # check_folder raises FileNotFoundError, which the validator catches and logs
        request = Request(file_path=str(self.tmp_path / "missing"))

        self.assertEqual(request.file_data, [])

    def test_request_with_empty_file_path_raises_validation_error(self):
        """An empty path is invalid input and must be rejected upfront."""
        with self.assertRaises(ValidationError):
            Request(file_path="")

    def test_request_requires_file_path(self):
        """The file path is mandatory: without it the request makes no sense."""
        with self.assertRaises(ValidationError):
            Request()

    def test_request_default_operation_type_is_none(self):
        """If the user doesn't pick an operation, it stays undecided (None)."""
        request = Request(file_path=str(self.file_path))
        self.assertIsNone(request.operation_type)

    def test_request_accepts_valid_operation_type(self):
        """A user can explicitly request a valid operation, e.g. classification."""
        request = Request(file_path=str(self.file_path), operation_type=OperationEnum.CLASSIFY)
        self.assertEqual(request.operation_type, OperationEnum.CLASSIFY)

    def test_request_rejects_invalid_operation_type(self):
        """An unsupported/made-up operation must be rejected."""
        with self.assertRaises(ValidationError):
            Request(file_path=str(self.file_path), operation_type="not-a-valid-operation")

    def test_request_id_is_unique_per_instance(self):
        """Even sending the same file twice, each request must remain individually traceable."""
        first = Request(file_path=str(self.file_path))
        second = Request(file_path=str(self.file_path))
        self.assertNotEqual(first.request_id, second.request_id)


if __name__ == "__main__":
    unittest.main()
