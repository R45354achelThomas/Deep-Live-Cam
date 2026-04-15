#!/usr/bin/env python3
"""Deep-Live-Cam: Real-time face swapping and deepfake application.

This is the main entry point for the Deep-Live-Cam application.
It handles argument parsing, module initialization, and launching
either the GUI or headless processing mode.
"""

import sys
import os
import argparse
import platform
from pathlib import Path

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for Deep-Live-Cam."""
    parser = argparse.ArgumentParser(
        description="Deep-Live-Cam: Real-time face swap and deepfake tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input/output options
    parser.add_argument(
        "-s", "--source",
        type=str,
        default=None,
        help="Path to the source face image",
    )
    parser.add_argument(
        "-t", "--target",
        type=str,
        default=None,
        help="Path to the target image or video file",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Path to save the output file",
    )

    # Processing options
    parser.add_argument(
        "--frame-processor",
        type=str,
        nargs="+",
        default=["face_swapper"],
        choices=["face_swapper", "face_enhancer"],
        help="Frame processors to apply (can specify multiple)",
    )
    parser.add_argument(
        "--keep-fps",
        action="store_true",
        default=False,
        help="Preserve original frames per second of target video",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        default=True,
        help="Preserve audio from target video",
    )
    parser.add_argument(
        "--keep-frames",
        action="store_true",
        default=False,
        help="Keep temporary extracted frames after processing",
    )
    parser.add_argument(
        "--many-faces",
        action="store_true",
        default=False,
        help="Process all detected faces instead of only the first",
    )

    # Execution options
    parser.add_argument(
        "--execution-provider",
        type=str,
        nargs="+",
        default=["cpu"],
        choices=["cpu", "cuda", "coreml", "directml", "openvino"],
        help="Execution provider(s) for inference",
    )
    parser.add_argument(
        "--execution-threads",
        type=int,
        default=4,
        help="Number of threads for parallel frame processing",
    )

    # UI options
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run without GUI (requires --source, --target, and --output)",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        choices=["en", "de", "es"],
        help="UI language",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging verbosity level",
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> bool:
    """Validate parsed arguments for consistency.

    Returns True if arguments are valid, False otherwise.
    """
    if args.headless:
        missing = []
        if not args.source:
            missing.append("--source")
        if not args.target:
            missing.append("--target")
        if not args.output:
            missing.append("--output")
        if missing:
            print(f"[ERROR] Headless mode requires: {', '.join(missing)}")
            return False

        if args.source and not Path(args.source).is_file():
            print(f"[ERROR] Source file not found: {args.source}")
            return False
        if args.target and not Path(args.target).is_file():
            print(f"[ERROR] Target file not found: {args.target}")
            return False

    return True


def main() -> None:
    """Main entry point for Deep-Live-Cam."""
    args = parse_args()

    if not validate_args(args):
        sys.exit(1)

    print(f"Deep-Live-Cam starting on {platform.system()} "
          f"(Python {platform.python_version()})")
    print(f"Execution provider(s): {', '.join(args.execution_provider)}")
    print(f"Frame processor(s): {', '.join(args.frame_processor)}")

    if args.headless:
        print("Running in headless mode...")
        # TODO: import and call core processing pipeline
    else:
        print("Launching GUI...")
        # TODO: import and launch GUI module


if __name__ == "__main__":
    main()
