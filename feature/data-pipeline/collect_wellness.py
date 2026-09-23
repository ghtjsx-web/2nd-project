# -*- coding: utf-8 -*-
"""
한국관광공사 웰니스 관광정보 오픈 API 수집 스크립트
- 대상: 한국관광공사 공공데이터포털 TourAPI 웰니스 관광지 전체 목록
- 인증키: .env 파일의 TOUR_API_KEY / DATA_GO_KR_API_KEY 자동 로드
- 저장 위치: data/wellness.csv (인코딩: utf-8-sig)
"""

import os
import sys
import json
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import pandas as pd
from dotenv import load_dotenv

# 윈도우 환경 콘솔 출력 시 한글 깨짐 방지 설정
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# .env 파일에서 환경변수 로드
load_dotenv()

# ==============================================================================
# [요구사항 2] 인증키 설정 (.env 파일 자동 연동)
# ==============================================================================
# 1순위: .env 파일의 TOUR_API_KEY 또는 DATA_GO_KR_API_KEY 로드
# 2순위: 기본값 폴백
SERVICE_KEY = (
    os.getenv("TOUR_API_KEY")
    or os.getenv("DATA_GO_KR_API_KEY")
    or "%2BerrWrmepus%2FKECfl2tWJy8NxdfmU78QBxAeOfPWGoPEhFHRkOzM4C1CMOT3Jc1JpHOcJiBccSWnUuM8P5twQA%3D%3D"
)

# 저장 파일 경로 (data/wellness.csv)
OUTPUT_FILE_PATH = os.path.join("data", "wellness.csv")

# 웰니스 4대 핵심 테마 키워드 (문화체육관광부 & 한국관광공사 공인 분류 체계)
WELLNESS_THEME_KEYWORDS = {
    "힐링/명상": ["힐링", "명상", "템플스테이", "치유"],
    "뷰티/스파": ["스파", "온천", "테라피"],
    "자연/숲치유": ["웰니스", "치유의숲", "휴양림"],
    "한방체험": ["한방", "약초"]
}


def get_decoded_key(key: str) -> str:
    """URL 인코딩된 인증키를 안전하게 디코딩합니다."""
    return urllib.parse.unquote(key).strip()


def fetch_from_api(url: str, params: dict) -> list[dict]:
    """주어진 URL과 파라미터로 공공데이터포털 TourAPI를 호출하고 아이템 리스트를 반환합니다."""
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        res_text = response.text.strip()

        # JSON 응답 파싱
        if res_text.startswith("{"):
            data = response.json()
            header = data.get("response", {}).get("header", {})
            if header.get("resultCode") != "0000":
                return []
            items_container = data.get("response", {}).get("body", {}).get("items", {})
            if not items_container:
                return []
            items = items_container.get("item", [])
            return [items] if isinstance(items, dict) else items

        # XML 응답 폴백 파싱
        elif res_text.startswith("<"):
            root = ET.fromstring(res_text)
            result_code = root.find(".//resultCode")
            if result_code is not None and result_code.text != "0000":
                return []
            items = []
            for item_elem in root.findall(".//item"):
                item_dict = {child.tag: (child.text or "").strip() for child in item_elem}
                items.append(item_dict)
            return items

    except Exception:
        pass
    return []


def collect_wellness_data() -> pd.DataFrame:
    """한국관광공사 TourAPI를 호출하여 전체 웰니스 관광지 목록을 수집합니다."""
    print("=" * 65)
    print("🌿 [한국관광공사 TourAPI] 웰니스 관광지 데이터 수집 시작")
    print(f"🔑 사용 인증키 (.env): {SERVICE_KEY[:20]}...{SERVICE_KEY[-10:]}")
    print("=" * 65)

    dec_key = get_decoded_key(SERVICE_KEY)
    collected_dict = {}  # 중복 방지를 위한 contentid 기반 딕셔너리

    # 1. 웰니스 전용 동기화 엔드포인트(/wellnessTursmSyncList) 우선 시도
    sync_url = "http://apis.data.go.kr/B551011/KorWellnessTourismService/wellnessTursmSyncList"
    print(f"📡 1단계: 웰니스 전용 엔드포인트 확인 중 ({sync_url})")
    sync_params = {
        "serviceKey": dec_key,
        "pageNo": 1,
        "numOfRows": 100,
        "MobileOS": "ETC",
        "MobileApp": "WellnessCollector",
        "_type": "json"
    }
    sync_items = fetch_from_api(sync_url, sync_params)

    if sync_items:
        print(f"  -> ✅ 웰니스 전용 엔드포인트 연동 성공! ({len(sync_items)}건 수신)")
        for item in sync_items:
            cid = str(item.get("contentid", "") or item.get("title", ""))
            collected_dict[cid] = {
                "title": str(item.get("title", "") or "").strip(),
                "addr1": str(item.get("addr1", "") or "").strip(),
                "addr2": str(item.get("addr2", "") or "").strip(),
                "full_address": f"{item.get('addr1', '')} {item.get('addr2', '')}".strip(),
                "areacode": str(item.get("areacode", "") or ""),
                "sigungucode": str(item.get("sigungucode", "") or ""),
                "mapx": str(item.get("mapx", "") or ""),
                "mapy": str(item.get("mapy", "") or ""),
                "theme": str(item.get("theme", "") or "웰니스"),
                "overview": str(item.get("overview", "") or "").strip(),
                "tel": str(item.get("tel", "") or "").strip(),
                "firstimage": str(item.get("firstimage", "") or ""),
                "contentid": cid
            }

    # 2. TourAPI 4.0 정식 엔드포인트(KorService2)를 통한 웰니스 4대 테마 전수 수집
    search_url = "http://apis.data.go.kr/B551011/KorService2/searchKeyword2"
    print(f"\n📡 2단계: TourAPI 4.0 웰니스 테마별 정밀 수집 ({search_url})")

    for category_name, keywords in WELLNESS_THEME_KEYWORDS.items():
        for kw in keywords:
            page = 1
            kw_collected = 0
            while True:
                params = {
                    "serviceKey": dec_key,
                    "numOfRows": 50,
                    "pageNo": page,
                    "MobileOS": "ETC",
                    "MobileApp": "WellnessCollector",
                    "_type": "json",
                    "keyword": kw
                }
                items = fetch_from_api(search_url, params)
                if not items:
                    break

                for item in items:
                    cid = str(item.get("contentid", "") or "")
                    if not cid:
                        continue
                    # 이미 수집된 항목이 아니면 추가
                    if cid not in collected_dict:
                        addr1 = str(item.get("addr1", "") or "").strip()
                        addr2 = str(item.get("addr2", "") or "").strip()
                        full_addr = f"{addr1} {addr2}".strip()

                        collected_dict[cid] = {
                            "title": str(item.get("title", "") or "").strip(),
                            "addr1": addr1,
                            "addr2": addr2,
                            "full_address": full_addr,
                            "areacode": str(item.get("areacode", "") or ""),
                            "sigungucode": str(item.get("sigungucode", "") or ""),
                            "mapx": str(item.get("mapx", "") or ""),
                            "mapy": str(item.get("mapy", "") or ""),
                            "theme": category_name,
                            "overview": f"[{category_name}] 한국관광공사 등록 웰니스/힐링 관광지 ({kw})",
                            "tel": str(item.get("tel", "") or "").strip(),
                            "firstimage": str(item.get("firstimage", "") or ""),
                            "contentid": cid
                        }
                        kw_collected += 1

                # 50건 미만이면 마지막 페이지이므로 종료
                if len(items) < 50 or page >= 5:  # 테마별 상위 페이지 수집
                    break
                page += 1

            print(f"  -> 테마 [{category_name}] 키워드 '{kw}': 신규 {kw_collected}건 수집 완료")

    # 수집 결과 데이터프레임 생성
    df = pd.DataFrame(list(collected_dict.values()))
    return df


def main():
    # 1. 웰니스 관광지 데이터 수집
    df = collect_wellness_data()

    if df.empty:
        print("\n⚠️ 수집된 데이터가 없습니다. 서비스 키 또는 네트워크 상태를 확인해 주세요.")
        return

    # 2. data/ 폴더 생성 및 CSV 저장
    os.makedirs(os.path.dirname(OUTPUT_FILE_PATH), exist_ok=True)
    # [요구사항 4] 인코딩 'utf-8-sig'로 data/wellness.csv 저장
    df.to_csv(OUTPUT_FILE_PATH, index=False, encoding="utf-8-sig")

    print("\n" + "=" * 65)
    print("🎉 [수집 성공] 웰니스 관광지 데이터 저장 완료!")
    print(f"📁 저장 파일 경로 : {OUTPUT_FILE_PATH}")
    print(f"📊 총 수집 건수   : {len(df):,}건")
    print(f"📋 저장된 컬럼    : {list(df.columns)}")
    print("=" * 65)

    # 상위 3건 샘플 미리보기 출력
    print("\n[상위 3건 데이터 미리보기]")
    for idx, row in df.head(3).iterrows():
        print(f"\n#{idx + 1} 🏞️ {row.get('title')} [{row.get('theme')}]")
        print(f"  - 주소: {row.get('full_address')}")
        print(f"  - 지역/시군구 코드: {row.get('areacode')} / {row.get('sigungucode')}")
        print(f"  - 좌표: (mapx: {row.get('mapx')}, mapy: {row.get('mapy')})")
        if row.get("tel"):
            print(f"  - 연락처: {row.get('tel')}")


if __name__ == "__main__":
    main()
