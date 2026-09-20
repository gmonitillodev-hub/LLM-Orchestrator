import logging
from pathlib import Path

LOG_DIR = Path("log")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger(enable_console=False) -> logging.Logger:
    logger = logging.getLogger("orchestrator_logger")
    logger.setLevel(logging.DEBUG)

    error_file_handler = logging.FileHandler(LOG_DIR / "error_orchestrator_logger.log")
    error_file_handler.setLevel(logging.ERROR)

    info_file_handler = logging.FileHandler(LOG_DIR / "info_orchestrator_logger.log")
    info_file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formator = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_file_handler.setFormatter(formator)
    info_file_handler.setFormatter(formator)
    console_handler.setFormatter(logging.Formatter('\n %(asctime)s - %(levelname)s - %(message)s \n'))

    logger.addHandler(error_file_handler)
    logger.addHandler(info_file_handler)

    if enable_console:
        logger.addHandler(console_handler)

    return logger


def setup_client_logger(enable_console=False) -> logging.Logger:
    logger = logging.getLogger("orchestrator_client_logger")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_file_handler = logging.FileHandler(LOG_DIR / "orchestrator_client_logger.log")
    error_file_handler.setLevel(logging.DEBUG)
    error_file_handler.setFormatter(formatter)

    logger.addHandler(error_file_handler)

    return logger
