"""
config.py
Hollo [홀로] 서비스 전역 설정 및 페르소나/에너지 상수 정의
"""

from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PLACES_FILE = DATA_DIR / "places.json"

# .env 로드
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

# 서비스 메타데이터
APP_TITLE = "Hollo [홀로]"
APP_SUBTITLE = "내향인 뚜벅이를 위한 저자극 힐링 여행 큐레이터"
APP_ICON = "🌿"
APP_VERSION = "v1.0.0"

# 🪫 에너지 레벨 정의 (사용자 컨디션)
ENERGY_LEVELS = {
    "EMPTY": {
        "name": "🪫 방전 (완전 휴식)",
        "desc": "이동을 최소화하고, 한적한 자연이나 조용한 공간에서 멍때리고 싶어요.",
        "max_spots": 2,
        "weights": {
            "quietness": 0.40,
            "transit": 0.25,
            "walking": 0.15,
            "stayability": 0.20,
            "nature": 0.20,
            "culture": -0.10,
            "interaction_penalty": -0.30,
        },
    },
    "LOW": {
        "name": "🌿 조금 쉼 (가벼운 산책)",
        "desc": "복잡한 곳은 피하고, 잔잔한 호수나 바다를 보며 혼자 걷고 싶어요.",
        "max_spots": 3,
        "weights": {
            "quietness": 0.30,
            "transit": 0.20,
            "walking": 0.20,
            "stayability": 0.15,
            "solo_cafe": 0.15,
            "nature": 0.15,
            "interaction_penalty": -0.20,
        },
    },
    "MEDIUM": {
        "name": "🙂 잔잔한 탐방 (여유로운 하루)",
        "desc": "혼자지만 작은 미술관, 독립서점, 고즈넉한 골목을 둘러보고 싶어요.",
        "max_spots": 3,
        "weights": {
            "quietness": 0.20,
            "transit": 0.15,
            "walking": 0.20,
            "culture": 0.25,
            "solo_dining": 0.15,
            "solo_cafe": 0.15,
            "interaction_penalty": -0.10,
        },
    },
    "HIGH": {
        "name": "🔋 에너지 충전 (새로운 발견)",
        "desc": "혼자만의 시간을 가지면서 로컬 감성 명소나 풍경을 알차게 보고 싶어요.",
        "max_spots": 4,
        "weights": {
            "quietness": 0.15,
            "transit": 0.15,
            "walking": 0.25,
            "culture": 0.20,
            "nature": 0.20,
            "solo_dining": 0.15,
            "interaction_penalty": -0.05,
        },
    },
}

# 5대 세부 페르소나 정의
PERSONAS = {
    "THINKING": {
        "title": "생각정리형",
        "tag": "🌊 바다/호수/사찰",
        "desc": "혼자 조용히 걷고 생각할 시간이 필요한 여행자",
        "keywords": ["둘레길", "호수", "바다", "사찰", "조용한 산책"],
    },
    "CULTURE": {
        "title": "문화감상형",
        "tag": "🖼️ 미술관/독립서점",
        "desc": "사람 치이지 않고 혼자만의 예술과 활자를 음미하고픈 여행자",
        "keywords": ["작은 미술관", "독립서점", "문학관", "전시"],
    },
    "CAFE_STAY": {
        "title": "카페체류형",
        "tag": "☕ 북카페/오션뷰",
        "desc": "채광 좋은 조용한 카페에서 책 읽고 멍때리고 싶은 여행자",
        "keywords": ["정원 카페", "북카페", "오션뷰", "숲 카페"],
    },
    "NATURE_REST": {
        "title": "자연회복형",
        "tag": "🌳 숲길/휴양림",
        "desc": "일상의 소음에서 벗어나 피톤치드로 숨을 고르고픈 여행자",
        "keywords": ["자연휴양림", "숲길", "치유의 숲", "조용한 공원"],
    },
    "EXPLORE": {
        "title": "가벼운 탐방형",
        "tag": "🏘️ 로컬 골목/마을",
        "desc": "너무 조용하면 심심하고, 혼자 천천히 동네를 거닐고픈 여행자",
        "keywords": ["오래된 골목", "작은 마을", "로컬 서점", "한적한 시장"],
    },
}
