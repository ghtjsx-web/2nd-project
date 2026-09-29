# -*- coding: utf-8 -*-
"""
validate_datasets.py
================================================================================
페스타픽 (FestaPick) 데이터 품질 및 무결성 자동 검증 스크립트

[검증 항목]
1. festivals.csv
   - 위도/경도 결측치(NaN 또는 0.0) 0건 검증
   - 대한민국 좌표 범위(위도 33~39, 경도 124~132) 100% 적합성 검증
   - 중복 축제(축제명 + 시작일자 기준) 0건 검증
2. good_price_stores.csv
   - 미용업, 세탁업 등 비외식업 업종 완전 배제(0건) 검증
3. wellness.csv
   - 4대 필수 테마(자연, 스파, 힐링, 한방) 정상 매핑(100%) 검증
================================================================================
"""

import os
import sys
import glob
from typing import Dict, Any, List, Tuple
import pandas as pd

# Windows 터미널 UTF-8 출력 지원
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def find_data_file(patterns: List[str]) -> str:
    """우선순위 패턴에 따라 데이터 파일을 탐색합니다."""
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return ""


def validate_festivals() -> Tuple[bool, Dict[str, Any]]:
    """festivals.csv 무결성을 검증합니다."""
    filepath = find_data_file([
        "festapick/data/festivals.csv",
        "data/festivals.csv",
        "festivals.csv"
    ])
    if not filepath or not os.path.exists(filepath):
        return False, {"error": "festivals.csv 파일을 찾을 수 없습니다."}

    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="cp949")

    total_count = len(df)

    # 1) 위도/경도 결측 또는 0 체크
    lat_col = "위도" if "위도" in df.columns else "lat"
    lng_col = "경도" if "경도" in df.columns else "lng"

    df["_lat"] = pd.to_numeric(df[lat_col], errors="coerce").fillna(0.0)
    df["_lng"] = pd.to_numeric(df[lng_col], errors="coerce").fillna(0.0)

    null_or_zero_mask = (df["_lat"] == 0.0) | (df["_lng"] == 0.0)
    missing_coords_count = int(null_or_zero_mask.sum())

    # 2) 대한민국 좌표 범위 (위도 33~39, 경도 124~132)
    in_korea_mask = (
        (df["_lat"] >= 33.0) & (df["_lat"] <= 39.0) &
        (df["_lng"] >= 124.0) & (df["_lng"] <= 132.0)
    )
    in_korea_count = int(in_korea_mask.sum())
    in_korea_ratio = (in_korea_count / total_count * 100.0) if total_count > 0 else 0.0

    # 3) 중복 축제 검증 (축제명 + 시작일자)
    name_col = "축제명" if "축제명" in df.columns else "title"
    sdate_col = "축제시작일자" if "축제시작일자" in df.columns else "start_date"
    dup_mask = df.duplicated(subset=[name_col, sdate_col], keep=False)
    duplicate_count = int(dup_mask.sum())

    # 4) 실내/야외(is_indoor) 태그 컬럼 검증
    indoor_col = "is_indoor" if "is_indoor" in df.columns else ("실내외구분" if "실내외구분" in df.columns else None)
    has_indoor = indoor_col is not None
    indoor_dist = df[indoor_col].value_counts().to_dict() if has_indoor else {}
    valid_indoor_count = int(df[indoor_col].isin(["실내", "야외"]).sum()) if has_indoor else 0
    indoor_ok = has_indoor and (valid_indoor_count == total_count)

    is_valid = (missing_coords_count == 0) and (in_korea_count == total_count) and (duplicate_count == 0) and indoor_ok

    report = {
        "file": filepath,
        "total_count": total_count,
        "missing_coords_count": missing_coords_count,
        "in_korea_count": in_korea_count,
        "in_korea_ratio": in_korea_ratio,
        "duplicate_count": duplicate_count,
        "has_indoor": has_indoor,
        "indoor_distribution": indoor_dist,
        "indoor_ok": indoor_ok,
        "passed": is_valid
    }
    return is_valid, report


def validate_good_price_stores() -> Tuple[bool, Dict[str, Any]]:
    """good_price_stores.csv (착한가격업소) 무결성을 검증합니다."""
    filepath = find_data_file([
        "festapick/data/good_price_stores.csv",
        "data/good_price_stores.csv",
        "festapick/data/*착한가격업소*.csv",
        "data/*착한가격업소*.csv"
    ])
    if not filepath or not os.path.exists(filepath):
        return False, {"error": "착한가격업소 데이터 파일을 찾을 수 없습니다."}

    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="cp949")

    # 비외식업 업종 키워드 (미용, 세탁, 목욕, 숙박 등)
    non_food_keywords = ["미용", "이용", "세탁", "목욕", "숙박", "기타비요식"]
    cat_col = "업종" if "업종" in df.columns else "분류"

    # good_price_stores.csv의 경우 이미 비외식업이 제거되어 있어야 함
    # 만약 원천 데이터라면 is_food_related 적용 검증
    is_prefiltered = "good_price_stores" in os.path.basename(filepath)
    if is_prefiltered:
        bad_mask = df[cat_col].astype(str).apply(lambda x: any(k in x for k in non_food_keywords))
        bad_count = int(bad_mask.sum())
        total_count = len(df)
        food_count = total_count - bad_count
    else:
        # data.py의 is_food_related 필터 적용
        try:
            try:
                from festapick.data_pipeline import is_food_related, clean_text
            except ImportError:
                from festapick.data import is_food_related, clean_text
            filtered_rows = []
            for _, r in df.iterrows():
                c = clean_text(r.get("업종", ""))
                n = clean_text(r.get("업소명", ""))
                m = f"{clean_text(r.get('메뉴1', ''))} {clean_text(r.get('메뉴2', ''))}"
                if is_food_related(c, n, m):
                    filtered_rows.append(r)
            df_food = pd.DataFrame(filtered_rows)
            bad_mask = df_food[cat_col].astype(str).apply(lambda x: any(k in x for k in non_food_keywords))
            bad_count = int(bad_mask.sum())
            total_count = len(df_food)
            food_count = total_count
        except Exception:
            bad_mask = df[cat_col].astype(str).apply(lambda x: any(k in x for k in non_food_keywords))
            bad_count = int(bad_mask.sum())
            total_count = len(df)
            food_count = total_count - bad_count

    is_valid = (bad_count == 0)

    report = {
        "file": filepath,
        "total_count": total_count,
        "non_food_count": bad_count,
        "food_count": food_count,
        "passed": is_valid
    }
    return is_valid, report


def validate_wellness() -> Tuple[bool, Dict[str, Any]]:
    """wellness.csv (웰니스 관광지) 무결성을 검증합니다."""
    filepath = find_data_file([
        "festapick/data/wellness.csv",
        "data/wellness.csv",
        "wellness.csv"
    ])
    if not filepath or not os.path.exists(filepath):
        return False, {"error": "wellness.csv 파일을 찾을 수 없습니다."}

    try:
        df = pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="cp949")

    total_count = len(df)
    theme_col = "theme" if "theme" in df.columns else "테마"

    # 필수 4대 테마 키워드: 자연, 스파, 힐링, 한방
    required_keywords = ["자연", "스파", "힐링", "한방"]
    
    # 테마 결측치 확인
    null_theme_count = int(df[theme_col].isna().sum())

    # 각 행의 테마가 필수 테마 중 최소 하나를 포함하는지 확인
    def matches_theme(val: Any) -> bool:
        s = str(val)
        return any(k in s for k in required_keywords)

    valid_theme_mask = df[theme_col].apply(matches_theme)
    valid_theme_count = int(valid_theme_mask.sum())
    theme_ratio = (valid_theme_count / total_count * 100.0) if total_count > 0 else 0.0

    # 테마별 상세 분포 집계
    theme_counts = df[theme_col].value_counts().to_dict()

    is_valid = (null_theme_count == 0) and (valid_theme_count == total_count)

    report = {
        "file": filepath,
        "total_count": total_count,
        "null_theme_count": null_theme_count,
        "valid_theme_count": valid_theme_count,
        "theme_ratio": theme_ratio,
        "theme_distribution": theme_counts,
        "passed": is_valid
    }
    return is_valid, report


def main() -> int:
    print("=" * 72)
    print(" 📊 [FestaPick] 데이터셋 무결성 & 품질 자동 검증 리포트")
    print("=" * 72)

    all_passed = True

    # 1. festivals.csv 검증
    print("\n[1] 🎪 축제 데이터 (festivals.csv) 검증")
    f_ok, f_rep = validate_festivals()
    if "error" in f_rep:
        print(f"  ❌ 에러: {f_rep['error']}")
        all_passed = False
    else:
        print(f"  - 검증 대상 파일: {f_rep['file']}")
        print(f"  - 총 레코드 수: {f_rep['total_count']:,}건")
        
        # 위경도 결측 체크
        c_status = "✅ 정상 (0건)" if f_rep["missing_coords_count"] == 0 else f"❌ 오류 ({f_rep['missing_coords_count']}건 누락)"
        print(f"  - 1) 위도/경도 결측 및 0인 데이터: {c_status}")

        # 대한민국 좌표 범위 체크
        k_status = f"✅ 정상 (100.0% 충족, {f_rep['in_korea_count']:,}/{f_rep['total_count']:,}건)" if f_rep["in_korea_ratio"] == 100.0 else f"❌ 비정상 ({f_rep['in_korea_ratio']:.1f}%)"
        print(f"  - 2) 대한민국 좌표 범위 (위도 33~39, 경도 124~132): {k_status}")

        # 중복 축제 체크
        d_status = "✅ 정상 (0건)" if f_rep["duplicate_count"] == 0 else f"❌ 오류 ({f_rep['duplicate_count']}건 중복)"
        print(f"  - 3) 중복 축제 (축제명+시작일자 기준): {d_status}")

        # 실내외 태그 컬럼 체크
        if f_rep.get("indoor_ok"):
            dist_str = ", ".join([f"{k}: {v:,}건" for k, v in f_rep["indoor_distribution"].items()])
            print(f"  - 4) 실내/야외(is_indoor) 태그 컬럼: ✅ 정상 (100% 매핑 - {dist_str})")
        else:
            print("  - 4) 실내/야외(is_indoor) 태그 컬럼: ❌ 미생성 또는 누락")

        if not f_ok:
            all_passed = False

    # 2. good_price_stores.csv 검증
    print("\n[2] 🍲 착한가격업소 데이터 (good_price_stores.csv) 검증")
    s_ok, s_rep = validate_good_price_stores()
    if "error" in s_rep:
        print(f"  ❌ 에러: {s_rep['error']}")
        all_passed = False
    else:
        print(f"  - 검증 대상 파일: {s_rep['file']}")
        print(f"  - 유효 외식/카페 업소 수: {s_rep['food_count']:,}건")
        
        # 비외식업 업종 배제 체크
        nf_status = "✅ 정상 (0건 잔존, 100% 완전 배제)" if s_rep["non_food_count"] == 0 else f"❌ 오류 ({s_rep['non_food_count']}건 잔존)"
        print(f"  - 1) 비외식업(미용업, 세탁업 등) 배제 검증: {nf_status}")

        if not s_ok:
            all_passed = False

    # 3. wellness.csv 검증
    print("\n[3] 🌿 웰니스 관광지 데이터 (wellness.csv) 검증")
    w_ok, w_rep = validate_wellness()
    if "error" in w_rep:
        print(f"  ❌ 에러: {w_rep['error']}")
        all_passed = False
    else:
        print(f"  - 검증 대상 파일: {w_rep['file']}")
        print(f"  - 총 레코드 수: {w_rep['total_count']:,}건")
        
        # 필수 테마 매핑 체크
        t_status = f"✅ 정상 (100.0% 매핑, {w_rep['valid_theme_count']:,}/{w_rep['total_count']:,}건)" if w_rep["theme_ratio"] == 100.0 else f"❌ 비정상 ({w_rep['theme_ratio']:.1f}%)"
        print(f"  - 1) 4대 필수 테마(자연, 스파, 힐링, 한방) 매핑: {t_status}")
        print("  - 2) 테마별 상세 분포:")
        for t_name, t_cnt in w_rep["theme_distribution"].items():
            print(f"       * {t_name}: {t_cnt}건")

        if not w_ok:
            all_passed = False

    # 최종 결과 판정
    print("\n" + "=" * 72)
    if all_passed:
        print("🎉 모든 데이터셋 무결성 검증 통과 (100% 정상)")
        print("=" * 72)
        return 0
    else:
        print("❌ 일부 데이터셋 검증 항목에서 결함이 발견되었습니다. 위 리포트를 확인하세요.")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
