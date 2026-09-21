import asyncio
import threading
import time
from pathlib import Path

from pandas import DataFrame

from classes import Request, OperationEnum, LlmClient, setup_logger
from orchestrator.request_processor import accept_new_request, ask_new_request
from utils.file_handler import read_text_file, ProcessedPath, ProcessingResult, Error
from utils.terminal import clear_terminal, to_bool, get_config, print_info


class Orchestrator:

    def __init__(self, client: str, max_concurrency: int | None = None) -> None:

        """ Initialize the Orchestrator class"""

        """ Read the configuration file """
        self.config = get_config()

        """ Initialize needed variables """
        self.requests = list[Request]()
        self.file_to_process = list[ProcessedPath]()
        self.MAX_CONCURRENCY = int(self.config.get("General", "MAX_CONCURRENCY"))
        if max_concurrency:
            self.MAX_CONCURRENCY = int(max_concurrency)

        """ Initialize client and logger """
        self.llm_client = LlmClient(client, self.config)
        self.logger = setup_logger(to_bool(self.config.get("General", "debug_mode")))

    """ Collect requests from the user """

    def initialize_request_processor(self) -> None:

        self.logger.info("Initializing Request Processor")

        need_request = True
        while need_request:
            new_request = accept_new_request()
            need_request = ask_new_request()
            self.requests.append(new_request)

            clear_terminal()
            print_info()

        self.file_to_process.extend(
            processed_path
            for request in self.requests
            for processed_path in request.file_data
        )

        self.logger.info(f"{len(self.requests)} requests to be processed for {len(self.file_to_process)} files")

    """ Process a single file with all needed operations """

    async def process_file(self, file):

        print_lock = threading.Lock()

        self.logger.info(f"Processing {file.file_name}")

        content = read_text_file(file.file_path)
        inference_results = await self.inference_request(content)

        processing_result = ProcessingResult(is_failed=False)
        file.processing_results = processing_result

        self.logger.info(f"{file.file_name} processed")

        for result in inference_results:

            if result.is_failed:

                self.logger.error(f"[{file.file_name}] Processing {result.operation} failed")

                processing_result.is_failed = True

                error = Error(
                    detail=f"Failed operation {result.operation} - Details: {result.response}",
                    status_code=result.status_code
                )
                processing_result.errors.append(error)

            else:
                processing_result.response.append(
                    f"Operation {result.operation} successful - Response: {result.response}"
                )

        with print_lock:
            print(f" File {file.file_name} processed")

    """ Sync call to process file, useful to run It properly in threads """

    def _process_file_sync(self, file, semaphore: threading.Semaphore) -> None:
        with semaphore:
            asyncio.run(self.process_file(file))

    """ Process all requests with threads """

    async def process_requests(self):

        clear_terminal()
        print(f" ------ File processing started ------ ")

        semaphore = threading.Semaphore(self.MAX_CONCURRENCY)
        threads = list()
        for file in self.file_to_process:
            thread = threading.Thread(
                target=self._process_file_sync,
                args=(file, semaphore),
                name=f"Th-{file.file_name}"
            )

            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    async def inference_request(self, content: str):

        promises = list()

        for operation in OperationEnum:

            operation_prompt: str

            match operation:
                case OperationEnum.CLASSIFY:
                    operation_prompt = (
                        "Classify the provided content into its most appropriate category. "
                        "Return only the category name and a brief justification."
                    )

                case OperationEnum.SUMMARIZE:
                    operation_prompt = (
                        "Provide a simple, concise summary of the provided content."
                    )

                case OperationEnum.KEYWORD_EXTRACTION:
                    operation_prompt = (
                        "Extract the most relevant keywords and key phrases from the provided "
                        "content. Return a concise, comma-separated list without explanations."
                    )

                case _:
                    self.logger.error(f"Unknown operation {operation}")

            promises.append(self.llm_client.call_llm(f"{operation_prompt} - Content: << {content} >>", operation.value))

        try:

            self.logger.info(f"Waiting {len(promises)} promises")
            return await asyncio.gather(*promises)

        except Exception as e:

            self.logger.error(e)
            raise e

    """ Save files to view processing results """

    def publish_processing_result(self) -> None:

        clear_terminal()

        message = f" Publishing processing results for {len(self.file_to_process)} files"
        self.logger.info(message)
        print("\n " + message)

        processing_failed = filter(lambda x: x.processing_results.is_failed, self.file_to_process)

        l1 = list()
        l2 = list()
        l3 = list()
        l4 = list()

        for file in processing_failed:

            processing_result = file.processing_results
            for error in processing_result.errors:
                l1.append(file.file_name)
                l2.append(file.file_path)
                l3.append(error.status_code)
                l4.append(error.detail)

        df = DataFrame({
            "File name": l1,
            "File path": l2,
            "Error code": l3,
            "Error detail": l4
        })

        timestamp = time.strftime("%Y%m%d-%H%M%S")

        output_dir = Path.home() / "LLM_Orchestrator_result" / "failed"
        output_dir.mkdir(parents=True, exist_ok=True)

        df.to_excel(
            output_dir / f"processing_error_{timestamp}.xlsx",
        )

        self.logger.info(f"Error file created for {len(list(processing_failed))}")

        properly_processed = [f for f in self.file_to_process if f.processing_results.is_failed == False]

        df = DataFrame({
            "File name": list(map(lambda f: f.file_name, properly_processed)),
            "File path": list(map(lambda f: f.file_path, properly_processed)),
        })

        output_dir = Path.home() / "LLM_Orchestrator_result" / "success"
        output_dir.mkdir(parents=True, exist_ok=True)

        df.to_excel(
            output_dir / f"processing_success_{timestamp}.xlsx",
        )

        self.logger.info(f"Success file created for {len(properly_processed)}")
        print(f"  Results published. Open {output_dir} to view the results")
