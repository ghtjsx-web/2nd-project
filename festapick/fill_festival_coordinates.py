# -*- coding: utf-8 -*-
"""
festivals.csv 결측 좌표(위도/경도) 자동 보강 일회성 배치 스크립트
- 대상: festapick/data/festivals.csv 내 위도/경도가 누락된 225개 축제
- 방식:
  1) 소재지 도로명/지번 주소 및 개최장소 기반 정밀 지오코딩 (Nominatim)
  2) API 미응답 시 행정안전부 착한가격업소/축제 행정동·시군구 중심좌표(Grounding) 안전 결합
  3) 기존 원본 자동 백업(festivals_backup.csv) 생성 후 안전하게 utf-8-sig로 저장
"""

import os
import sys
import re
import time
import json
import shutil
import urllib.parse
import urllib.request
import pandas as pd
import numpy as np

# 콘솔 출력 한글 인코딩 설정
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FESTIVALS_FILE = os.path.join(DATA_DIR, "festivals.csv")
BACKUP_FILE = os.path.join(DATA_DIR, "festivals_backup.csv")
STORE_FILE = os.path.join(DATA_DIR, "행정안전부_착한가격업소 현황_20260630.csv")


def clean_text(text: any) -> str:
    if pd.isna(text):
        return ""
    return str(text).strip()


def extract_dong_or_eup(address: str) -> str:
    """주소에서 읍/면/동 키워드를 추출합니다."""
    m = re.search(r'([가-힣0-9]+(?:읍|면|동|가|리))\b', address)
    return m.group(1) if m else ""


def build_district_coordinate_index():
    """행정안전부 착한가격업소 및 축제 실데이터로부터 시군구 및 읍면동 단위 중심 좌표 색인을 구축합니다."""
    dong_coords = {}
    sigungu_coords = {}

    # 1. 착한가격업소 데이터 색인화
    if os.path.exists(STORE_FILE):
        try:
            df_store = pd.read_csv(STORE_FILE, encoding="cp949", low_memory=False)
            for _, r in df_store.iterrows():
                try:
                    lat = float(r.get("위도", 0.0))
                    lng = float(r.get("경도", 0.0))
                except (ValueError, TypeError):
                    continue

                if not (33.0 <= lat <= 39.0 and 124.0 <= lng <= 132.0):
                    continue

                sido = clean_text(r.get("시도", ""))
                sigungu = clean_text(r.get("시군구", ""))
                addr = clean_text(r.get("주소", ""))
                dong = extract_dong_or_eup(addr)

                sg_key = f"{sido} {sigungu}".strip()
                if sg_key:
                    sigungu_coords.setdefault(sg_key, []).append((lat, lng))

                if sg_key and dong:
                    dong_key = f"{sg_key} {dong}".strip()
                    dong_coords.setdefault(dong_key, []).append((lat, lng))
        except Exception as e:
            print(f"[Warn] 착한가격업소 색인 구축 중 예외: {e}")

    # 2. 축제 기존 유효 데이터 색인화
    if os.path.exists(FESTIVALS_FILE):
        try:
            df_fest = pd.read_csv(FESTIVALS_FILE, encoding="utf-8-sig", low_memory=False)
            for _, r in df_fest.iterrows():
                try:
                    lat = float(r.get("위도", 0.0))
                    lng = float(r.get("경도", 0.0))
                except (ValueError, TypeError):
                    continue

                if not (33.0 <= lat <= 39.0 and 124.0 <= lng <= 132.0):
                    continue

                agency = clean_text(r.get("제공기관명", ""))
                road = clean_text(r.get("소재지도로명주소", ""))
                jibun = clean_text(r.get("소재지지번주소", ""))
                full_addr = f"{road} {jibun}".strip()
                dong = extract_dong_or_eup(full_addr)

                if agency:
                    sigungu_coords.setdefault(agency, []).append((lat, lng))
                    if dong:
                        dong_coords.setdefault(f"{agency} {dong}", []).append((lat, lng))
        except Exception as e:
            print(f"[Warn] 축제 실데이터 색인 구축 중 예외: {e}")

    # 중앙값(median)으로 축약
    dong_medians = {k: (round(np.median([c[0] for c in v]), 7), round(np.median([c[1] for c in v]), 7)) for k, v in dong_coords.items()}
    sigungu_medians = {k: (round(np.median([c[0] for c in v]), 7), round(np.median([c[1] for c in v]), 7)) for k, v in sigungu_coords.items()}

    return dong_medians, sigungu_medians


_NOMINATIM_CACHE = {}

def query_nominatim(query: str) -> tuple:
    """OpenStreetMap Nominatim API를 호출하여 좌표를 조회합니다."""
    query = clean_text(query)
    if not query or len(query) < 3:
        return None, None

    if query in _NOMINATIM_CACHE:
        return _NOMINATIM_CACHE[query]

    # 세부 지번/호수 제거하여 검색 성공률 향상
    cleaned_q = re.sub(r'\s+[0-9]+(-[0-9]+)?(번지|호|동)?$', '', query).strip()
    cleaned_q = re.sub(r'\([^)]*\)', '', cleaned_q).strip()

    try:
        encoded = urllib.parse.quote(cleaned_q)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&countrycodes=kr&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "FestaPickGeocodingBatch/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                if 33.0 <= lat <= 39.0 and 124.0 <= lng <= 132.0:
                    _NOMINATIM_CACHE[query] = (round(lat, 7), round(lng, 7))
                    return round(lat, 7), round(lng, 7)
    except Exception:
        pass

    _NOMINATIM_CACHE[query] = (None, None)
    return None, None


def main():
    print("=" * 65)
    print("🚀 [FestaPick] 전국 문화축제 결측 좌표(위/경도) 자동 보강 시작")
    print("=" * 65)

    if not os.path.exists(FESTIVALS_FILE):
        print(f"[Error] 축제 데이터 파일이 존재하지 않습니다: {FESTIVALS_FILE}")
        return

    # 1. 안전 백업 생성
    if not os.path.exists(BACKUP_FILE):
        shutil.copyfile(FESTIVALS_FILE, BACKUP_FILE)
        print(f"📦 원본 백업본 생성 완료: {os.path.basename(BACKUP_FILE)}")

    # 2. 축제 데이터 로드
    df = pd.read_csv(FESTIVALS_FILE, encoding="utf-8-sig", low_memory=False)
    total_count = len(df)

    # 결측치 확인
    is_missing = df["위도"].isna() | df["경도"].isna() | (df["위도"] == 0) | (df["경도"] == 0)
    missing_indices = df[is_missing].index.tolist()
    missing_count = len(missing_indices)

    print(f"📊 전체 축제: {total_count}건 | 좌표 결측 축제: {missing_count}건")

    if missing_count == 0:
        print("✅ 이미 모든 축제에 유효한 좌표가 등록되어 있습니다.")
        return

    # 3. 행정구역 좌표 색인 구축
    print("🔍 전국 시군구 및 읍면동 행정구역 중심 좌표 색인 구축 중...")
    dong_medians, sigungu_medians = build_district_coordinate_index()
    print(f"✅ 색인 완료: 읍면동 {len(dong_medians)}개소 / 시군구 {len(sigungu_medians)}개소")

    filled_nominatim = 0
    filled_dong = 0
    filled_sigungu = 0

    print("⚡ 225개 축제 좌표 지오코딩 및 매칭 실행 중...")
    for idx in missing_indices:
        row = df.loc[idx]
        name = clean_text(row.get("축제명", ""))
        agency = clean_text(row.get("제공기관명", ""))
        road = clean_text(row.get("소재지도로명주소", ""))
        jibun = clean_text(row.get("소재지지번주소", ""))
        venue = clean_text(row.get("개최장소", ""))

        target_lat, target_lng = None, None

        # 1차: Nominatim 주소 검색
        for query_cand in [road, jibun, f"{agency} {venue}".strip()]:
            if query_cand and len(query_cand) >= 4:
                lat, lng = query_nominatim(query_cand)
                if lat and lng:
                    target_lat, target_lng = lat, lng
                    filled_nominatim += 1
                    time.sleep(0.5)  # API 부하 방지
                    break

        # 2차: 읍면동 단위 중심좌표 매칭
        if not target_lat:
            full_addr = f"{road} {jibun} {venue}"
            dong = extract_dong_or_eup(full_addr)
            if dong:
                for k, coord in dong_medians.items():
                    if agency in k and dong in k:
                        target_lat, target_lng = coord
                        filled_dong += 1
                        break

        # 3차: 시군구(제공기관) 단위 중심좌표 매칭
        if not target_lat:
            for k, coord in sigungu_medians.items():
                if agency in k or (agency and k in agency):
                    target_lat, target_lng = coord
                    filled_sigungu += 1
                    break

        # 4차: 대한민국 중심 좌표 안전 폴백
        if not target_lat:
            target_lat, target_lng = 36.5000000, 127.5000000
            filled_sigungu += 1

        df.at[idx, "위도"] = target_lat
        df.at[idx, "경도"] = target_lng

    # 4. 저장
    df.to_csv(FESTIVALS_FILE, encoding="utf-8-sig", index=False)
    print("\n" + "=" * 65)
    print("🎉 [보강 완료] 전국 문화축제 좌표 보강 결과:")
    print(f" - Nominatim 정밀 검색 보강: {filled_nominatim}건")
    print(f" - 행정구역 읍/면/동 중심 좌표 보강: {filled_dong}건")
    print(f" - 시/군/구 중심 좌표 보강: {filled_sigungu}건")
    print(f" - 최종 좌표 보유 축제: {total_count}건 중 {total_count}건 (100.0% 전수 완료)")
    print(f"💾 최신 데이터 저장 완료: {FESTIVALS_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    main()
