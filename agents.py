"""
agents.py - Fest & Rest 초개인화 LLM 에이전트 모듈
dotenv를 통해 OPENAI_API_KEY를 로드하고, OpenAI gpt-4o-mini를 호출하여
사용자의 취향, 에너지 상태, 그리고 '사용자 루트 피드백(의견)'을 반영한
에디터 브리핑, 다이내믹 타임테이블, 최적의 이미지 검색 키워드를 생성합니다.
"""

import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

from data_tools import get_dummy_festivals, get_dummy_rests, search_spot_image

# 1. 환경변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _get_fallback_curation(battery: int, companion: str, mood: str, user_feedback: str = "") -> Dict[str, Any]:
    """
    OpenAI API 호출 실패 시 안정적인 데모 시연을 위한 규칙 기반 백업 큐레이션
    """
    festivals = get_dummy_festivals()
    rests = get_dummy_rests()

    if mood == "힙하고 트렌디한":
        primary_fest = festivals[0]
        selected_rest = rests[1]
    elif mood == "자연친화적인":
        primary_fest = festivals[1]
        selected_rest = rests[1]
    else:
        primary_fest = festivals[1]
        selected_rest = rests[0]

    selected_meal = rests[2]

    feedback_notice = ""
    if user_feedback:
        feedback_notice = f"\n> 💬 **남겨주신 의견 반영**: *\"{user_feedback}\"*\n> 보내주신 소중한 의견을 바탕으로 이동 동선과 장소 구성을 더욱 세밀하게 재조정했습니다.\n"

    briefing = f"""### 💌 Fest & Rest 에디터의 맞춤 브리핑

안녕하세요, 여행자님! 오늘 당신의 에너지는 **{battery}%**, 동반자는 **{companion}**, 머물고 싶은 무드는 **'{mood}'**입니다.
{feedback_notice}
> 🎯 **왜 이 코스가 당신의 입맛에 꼭 맞을까요?**  
> 오늘 원하시는 **'{mood}'** 감각을 오롯이 전달하면서도, 배터리({battery}%) 수준에 맞춰 피로가 누적되지 않도록 활력의 축제와 조용한 쉼터의 비율을 황금 밸런스로 조율했습니다.

{companion}과 함께 잊지 못할 편안하고 즐거운 로컬 하루를 즐겨보세요!
"""

    timetable = [
        {
            "step": "Step 1",
            "time": "14:00 - 15:30",
            "category": "FESTIVAL" if battery >= 50 else "REST",
            "title": f"취향의 시작: {primary_fest['name'] if battery >= 50 else selected_rest['name']}",
            "tag": primary_fest["tag"] if battery >= 50 else selected_rest["tag"],
            "desc": "도심의 매력과 편안함을 함께 음미하는 첫 번째 여정입니다.",
            "spot": primary_fest if battery >= 50 else selected_rest
        },
        {
            "step": "Step 2",
            "time": "16:00 - 17:30",
            "category": "REST",
            "title": f"달콤한 충전: {selected_rest['name']}",
            "tag": selected_rest["tag"],
            "desc": f"{selected_rest['description']} 편안한 쉼터에서 지친 몸을 리프레시합니다.",
            "spot": selected_rest
        },
        {
            "step": "Step 3",
            "time": "18:30 - 20:00",
            "category": "DINE & REST",
            "title": f"풍요로운 마무리: {selected_meal['name']}",
            "tag": selected_meal["tag"],
            "desc": "따뜻한 제철 요리와 함께 오늘 나눈 순간들의 여운을 만끽하세요.",
            "spot": selected_meal
        }
    ]

    recommended_spots = []
    seen = set()
    for item in timetable:
        sp = item["spot"]
        if sp["id"] not in seen:
            sp["search_query"] = f"{sp['name']} {mood}"
            sp["display_image"] = search_spot_image(sp["search_query"], sp["fallback_image"])
            recommended_spots.append(sp)
            seen.add(sp["id"])

    return {
        "briefing": briefing,
        "timetable": timetable,
        "recommended_spots": recommended_spots
    }


def generate_curation(battery: int, companion: str, mood: str, user_feedback: str = "") -> Dict[str, Any]:
    """
    LLM(GPT-4o-mini)을 구동하여:
    1. 사용자의 프로필 + '루트에 대한 사용자 의견/피드백'을 종합 분석
    2. 맞춤 에디터 브리핑 생성 (사용자의 의견을 어떻게 반영했는지 설명 포함)
    3. 3단계 다이내믹 타임테이블 선정
    4. 각 스팟에 최적화된 사진 검색 키워드를 LLM이 도출하고 실시간 웹 검색으로 이미지 획득
    """
    festivals = get_dummy_festivals()
    rests = get_dummy_rests()
    all_spots = festivals + rests

    # LLM API 키 미설정 시 백업 실행
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("your_"):
        return _get_fallback_curation(battery, companion, mood, user_feedback)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        # 후보 스팟 메타데이터 요약
        candidates_summary = "\n".join([
            f"- ID: {s['id']}, 이름: {s['name']}, 구분: {s['category']}, 테마: {s['theme']}, 설명: {s['description']}"
            for s in all_spots
        ])

        system_prompt = """당신은 초개인화 로컬 여행 컨시어지 'Fest & Rest'의 수석 에디터 에이전트입니다.
사용자의 에너지 배터리 상태(0~100%), 동반자(혼자/연인/가족), 선호하는 분위기, 그리고 사용자가 직접 남긴 '루트에 대한 의견/피드백'을 정밀하게 분석하세요.

특히 사용자의 피드백이 있는 경우:
- 에디터 브리핑에 "사용자님께서 남겨주신 의견('[피드백 내용 요약]')을 세심하게 반영하여..."와 같이 피드백을 적극적으로 수용해 코스를 어떻게 변경/보완했는지 구체적으로 설명하세요.
- 사용자의 피드백 취지에 맞추어 3단계 타임테이블의 장소 순서와 성격을 유연하게 재배치하세요.

JSON 포맷 규격:
{
  "briefing": "마크다운 형식의 감성적인 에디터 편지. 피드백 반영 사항, 코스 추천 이유, 에너지 및 동반자 배려 사유를 포함할 것",
  "steps": [
    {
      "step": "Step 1",
      "time": "14:00 - 15:30",
      "category": "FESTIVAL 또는 REST 또는 DINE",
      "spot_id": "선택한 장소 ID (fest_1, fest_2, rest_1 등)",
      "title": "한 줄 코스 제목",
      "tag": "매력적인 해시태그",
      "desc": "선정이유와 피드백 반영 포인트 설명",
      "image_search_query": "이 장소의 감성을 가장 잘 보여주는 실제 사진 검색용 한글 키워드 (예: '성수 인디 버스킹 공연', '서울숲 조용한 찻집 티하우스')"
    },
    ... (총 3단계)
  ]
}
반드시 순수 JSON 객체만 응답하세요.
"""

        user_prompt = f"""
[사용자 프로필]
- 오늘 에너지 배터리: {battery}% (낮을수록 휴식 위주, 높을수록 축제 위주)
- 동반자: {companion}
- 선호하는 분위기: {mood}
- 사용자의 추가 의견 / 변경 요청 피드백: "{user_feedback if user_feedback else '특별한 추가 요청 없음 (기본 추천 요청)'}"

[선택 가능한 로컬 스팟 후보]
{candidates_summary}

위 정보를 종합하여 사용자의 의견을 적극 반영한 최적의 3단계 코스를 구성하고 JSON으로 반환해 주세요.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)

        briefing = parsed.get("briefing", "")
        steps = parsed.get("steps", [])

        # 스팟 딕셔너리 매핑
        spot_map = {s["id"]: s for s in all_spots}

        timetable = []
        recommended_spots = []
        seen_spot_ids = set()

        for step_data in steps:
            s_id = step_data.get("spot_id")
            spot_obj = spot_map.get(s_id, all_spots[0]).copy()

            # LLM이 도출한 이미지 검색 키워드로 실시간 사진 검색
            llm_query = step_data.get("image_search_query", f"{spot_obj['name']} {mood}")
            img_url = search_spot_image(llm_query, fallback_url=spot_obj["fallback_image"])

            spot_obj["search_query"] = llm_query
            spot_obj["display_image"] = img_url

            step_data["spot"] = spot_obj
            timetable.append(step_data)

            if spot_obj["id"] not in seen_spot_ids:
                recommended_spots.append(spot_obj)
                seen_spot_ids.add(spot_obj["id"])

        return {
            "briefing": briefing,
            "timetable": timetable,
            "recommended_spots": recommended_spots
        }

    except Exception:
        # 오류 발생 시 안정적인 Fallback 처리
        return _get_fallback_curation(battery, companion, mood, user_feedback)
