import argparse
import asyncio

from classes.orchestrator import Orchestrator
from utils.terminal import clear_terminal, print_info

CLIENT_CHOICES = ("Active", "Inactive", "Partial")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="orchestrator", description="LLM Orchestrator")

    parser.add_argument(
        "--client",
        required=False,
        default="Active",
        choices=CLIENT_CHOICES,
        help="LLM client type to use (Active, Inactive, Partial)"
    )

    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=None,
        help="Maximum number of files processed concurrently (overrides config.ini)"
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    clear_terminal()
    print_info()

    orchestrator = Orchestrator(args.client, args.max_concurrency)
    orchestrator.initialize_request_processor()
    await orchestrator.process_requests()

    orchestrator.publish_processing_result()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
