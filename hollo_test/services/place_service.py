"""
services/place_service.py
장소 데이터 로드, 검증 및 필터링 서비스
"""

import json
from typing import List, Dict, Optional
from pathlib import Path

try:
    from config import PLACES_FILE
except ImportError:
    from hollo_test.config import PLACES_FILE


class PlaceService:
    def __init__(self, json_path: Optional[Path] = None):
        self.json_path = json_path or PLACES_FILE
        self._places: List[Dict] = []
        self.reload()

    def reload(self):
        """JSON 데이터베이스 로드 및 캐싱"""
        if self.json_path.exists():
            with open(self.json_path, "r", encoding="utf-8") as f:
                self._places = json.load(f)
        else:
            self._places = []

    def get_all(self) -> List[Dict]:
        """모든 장소 목록 반환"""
        return self._places

    def get_by_id(self, place_id: str) -> Optional[Dict]:
        """ID로 장소 단건 조회"""
        for p in self._places:
            if p.get("id") == place_id:
                return p
        return None

    def filter_candidates(
        self,
        max_transit_minutes: Optional[int] = None,
        theme: Optional[str] = None,
        persona: Optional[str] = None,
    ) -> List[Dict]:
        """
        Step 1. Hard Filter:
        제약 조건(이동시간 한계, 특정 테마, 페르소나)에 따라 후보군을 1차 필터링합니다.
        """
        candidates = []
        for p in self._places:
            # 1. 최대 이동시간 제약 (Hard Constraint)
            if max_transit_minutes is not None:
                p_time = p.get("transit", {}).get("total_minutes", 999)
                if p_time > max_transit_minutes:
                    continue

            # 2. 테마 필터 (선택적)
            if theme and theme != "전체":
                if theme not in p.get("theme", "") and theme not in p.get("name", ""):
                    continue

            # 3. 페르소나 매칭 필터 (선택적)
            if persona and persona != "전체":
                if persona not in p.get("persona_fit", []):
                    continue

            candidates.append(p)

        return candidates

    def get_themes(self) -> List[str]:
        """등록된 테마 고유값 목록 반환"""
        themes = set()
        for p in self._places:
            t = p.get("theme")
            if t:
                themes.add(t)
        return sorted(list(themes))


# 싱글톤 서비스 인스턴스
place_service = PlaceService()
