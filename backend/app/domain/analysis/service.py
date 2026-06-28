from typing import List, Optional, Dict, Any
import cv2
import numpy as np
from pathlib import Path
import tempfile
import os
import re
from functools import lru_cache

from .frame_extractor import FrameExtractor
from .classifier_model import ClassifierModel
from .segmenter import Segmenter
from .models import FrameAnalysis, AnalysisResult, Fragment as AnalysisFragment, Detection
from ...config import settings
from ...shared.minio_client import minio_client


class TextProcessor:

    def __init__(self, use_cache: bool = True, add_article: bool = True):
        self.use_cache = use_cache
        self.add_article = add_article
        self._translator = None
        self._translator_type = None
        self._init_translator()

    def _init_translator(self):
        try:
            from deep_translator import GoogleTranslator
            self._translator = GoogleTranslator(source='ru', target='en')
            self._translator_type = 'deep-translator'
            print("Инициализирован переводчик deep-translator")
            return
        except ImportError:
            pass

        try:
            from googletrans import Translator
            self._translator = Translator()
            self._translator_type = 'googletrans'
            print("Инициализирован переводчик googletrans")
        except ImportError:
            print("Переводчики не установлены. Будет использован fallback-режим.")
            self._translator = None
            self._translator_type = 'none'

    def is_english(self, text: str) -> bool:
        if not text:
            return True
        return not bool(re.search('[а-яА-ЯёЁ]', text))

    def _add_article(self, text: str) -> str:
        if not self.add_article:
            return text

        text = text.strip().lower()

        if not text:
            return text

        first_word = text.split()[0] if ' ' in text else text

        if first_word in ['a', 'an', 'the']:
            return text

        if ' ' in text:
            return text

        return f"a {text}"

    async def _translate_async(self, text: str) -> str:
        if self._translator_type == 'googletrans':
            result = await self._translator.translate(text, src='ru', dest='en')
            return result.text
        return text

    @lru_cache(maxsize=1000)
    def _translate_cached(self, text: str) -> str:
        if self._translator is None:
            return text

        try:
            if self._translator_type == 'deep-translator':
                translated = self._translator.translate(text)
            elif self._translator_type == 'googletrans':
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                translated = loop.run_until_complete(self._translate_async(text))
                loop.close()
            else:
                return text

            return self._add_article(translated)
        except Exception as e:
            print(f"Ошибка перевода '{text}': {e}")
            return text

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return text

        if self.is_english(text):
            return self._add_article(text.lower().strip())

        if self.use_cache:
            return self._translate_cached(text.strip())
        else:
            if self._translator is None:
                return text
            try:
                if self._translator_type == 'deep-translator':
                    translated = self._translator.translate(text.strip())
                elif self._translator_type == 'googletrans':
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    translated = loop.run_until_complete(self._translate_async(text.strip()))
                    loop.close()
                else:
                    return text

                return self._add_article(translated)
            except Exception as e:
                print(f"Ошибка перевода '{text}': {e}")
                return text

    def translate_batch(self, texts: List[str]) -> List[str]:
        return [self.translate(t) for t in texts]

    def prepare_prompt(self, keyword: str) -> str:
        if not keyword or not keyword.strip():
            return keyword
        return self.translate(keyword)

    def prepare_prompts(self, keywords: List[str]) -> List[str]:
        return [self.prepare_prompt(kw) for kw in keywords]

    def prepare_for_detector(self, keywords: List[str]) -> List[str]:
        prepared = self.prepare_prompts(keywords)
        return [kw + '.' if not kw.endswith('.') else kw for kw in prepared]


class AnalysisService:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.text_processor = TextProcessor(add_article=True)
        self.frame_extractor = FrameExtractor(target_fps=settings.FRAMES_PER_SECOND)
        self.detector = ClassifierModel(
            confidence_threshold=settings.DETECTION_CONFIDENCE_THRESHOLD,
            verbose=verbose
        )
        self.segmenter = Segmenter(gap_threshold=settings.DEFAULT_GAP_THRESHOLD)

    def _download_video_from_minio(self, video_path_key: str) -> str:
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_path = temp_file.name
            temp_file.close()

            parts = video_path_key.split('/', 1)

            if self.verbose:
                print(f"Parsing video_path_key: {video_path_key}")
                print(f"Parts: {parts}")

            if len(parts) == 2:
                folder = parts[0]
                object_name = parts[1]
            else:
                folder = settings.MINIO_FOLDER_VIDEOS
                object_name = video_path_key

            if self.verbose:
                print(f"   Downloading from MinIO: bucket={settings.MINIO_BUCKET}, folder={folder}, object={object_name}")

            video_bytes = minio_client.download_file(
                object_name=object_name,
                folder=folder
            )

            with open(temp_path, 'wb') as f:
                f.write(video_bytes)

            if self.verbose:
                print(f"Video downloaded to: {temp_path}")

            return temp_path
        except Exception as e:
            print(f"Download error: {e}")
            raise Exception(f"Failed to download video from MinIO: {e}")

    def _cleanup_temp_file(self, temp_path: str):
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp file {temp_path}: {e}")

    def _save_fragment_to_minio(
        self,
        fragment_bytes: bytes,
        request_id: int,
        fragment_id: int,
        keyword: str
    ) -> str:
        object_name = f"request_{request_id}/fragment_{fragment_id}_{keyword.replace(' ', '_')}.mp4"
        try:
            full_key = minio_client.upload_file(
                file_data=fragment_bytes,
                object_name=object_name,
                folder=settings.MINIO_FOLDER_FRAGMENTS,
                content_type="video/mp4"
            )
            return full_key
        except Exception as e:
            print(f"Failed to save fragment to MinIO: {e}")
            return None

    def _extract_fragment_from_video(
            self,
            video_path: str,
            start_frame: int,
            end_frame: int
    ) -> bytes:
        import subprocess

        temp_output = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_output_path = temp_output.name
        temp_output.close()

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()

            start_time = start_frame / fps
            end_time = end_frame / fps
            duration = end_time - start_time

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',
                '-map', '0',
                '-y',
                temp_output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                with open(temp_output_path, 'rb') as f:
                    fragment_bytes = f.read()
                os.unlink(temp_output_path)
                return fragment_bytes
            else:
                raise Exception("ffmpeg failed, falling back to OpenCV")

        except (subprocess.SubprocessError, FileNotFoundError, Exception):
            print("Warning: ffmpeg not available, using OpenCV (audio will be lost)")

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_path = temp_file.name
            temp_file.close()

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

            frame_count = start_frame
            while frame_count <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frame_count += 1

            out.release()
            cap.release()

            with open(temp_path, 'rb') as f:
                fragment_bytes = f.read()

            os.unlink(temp_path)
            return fragment_bytes

    def analyze_video(
            self,
            video_path_key: str,
            keywords: List[str],
            fps: int = 2,
            confidence: float = 0.35,
            progress_callback: Optional[callable] = None,
            request_id: Optional[int] = None
    ) -> AnalysisResult:
        temp_video_path = None
        video_fps = 0

        try:
            original_keywords = keywords.copy()
            translated_keywords = self.text_processor.prepare_for_detector(keywords)

            if self.verbose and original_keywords != translated_keywords:
                print(f"\nПеревод ключевых слов:")
                for orig, trans in zip(original_keywords, translated_keywords):
                    print(f"   '{orig}' → '{trans}'")

            if progress_callback:
                progress_callback(0.05)

            if self.verbose:
                print(f"\nСтарт анализа видео")
                print(f"   Video key: {video_path_key}")
                print(f"   Original keywords: {original_keywords}")
                print(f"   Translated keywords: {translated_keywords}")
                print(f"   FPS: {fps}")

            self.frame_extractor = FrameExtractor(target_fps=fps)
            self.detector = ClassifierModel(
                confidence_threshold=confidence,
                verbose=self.verbose
            )

            temp_video_path = self._download_video_from_minio(video_path_key)

            if progress_callback:
                progress_callback(0.1)

            frames, duration, total_frames, original_fps = self.frame_extractor.extract(temp_video_path)
            video_fps = original_fps

            if self.verbose:
                print(f"\nExtracted {len(frames)} frames (target {fps} fps)")
                print(f"Video duration: {duration:.2f}s, Original FPS: {original_fps:.2f}")

            if not frames:
                return AnalysisResult(
                    fragments=[],
                    total_frames_analyzed=0,
                    duration=duration,
                    keywords_found=[],
                    with_detection=True
                )

            frame_analyses = []
            keywords_found_set = set()

            if self.verbose:
                print(f"\nAnalyzing frames:")

            for i, (timestamp, frame) in enumerate(frames):
                if progress_callback:
                    progress = 0.1 + (i / len(frames)) * 0.8
                    progress_callback(progress)

                frame_info = f"[{timestamp:5.2f}s]"

                detections = self.detector.detect(frame, translated_keywords, frame_info=frame_info)

                for det in detections:
                    clean_label = det.label.rstrip('.')
                    keywords_found_set.add(clean_label)

                frame_analyses.append(FrameAnalysis(
                    timestamp=timestamp,
                    frame_index=i,
                    detections=detections,
                    has_objects=len(detections) > 0
                ))

            if self.verbose:
                print(f"Total keywords found in video: {keywords_found_set}")

            if progress_callback:
                progress_callback(0.95)

            fragments = self.segmenter.segment(frame_analyses, with_detection=True)

            for idx, frag in enumerate(fragments):
                try:
                    if request_id:
                        try:
                            frame_step = original_fps / fps

                            start_frame_analysis = int(round(frag.start_time * fps))
                            end_frame_analysis = int(round(frag.end_time * fps))


                            start_frame_original = int(round(start_frame_analysis * frame_step))
                            end_frame_original = int(round(end_frame_analysis * frame_step))


                            start_frame_original = max(0, start_frame_original)
                            end_frame_original = min(total_frames, end_frame_original)

                            if self.verbose:
                                print(f"Fragment {idx + 1}: analysis frames {start_frame_analysis}-{end_frame_analysis}")
                                print(f"original frames {start_frame_original}-{end_frame_original}")
                                print(f"frame_step = {frame_step:.2f}")

                            fragment_bytes = self._extract_fragment_from_video(
                                temp_video_path,
                                start_frame_original,
                                end_frame_original
                            )
                            fragment_key = self._save_fragment_to_minio(
                                fragment_bytes,
                                request_id,
                                idx + 1,
                                frag.keyword
                            )
                            if fragment_key and self.verbose:
                                print(f"Fragment {idx + 1} saved to MinIO: {fragment_key}")

                            preview_frame_original = (start_frame_original + end_frame_original) // 2
                            preview_time = preview_frame_original / original_fps
                            preview_bytes = self.frame_extractor.get_preview_frame(temp_video_path, preview_time)
                            frag.preview_bytes = preview_bytes

                        except Exception as e:
                            if self.verbose:
                                print(f"Warning: Failed to save fragment {idx + 1}: {e}")
                except Exception as e:
                    if self.verbose:
                        print(f"Failed to process fragment {idx + 1}: {e}")

            if progress_callback:
                progress_callback(1.0)

            if self.verbose:
                print(f"\nАнализ завершен")
                print(f"Fragments found: {len(fragments)}")
                for frag in fragments:
                    print(f"  - {frag.keyword}: {frag.start_time:.2f}s - {frag.end_time:.2f}s")

            return AnalysisResult(
                fragments=fragments,
                total_frames_analyzed=len(frames),
                duration=duration,
                keywords_found=list(keywords_found_set),
                with_detection=True
            )

        finally:
            if temp_video_path:
                self._cleanup_temp_file(temp_video_path)

    def get_detections_list(
        self,
        video_path_key: str,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        temp_video_path = None

        try:
            temp_video_path = self._download_video_from_minio(video_path_key)

            frames, duration, _, _ = self.frame_extractor.extract(temp_video_path)

            if self.verbose:
                print(f"Analyzing {len(frames)} frames ...")

            detections = []

            for timestamp, frame in frames:
                dets = self.detector.detect(frame, keywords, frame_info=f"[{timestamp:.2f}s]")

                for det in dets:
                    detections.append({
                        "keyword": det.label.rstrip('.'),
                        "timestamp": timestamp,
                        "confidence": det.confidence
                    })

            if self.verbose:
                print(f"Found {len(detections)} detections")

            return detections

        finally:
            if temp_video_path:
                self._cleanup_temp_file(temp_video_path)