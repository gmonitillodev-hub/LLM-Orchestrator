import configparser
import os


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def print_info():
    print("\n ------------------------------------------------------- ")
    print(" ------------------ LLM Orchestrator -------------------")
    print(" ----- Process your document in few simple steps -------")
    print(" - Insert the path of one or more documents or folders -")
    print(" ------------------------------------------------------- ")


def to_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes", "y")


def get_config():
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(src_dir, "config", "config.ini")

    config = configparser.ConfigParser()
    if not config.read(filenames=config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    return config
