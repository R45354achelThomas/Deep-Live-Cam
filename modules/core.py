import os
import sys
import threading
from typing import Any, Callable, List, Optional

import modules.globals
from modules.typing import Frame

# Supported file extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.gif')


def has_image_extension(filepath: str) -> bool:
    """Check if a file path has a supported image extension."""
    return filepath.lower().endswith(IMAGE_EXTENSIONS)


def has_video_extension(filepath: str) -> bool:
    """Check if a file path has a supported video extension."""
    return filepath.lower().endswith(VIDEO_EXTENSIONS)


def is_image(filepath: str) -> bool:
    """Verify that the path points to an existing image file."""
    if filepath and os.path.isfile(filepath):
        return has_image_extension(filepath)
    return False


def is_video(filepath: str) -> bool:
    """Verify that the path points to an existing video file."""
    if filepath and os.path.isfile(filepath):
        return has_video_extension(filepath)
    return False


def resolve_relative_path(path: str) -> str:
    """Resolve a path relative to the project root directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', path))


def get_temp_directory_path(target_path: str) -> str:
    """Return the temporary directory path for processing a given target file."""
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    target_directory_path = os.path.dirname(target_path)
    return os.path.join(target_directory_path, target_name + '_temp')


def create_temp(target_path: str) -> None:
    """Create a temporary directory for processing frames."""
    temp_directory_path = get_temp_directory_path(target_path)
    Path(temp_directory_path).mkdir(parents=True, exist_ok=True)


def move_temp(target_path: str, output_path: str) -> None:
    """Move the processed temporary file to the final output path."""
    temp_output_path = get_temp_output_path(target_path)
    if os.path.isfile(temp_output_path):
        if os.path.isfile(output_path):
            os.remove(output_path)
        os.rename(temp_output_path, output_path)


def get_temp_output_path(target_path: str) -> str:
    """Return the path for the temporary output file."""
    temp_directory_path = get_temp_directory_path(target_path)
    target_name, _ = os.path.splitext(os.path.basename(target_path))
    return os.path.join(temp_directory_path, target_name + '.mp4')


def clean_temp(target_path: str) -> None:
    """Remove the temporary directory used during processing."""
    import shutil
    temp_directory_path = get_temp_directory_path(target_path)
    if not modules.globals.keep_frames and os.path.isdir(temp_directory_path):
        shutil.rmtree(temp_directory_path)
    elif os.path.isfile(get_temp_output_path(target_path)):
        os.remove(get_temp_output_path(target_path))


def get_frame_processors_modules(frame_processors: List[str]) -> List[Any]:
    """Dynamically load and return frame processor modules by name."""
    import importlib
    loaded_processors = []
    for frame_processor in frame_processors:
        module_path = f'modules.processors.frame.{frame_processor}'
        try:
            module = importlib.import_module(module_path)
            loaded_processors.append(module)
        except ImportError as e:
            sys.exit(f'[ERROR] Failed to load frame processor "{frame_processor}": {e}')
    return loaded_processors


def limit_resources() -> None:
    """Apply memory and CPU limits based on global configuration."""
    if modules.globals.max_memory:
        memory = modules.globals.max_memory * 1024 ** 3
        if sys.platform == 'darwin':
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))
        elif sys.platform == 'linux':
            import resource
            resource.setrlimit(resource.RLIMIT_DATA, (memory, memory))


def pre_check() -> bool:
    """Run pre-flight checks before processing begins."""
    if sys.version_info < (3, 9):
        print('[ERROR] Python 3.9 or higher is required.')
        return False
    if not os.path.exists(resolve_relative_path('models')):
        os.makedirs(resolve_relative_path('models'), exist_ok=True)
    return True


def conditional_process_video(
    source_path: str,
    target_path: str,
    process_frames: Callable[[str, List[str], Any], None]
) -> None:
    """Process a video file using multi-threading if configured."""
    import cv2
    from tqdm import tqdm

    capture = cv2.VideoCapture(target_path)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()

    temp_directory_path = get_temp_directory_path(target_path)
    frame_paths = [
        os.path.join(temp_directory_path, f'{str(i).zfill(6)}.png')
        for i in range(frame_count)
    ]

    progress = tqdm(total=frame_count, desc='Processing', unit='frame', dynamic_ncols=True)

    def update_progress(_future: Any) -> None:
        progress.update(1)

    with threading.Semaphore(modules.globals.execution_threads):
        threads = []
        for frame_path in frame_paths:
            thread = threading.Thread(
                target=process_frames,
                args=(source_path, [frame_path], None)
            )
            thread.start()
            thread.join = lambda t=thread: (t, update_progress(None))
            threads.append(thread)
        for t in threads:
            t.join()

    progress.close()


try:
    from pathlib import Path
except ImportError:
    sys.exit('[ERROR] pathlib is required. Please install it.')
