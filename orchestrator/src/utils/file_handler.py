from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

@dataclass(slots=True)
class Error:
    detail: str
    status_code: int

@dataclass(slots=True)
class ProcessingResult:
    is_failed: bool = field(default=False)
    errors: List[Error] = field(default_factory=list)
    response: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ProcessedPath:
    file_path: str
    file_name: str
    processing_results: Optional[ProcessingResult] = None


def check_folder(folder_path: str | Path) -> list["ProcessedPath"]:
    path = Path(folder_path)

    if path.is_file():
        return [
            ProcessedPath(
                file_path=str(path),
                file_name=path.name
            )
        ]

    elif path.is_dir():
        processed_paths: list[ProcessedPath] = []

        documents = [item for item in path.iterdir() if item.is_file()]
        for document in documents:
            processed_paths.append(
                ProcessedPath(
                    file_path=str(document),
                    file_name=document.name
                )
            )

        return processed_paths
    else:
        raise FileNotFoundError("Path inesistente o non valido")


def read_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()
