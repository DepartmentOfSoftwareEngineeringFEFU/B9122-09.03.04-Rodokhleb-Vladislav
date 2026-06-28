import cv2
from typing import List, Tuple, Generator, Optional
import numpy as np


class FrameExtractor:

    def __init__(self, target_fps: int = 2):
        self.target_fps = target_fps

    def extract(self, video_path: str, progress_callback: Optional[callable] = None) -> Tuple[List[Tuple[float, np.ndarray]], float, int, float]:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames_count / fps if fps > 0 else 0

        frame_step = max(1, int(fps / self.target_fps))

        print(f"Video FPS: {fps:.2f}")
        print(f"Target FPS: {self.target_fps}")
        print(f"Frame step: {frame_step}")

        frames = []
        frame_idx = 0
        processed_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                timestamp = frame_idx / fps
                frames.append((timestamp, frame.copy()))
                processed_frames += 1

                if processed_frames % 100 == 0:
                    print(f"Extracted {processed_frames} frames...")
                    if progress_callback:
                        progress_callback(min(0.1, processed_frames / (total_frames_count / frame_step) * 0.1))

            frame_idx += 1

        cap.release()
        print(f"Extracted {len(frames)} frames from {total_frames_count} total frames")

        return frames, duration, total_frames_count, fps

    def extract_frames_generator(self, video_path: str) -> Generator[Tuple[float, np.ndarray], None, None]:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_step = max(1, int(fps / self.target_fps))

        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                timestamp = frame_idx / fps
                yield (timestamp, frame)

            frame_idx += 1

        cap.release()

    def extract_at_timestamp(self, video_path: str, timestamp: float) -> np.ndarray:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError(f"Cannot extract frame at timestamp {timestamp}")

        return frame

    def get_preview_frame(self, video_path: str, timestamp: float, max_width: int = 320) -> bytes:
        frame = self.extract_at_timestamp(video_path, timestamp)

        height, width = frame.shape[:2]
        if width > max_width:
            scale = max_width / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))

        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

    def get_video_info(self, video_path: str) -> dict:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames_count / fps if fps > 0 else 0

        cap.release()

        return {
            "fps": fps,
            "total_frames": total_frames_count,
            "width": width,
            "height": height,
            "duration": duration
        }

    def extract_at_frame(self, video_path: str, frame_number: int) -> np.ndarray:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError(f"Cannot extract frame at frame number {frame_number}")

        return frame

    def get_preview_frame_by_frame(self, video_path: str, frame_number: int, max_width: int = 320) -> bytes:
        frame = self.extract_at_frame(video_path, frame_number)

        height, width = frame.shape[:2]
        if width > max_width:
            scale = max_width / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))

        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()