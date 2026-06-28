from typing import List, Dict, Tuple, Optional
from .models import FrameAnalysis, Fragment, Detection


class Segmenter:

    def __init__(self, gap_threshold: float = 0.5):

        self.gap_threshold = gap_threshold

    def segment(
            self,
            frame_analyses: List[FrameAnalysis],
            with_detection: bool = True
    ) -> List[Fragment]:

        if not frame_analyses:
            return []

        fragments = []


        detections_by_keyword = {}

        for fa in frame_analyses:
            for det in fa.detections:
                keyword = det.label
                if keyword not in detections_by_keyword:
                    detections_by_keyword[keyword] = []
                detections_by_keyword[keyword].append({
                    "frame_index": fa.frame_index,
                    "timestamp": fa.timestamp,
                    "detection": det
                })

        for keyword, detections in detections_by_keyword.items():
            detections.sort(key=lambda x: x["frame_index"])

            current_fragment = None

            for item in detections:
                if current_fragment is None:
                    current_fragment = {
                        "keyword": keyword,
                        "start_frame_index": item["frame_index"],
                        "end_frame_index": item["frame_index"],
                        "start_time": item["timestamp"],
                        "end_time": item["timestamp"],
                        "detections": [item["detection"]],
                        "frame_count": 1
                    }
                elif (item["frame_index"] - current_fragment["end_frame_index"]) <= 1:
                    current_fragment["end_frame_index"] = item["frame_index"]
                    current_fragment["end_time"] = item["timestamp"]
                    current_fragment["detections"].append(item["detection"])
                    current_fragment["frame_count"] += 1
                else:
                    fragments.append(Fragment(
                        keyword=current_fragment["keyword"],
                        start_time=current_fragment["start_time"],
                        end_time=current_fragment["end_time"],
                        detections=current_fragment["detections"],
                        frame_count=current_fragment["frame_count"]
                    ))
                    current_fragment = {
                        "keyword": keyword,
                        "start_frame_index": item["frame_index"],
                        "end_frame_index": item["frame_index"],
                        "start_time": item["timestamp"],
                        "end_time": item["timestamp"],
                        "detections": [item["detection"]],
                        "frame_count": 1
                    }

            if current_fragment:
                fragments.append(Fragment(
                    keyword=current_fragment["keyword"],
                    start_time=current_fragment["start_time"],
                    end_time=current_fragment["end_time"],
                    detections=current_fragment["detections"],
                    frame_count=current_fragment["frame_count"]
                ))

        return fragments

    def group_detections_into_fragments(
            self,
            detections: List[Dict],
            gap_threshold: float = 0.5
    ) -> List[Dict]:

        if not detections:
            return []

        sorted_dets = sorted(detections, key=lambda x: x["timestamp"])

        fragments = []
        current_fragment = None

        for det in sorted_dets:
            if current_fragment is None:
                current_fragment = {
                    "keyword": det["keyword"],
                    "start_time": det["timestamp"],
                    "end_time": det["timestamp"],
                    "detections": [det],
                    "confidence": det.get("confidence", 1.0)
                }
            elif (det["timestamp"] - current_fragment["end_time"]) <= gap_threshold and det["keyword"] == \
                    current_fragment["keyword"]:
                current_fragment["end_time"] = det["timestamp"]
                current_fragment["detections"].append(det)
                current_fragment["confidence"] = max(current_fragment["confidence"], det.get("confidence", 1.0))
            else:
                fragments.append(current_fragment)
                current_fragment = {
                    "keyword": det["keyword"],
                    "start_time": det["timestamp"],
                    "end_time": det["timestamp"],
                    "detections": [det],
                    "confidence": det.get("confidence", 1.0)
                }

        if current_fragment:
            fragments.append(current_fragment)

        return fragments

    def merge_overlapping_fragments(self, fragments: List[Fragment]) -> List[Fragment]:
        if len(fragments) <= 1:
            return fragments

        sorted_frags = sorted(fragments, key=lambda f: f.start_time)
        merged = []
        current = sorted_frags[0]

        for frag in sorted_frags[1:]:
            if frag.start_time <= current.end_time + self.gap_threshold and frag.keyword == current.keyword:
                current.end_time = max(current.end_time, frag.end_time)
                current.detections.extend(frag.detections)
                current.frame_count += frag.frame_count
            else:
                merged.append(current)
                current = frag

        merged.append(current)
        return merged