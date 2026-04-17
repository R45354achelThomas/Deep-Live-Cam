import cv2
import insightface
import threading
from typing import Any, List, Optional
import modules.globals as globals

NAME = 'DLC.FACE-SWAPPER'

face_analyser = None
face_swapper = None
thread_lock = threading.Lock()


def pre_check() -> bool:
    """Check that required models are available."""
    from modules.core import resolve_relative_path
    import os

    model_path = resolve_relative_path('../../models/inswapper_128.onnx')
    if not os.path.exists(model_path):
        print(f'[{NAME}] Model not found at {model_path}. Please download inswapper_128.onnx.')
        return False
    return True


def pre_start() -> bool:
    """Validate source and target before processing."""
    from modules.core import is_image

    if not globals.source_path or not is_image(globals.source_path):
        print(f'[{NAME}] No valid source image selected.')
        return False
    if not globals.target_path:
        print(f'[{NAME}] No target selected.')
        return False
    return True


def get_face_analyser() -> Any:
    """Lazy-load and return the face analyser (thread-safe)."""
    global face_analyser
    with thread_lock:
        if face_analyser is None:
            face_analyser = insightface.app.FaceAnalysis(name='buffalo_l',
                                                         providers=globals.execution_providers)
            face_analyser.prepare(ctx_id=0, det_size=(640, 640))
    return face_analyser


def get_face_swapper() -> Any:
    """Lazy-load and return the face swapper model (thread-safe)."""
    global face_swapper
    with thread_lock:
        if face_swapper is None:
            from modules.core import resolve_relative_path
            model_path = resolve_relative_path('../../models/inswapper_128.onnx')
            face_swapper = insightface.model_zoo.get_model(model_path,
                                                           providers=globals.execution_providers)
    return face_swapper


def get_one_face(frame: Any) -> Optional[Any]:
    """Detect and return the most prominent face in a frame."""
    faces = get_face_analyser().get(frame)
    if faces:
        # Return face with largest bounding box area
        return max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return None


def get_many_faces(frame: Any) -> List[Any]:
    """Detect and return all faces in a frame."""
    faces = get_face_analyser().get(frame)
    return faces or []


def swap_face(source_face: Any, target_face: Any, frame: Any) -> Any:
    """Swap source face onto target face in the given frame."""
    return get_face_swapper().get(frame, target_face, source_face, paste_back=True)


def process_frame(source_face: Any, frame: Any) -> Any:
    """Process a single frame, swapping all detected faces with the source face."""
    if globals.many_faces:
        target_faces = get_many_faces(frame)
        for target_face in target_faces:
            frame = swap_face(source_face, target_face, frame)
    else:
        target_face = get_one_face(frame)
        if target_face:
            frame = swap_face(source_face, target_face, frame)
    return frame


def process_frames(source_path: str, frame_paths: List[str], progress: Any = None) -> None:
    """Process a list of frame image files, performing face swap on each."""
    source_frame = cv2.imread(source_path)
    source_face = get_one_face(source_frame)
    if not source_face:
        print(f'[{NAME}] No face detected in source image.')
        return
    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        result = process_frame(source_face, frame)
        cv2.imwrite(frame_path, result)
        if progress:
            progress.update(1)


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    """Perform face swap on a single image and save the result."""
    source_frame = cv2.imread(source_path)
    source_face = get_one_face(source_frame)
    if not source_face:
        print(f'[{NAME}] No face detected in source image.')
        return
    target_frame = cv2.imread(target_path)
    result = process_frame(source_face, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, frame_paths: List[str], progress: Any = None) -> None:
    """Alias for process_frames, used when the target is a video."""
    process_frames(source_path, frame_paths, progress)
