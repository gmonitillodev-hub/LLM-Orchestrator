from enum import Enum
from nturl2path import pathname2url
from typing import Self, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from utils.file_handler import check_folder, ProcessedPath


class OperationEnum(str, Enum):
    CLASSIFY = "classify"
    SUMMARIZE = "summarize"
    KEYWORD_EXTRACTION = "keyword-extraction"


class FileData(BaseModel):
    path: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class Request(BaseModel):
    request_id: UUID = Field(default_factory=uuid4)
    file_path: str = Field(..., min_length=1)
    file_data: List[ProcessedPath] = Field(default_factory=list)
    operation_type: OperationEnum | None = Field(None)

    @model_validator(mode="after")
    def validate(self: Self) -> Self:
        """ Here we validate the exitance of the file / folder """
        """if self.file_path == "/.":
            raise ValueError("Invalid file path")"""

        try:
            check_result = check_folder(self.file_path)
            for checked_file in check_result:
                self.file_data.append(checked_file)
        except Exception as e:
            print(f"        Check error -> {e}")
        return self
