"""
data_tools.py - Fest & Rest 로컬 축제 & 쉼터 데이터 및 이미지 검색 도구
dotenv를 통해 TAVILY_API_KEY를 로드하여 LLM이 지정한 키워드로 웹에서 실제 사진을 검색합니다.
"""

import os
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv

# .env 환경변수 로드
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def search_spot_image(search_query: str, fallback_url: str = "") -> str:
    """
    Tavily 검색 API를 활용해 검색 쿼리에 맞는 실제 웹 이미지를 실시간으로 가져옵니다.
    실패하거나 이미지가 없을 경우 fallback_url을 반환합니다.
    """
    if not TAVILY_API_KEY:
        return fallback_url

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": search_query,
            "include_images": True,
            "search_depth": "basic"
        }
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            images = data.get("images", [])
            if images and isinstance(images, list) and len(images) > 0:
                first_img = images[0]
                # http로 시작하는 유효한 이미지 URL인지 확인
                if isinstance(first_img, str) and first_img.startswith("http"):
                    return first_img
    except Exception:
        pass

    return fallback_url


def get_dummy_festivals() -> List[Dict[str, Any]]:
    """
    활기찬 에너지를 경험할 수 있는 지역 축제 데이터 목록
    """
    return [
        {
            "id": "fest_1",
            "name": "성수 인디 뮤직 & 팝업 페스타",
            "theme": "힙하고 트렌디한",
            "category": "festival",
            "lat": 37.5445,
            "lon": 127.0560,
            "address": "서울 성동구 연무장길 일대",
            "energy_cost": "High",
            "description": "골목마다 울려 퍼지는 인디 밴드의 라이브 버스킹과 힙한 브랜드 팝업스토어",
            "tag": "🔥 도파민 폭발",
            "fallback_image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&h=500&q=80"
        },
        {
            "id": "fest_2",
            "name": "서울숲 가을 재즈 & 피크닉 나이트",
            "theme": "자연친화적인",
            "category": "festival",
            "lat": 37.5430,
            "lon": 127.0415,
            "address": "서울 성동구 서울숲 야외무대",
            "energy_cost": "Medium",
            "description": "잔디밭에 돗자리를 펴고 즐기는 감미로운 색소폰 선율과 푸드트럭 빌리지",
            "tag": "🎷 로맨틱 피크닉",
            "fallback_image": "https://images.unsplash.com/photo-1511192336575-5a79af67a629?auto=format&fit=crop&w=800&h=500&q=80"
        },
        {
            "id": "fest_3",
            "name": "뚝섬 한강 드론 라이트쇼",
            "theme": "힙하고 트렌디한",
            "category": "festival",
            "lat": 37.5315,
            "lon": 127.0667,
            "address": "서울 광진구 뚝섬한강공원 수변무대",
            "energy_cost": "Medium",
            "description": "밤하늘을 화려하게 수놓는 1,000대의 불빛 드론과 한강 분수 퍼포먼스",
            "tag": "✨ 환상적인 야경",
            "fallback_image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&h=500&q=80"
        }
    ]


def get_dummy_rests() -> List[Dict[str, Any]]:
    """
    도심의 소음을 피해 숨을 고를 수 있는 로컬 쉼터/카페 데이터 목록
    """
    return [
        {
            "id": "rest_1",
            "name": "숲속 서재 & 티하우스 '정적'",
            "theme": "조용하고 아늑한",
            "category": "rest",
            "lat": 37.5458,
            "lon": 127.0432,
            "address": "서울 성동구 서울숲2길",
            "energy_cost": "Low",
            "description": "잔잔한 빗소리 앰비언트와 엄선된 싱글오리진 잎차, 통창 너머 초록 정원 뷰",
            "tag": "🌿 배터리 급속 충전",
            "fallback_image": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&h=500&q=80"
        },
        {
            "id": "rest_2",
            "name": "오솔길 루프탑 가든",
            "theme": "자연친화적인",
            "category": "rest",
            "lat": 37.5472,
            "lon": 127.0498,
            "address": "서울 성동구 아차산로 쉼터",
            "energy_cost": "Low",
            "description": "도심 속 숨겨진 옥상 정원에서 푹신한 빈백에 기대어 즐기는 바람과 햇살",
            "tag": "☕ 멍때리기 명당",
            "fallback_image": "https://images.unsplash.com/photo-1519999482648-25049ddd37b1?auto=format&fit=crop&w=800&h=500&q=80"
        },
        {
            "id": "rest_3",
            "name": "고즈넉 한옥 다이닝 & 뜰",
            "theme": "조용하고 아늑한",
            "category": "rest",
            "lat": 37.5412,
            "lon": 127.0520,
            "address": "서울 성동구 성수동 한옥마당",
            "energy_cost": "Low",
            "description": "툇마루에 앉아 정원의 물소리를 들으며 정갈한 제철 솥밥을 즐길 수 있는 쉼터",
            "tag": "🍵 속 편한 위로",
            "fallback_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&h=500&q=80"
        }
    ]
