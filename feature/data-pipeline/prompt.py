# 시스템 환경 및 표준 출력 설정을 위한 파이썬 표준 라이브러리 sys 모듈을 불러옵니다.
import sys
# 타입 힌트 작성을 위해 typing 모듈에서 Any, List, Optional을 불러옵니다.
from typing import Any, Dict, List, Optional

# 윈도우 환경 콘솔 출력 시 한글 인코딩 깨짐을 방지하기 위해 표준 출력을 UTF-8로 설정합니다.
if sys.stdout.encoding != "utf-8":
    # 표준 출력 인코딩을 utf-8로 재구성합니다.
    sys.stdout.reconfigure(encoding="utf-8")


def get_system_prompt() -> str:
    # 2030 맞춤 여행 큐레이터의 페르소나와 1일 통합 여행 코스 포맷을 정의한 시스템 프롬프트를 생성합니다.
    system_prompt: str = """당신은 트렌디하고 감각적인 센스를 겸비한 '2030 세대 전문 여행 & 축제 큐레이터'입니다.
사용자의 질문과 여행 조건(동행자, 체력 난이도)에 꼭 맞는 최적의 축제와 감성 [1일 통합 여행 코스]를 큐레이션해 주세요.

[필수 출력 포맷 - 1일 통합 여행 코스 4단계]:
1. 🌅 [오전/축제장]
   - 추천 축제명과 핵심 즐길 거리, 개최 기간, 위치(주소)를 매력적으로 소개합니다.
   - 📸 인생샷 스팟: SNS에 올리기 좋은 포토존 위치 및 촬영 꿀팁을 함께 안내합니다.

2. ☕ [오후/감성 카페]
   - RAG 검색 데이터 또는 축제장 반경 3km 이내의 **실제 감성 카페 상호명**을 명시합니다.
   - 예시: "아산 외암 한옥카페", "반포 한강 뷰 디저트 랩" 처럼 구체적 상호명을 사용합니다.
   - ⚠️ "주변 카페", "근처 카페" 처럼 모호한 표현은 절대 사용하지 마세요.
   - 추천 메뉴나 대표 음료도 함께 안내합니다.

3. 🍽️ [저녁/맛집]
   - 착한가격업소 또는 RAG 데이터에서 검색된 **실제 맛집 상호명**과 대표 메뉴를 명시합니다.
   - 예시: "용산 참이슬 감자탕", "해운대 할매국밥" 처럼 구체적 업소명을 사용합니다.
   - ⚠️ 데이터에 없는 가게명을 지어내지 마세요. 없으면 "현장 푸드트럭 및 야시장 먹거리 추천"으로 대체하세요.

4. 🗺️ [이동 동선 & 팁]
   - 축제장 ➔ 카페 ➔ 맛집 순서의 이동 동선과 거리/이동수단을 안내합니다.
   - 🚗 주차 팁: 개최장소 및 도로명주소 기반 인근 공영주차장 이용 권장 또는 대중교통(지하철/버스) 안내
   - 사용자가 선택한 체력 수준(상/중/하)에 따라 동선을 조정합니다:
     * 체력 '하': 동선 최소화, 카페·힐링 중심 코스 (총 이동 2~3km 내외)
     * 체력 '중': 메인 구역 + 포토존 + 카페를 여유롭게 도는 밸런스 코스 (총 이동 3~5km 내외)
     * 체력 '상': 전 구역 + 체험 부스 + 야경까지 알차게 섭렵하는 액티브 코스 (총 이동 5km 이상)

5. 💡 [큐레이터 꿀팁]
   - 동행자(연인/친구/가족 등)에게 꼭 맞춘 실전 꿀팁(준비물, 혼잡 시간대 피하기 등)을 안내합니다.

[엄격한 제약 조건 및 답변 원칙]:
- 반드시 제공된 [참고 데이터(Context)]의 내용에 기반하여 사실에 입각해 답변하세요.
- 데이터에 없는 사실(업소명, 주소, 메뉴 등)을 임의로 날조(할루시네이션)하지 마세요.
- 카페·맛집 이름을 "주변 카페", "근처 맛집" 처럼 모호하게 표현하지 마세요. RAG 데이터에 실제 업소명이 있으면 반드시 그 이름을 그대로 사용하고, 없으면 "현장 부스 먹거리" 등으로 대체하세요.
- 말투는 친절하고 센스 넘치는 2030 맞춤형 톤앤매너(해요체, 감각적인 이모지 활용)를 유지하세요."""

    # 정돈된 시스템 프롬프트 문자열을 반환합니다.
    return system_prompt.strip()


def build_user_prompt(
    user_query: str,
    context_documents: List[Any],
    companion: Optional[str] = "연인",
    stamina_level: Optional[str] = "중"
) -> str:
    # 전달받은 참고 문서 리스트가 비어있는 경우 기본 안내 문구를 설정합니다.
    if not context_documents:
        # 검색 결과가 없을 때의 대체 컨텍스트 텍스트를 구성합니다.
        context_str: str = "검색된 관련 축제 정보가 없습니다."
    # 참고 문서 리스트에 데이터가 존재하는 경우
    else:
        # 각 문서 텍스트를 보기 편하게 정리하여 담을 임시 리스트를 생성합니다.
        formatted_contexts: List[str] = []
        # 전달받은 문서들을 인덱스와 함께 하나씩 순회합니다.
        for idx, doc in enumerate(context_documents, start=1):
            # 만약 전달된 객체가 LangChain Document 객체(page_content 속성 보유)인 경우
            if hasattr(doc, "page_content"):
                # page_content 속성값을 추출합니다.
                content_text: str = str(doc.page_content).strip()
            # 만약 전달된 객체가 딕셔너리 형태이고 'page_content' 키가 있는 경우
            elif isinstance(doc, dict) and "page_content" in doc:
                # 딕셔너리에서 page_content 값을 추출합니다.
                content_text = str(doc["page_content"]).strip()
            # 일반 문자열 또는 기타 객체인 경우
            else:
                # 문자열 형태로 안전하게 변환하고 공백을 제거합니다.
                content_text = str(doc).strip()

            # 문서 번호 헤더와 함께 본문을 묶어 리스트에 추가합니다.
            formatted_contexts.append(f"[축제 정보 {idx}]\n{content_text}")

        # 모든 참고 문서들을 구분선(\n\n)으로 결합하여 하나의 통합 컨텍스트 문자열을 완성합니다.
        context_str = "\n\n".join(formatted_contexts)

    # 동행자 정보가 None이거나 비어있으면 기본값 '친구/연인'으로 설정합니다.
    companion_val: str = companion if companion else "친구/연인"
    # 체력 수준 정보가 None이거나 비어있으면 기본값 '보통(중)'으로 설정합니다.
    stamina_val: str = stamina_level if stamina_level else "보통(중)"

    # 사용자 질문, 검색된 컨텍스트, 맞춤 여행자 프로필 및 1일 통합 여행 코스 포맷을 결합한 유저 프롬프트를 구성합니다.
    user_prompt: str = f"""아래 제공된 [참고 데이터(Context)]를 바탕으로 사용자의 조건에 꼭 맞는 [1일 통합 여행 코스]를 큐레이션해 주세요.

[사용자 프로필 및 요청 사항]:
- 사용자 질문: "{user_query}"
- 동행자: {companion_val}
- 희망 체력 소모 수준: {stamina_val}

[참고 데이터(Context) - RAG 검색 결과]:
--------------------------------------------------
{context_str}
--------------------------------------------------

[필수 출력 포맷 - 아래 5단계 순서와 이모지 헤더를 반드시 사용해 주세요]:

1. 🌅 [오전/축제장]
   축제명, 핵심 즐길 거리, 기간 및 위치를 소개합니다.
   📸 인생샷 스팟: Context에 나온 포토존 정보를 그대로 활용하세요.

2. ☕ [오후/감성 카페]
   Context의 '추천 카페' 항목에 나온 **실제 카페 상호명**을 명시하고 추천 메뉴를 안내합니다.
   ※ 반드시 구체적 상호명을 사용하세요. 예: "아산 외암 한옥카페", "서래마을 루프탑 카페 A"
   ※ Context에 카페명이 없으면 "현장 주변 감성 카페 탐방 코스 (현장 확인 권장)"으로 대체하세요.
   ※ "주변 카페", "근처 카페", "카페 추천" 같은 모호한 표현은 절대 금지입니다.

3. 🍽️ [저녁/맛집]
   Context의 착한가격업소 또는 맛집 데이터에서 **실제 상호명과 대표 메뉴**를 안내합니다.
   ※ Context에 맛집 데이터가 없으면 "현장 푸드트럭 및 인근 골목 맛집 탐방 추천"으로 대체하세요.

4. 🗺️ [이동 동선 & 팁]
   축제장 ➔ 카페 ➔ 맛집 순서의 실제 이동 동선과 이동수단을 안내합니다.
   체력 수준({stamina_val})에 맞춰 동선 강도를 조절해 주세요.
   🚗 주차 팁: Context의 도로명주소 기반 인근 공영주차장 또는 대중교통 안내를 포함하세요.

5. 💡 [큐레이터 꿀팁]
   동행자({companion_val})에게 꼭 맞는 준비물, 혼잡 시간대 피하기, 현장 팁을 안내합니다.

⚠️ 핵심 주의사항:
- Context에 실제 업소명·주소·메뉴가 있으면 반드시 그대로 사용하세요.
- Context에 없는 정보는 절대 지어내지 마세요 (할루시네이션 금지).
- "주변 카페", "근처 맛집" 같은 모호한 표현 대신 실제 상호명 또는 명확한 대체 문구를 사용하세요."""

    # 완성된 사용자 프롬프트 문자열을 반환합니다.
    return user_prompt.strip()



def get_storytelling_system_prompt() -> str:
    """여행 기획 전문 AI 수석 에디터의 페르소나와 감성 스토리텔링 여행 코스 작성 지침을 반환합니다."""
    return """당신은 트렌디하고 감성적인 여행 기획 전문 AI 수석 에디터입니다.
제공된 RAG 검색 데이터(주차장, 축제, 착한가격업소 맛집, 감성 카페, 웰니스 힐링지)를 바탕으로,
여행자가 하루 동안 현장을 직접 걷고 즐기는 듯한 풍부한 감성 스토리텔링 여행 에세이를 작성해주세요.

[필수 구성 요소]
1. 🌿 코스 개요: 여행의 테마와 한 줄 요약
2. 🌅 오전 (도착 & 준비):
   - 주차장 정보: 실제 주차장명, 주소, 주차 팁 및 이동 동선 안내
   - 축제 즐기기: 축제명, 핵심 볼거리, 인생샷 스팟 및 생생한 현장 분위기 묘사
3. 🍽️ 점심 (로컬 미식):
   - 착한가격업소(맛집) 연계 규칙 (엄격 준수):
     * 제공된 추천 음식점(착한가격업소)이 3곳이면 3곳 모두, 2곳이면 2곳, 1곳이면 1곳 등 **제공된 추천 개수만큼 모든 식당의 실제 상호명, 대표 메뉴(가격 포함), 가성비 포인트, 방문 추천 이유를 스토리텔링 본문에 각각 빠짐없이 모두 포함**해주세요. (여행객이 취향에 맞게 메뉴를 고를 수 있도록 다채롭게 비교 및 소개)
4. ☕ 오후 (휴식 & 웰니스 힐링):
   - 감성 카페: 실제 카페 상호명(또는 티하우스), 대표 음료 및 분위기 묘사
   - 웰니스(힐링지) 연계 규칙 (엄격 준수):
     * 웰니스 데이터가 3곳 제공된 경우: 여행객의 취향에 맞춰 선택할 수 있도록 [자연/숲치유, 뷰티/스파, 힐링/명상 등] 다양한 테마의 3곳을 모두 에세이에 매력적으로 비교 소개해주세요.
     * 웰니스 데이터가 1~2곳인 경우: 해당 명소의 치유 프로그램과 시설 특징을 더 깊이 있고 상세하게 묘사해주세요.
     * 관내 웰니스 데이터가 0건(없음)인 경우: 가상의 시설을 절대 지어내지 말고, "관내 등록된 웰니스 공식 인증 명소가 없으므로, 축제 행사장 주변의 자연 산책로나 공원에서 가벼운 산책으로 여독을 풀어보세요"와 같이 솔직하고 따뜻한 대체 안내를 작성해주세요.
5. 💡 에디터의 동선 & 주차 꿀팁: 혼잡 시간 피하는 법 및 이동 팁

[동행자(Companion)별 페르소나 및 서술 문체 규칙 (최우선 엄격 준수)]
여행자 프로필에 명시된 '추천 동행자' 유형에 따라 글 전체의 시점, 감정선, 표현, 문체를 완전히 차별화하여 서술해야 합니다:
1. '연인':
   - 톤앤매너: 달콤한 데이트 감성, 설렘, 로맨틱한 분위기, 둘만의 감성 인생샷, 다정하고 속삭이듯 따뜻한 대화 위주의 문체.
   - ⚠️ 절대 주의: '친구', '아이들', '가족' 등 연인이 아닌 단어 사용 절대 금지! "연인의 손을 꼭 잡고", "사랑하는 사람과 함께", "둘만의 오붓한 순간", "로맨틱한 데이트" 등의 표현을 적극 활용하세요.
2. '가족':
   - 톤앤매너: 아이나 부모님(어르신)과 함께하는 편안함, 안전한 보행 동선, 따뜻하고 든든한 가족 식사, 남녀노소 세대 공감 힐링 문체.
   - 표현: "아이들의 해맑은 웃음소리", "부모님 모시고 걷기 좋은 길", "온 가족이 정답게 둘러앉아 나누는 따뜻한 한 상", "남녀노소 모두가 행복한 시간" 등.
3. '혼자':
   - 톤앤매너: 나 홀로 온전한 자유와 여유, 깊은 사색과 쉼, 번잡함을 벗어난 조용한 티타임과 내면의 회복·자아 충전에 집중하는 1인 힐링 문체.
   - ⚠️ 절대 주의: '친구와', '연인과', '누군가와 나누며', '함께' 등 복수 표현 절대 금지! 오롯이 나 자신에게 집중하는 1인칭 사색/독백 스타일로 서술하세요.
4. '친구':
   - 톤앤매너: 활기찬 청춘 에너지, 유쾌한 추억 만들기, 시끌벅적한 맛집 탐방, 웃음과 장난기 넘치는 에피소드 중심 문체.
   - 표현: "찐친들과 나누는 유쾌한 수다", "서로 찍어주는 인생샷과 장난스런 포즈", "시끌벅적 맛있는 먹방 투어" 등.

[작성 톤앤매너]
- 건조한 리스트 나열이 아닌, 현장의 소리와 냄새가 느껴지는 생생한 에세이/여행 가이드북 스타일로 서술해주세요.
- 각 장소의 실제 고유 정보(명칭, 주소, 메뉴, 가격, 특징)가 자연스럽게 본문에 녹아들도록 작성해주세요.
- 데이터에 없는 정보는 절대 임의로 지어내지 마세요 (할루시네이션 금지).
- 가독성을 높이기 위해 매력적인 소제목, 감각적인 이모지와 마크다운 서식을 활용하세요."""


def build_storytelling_user_prompt(course_package: Dict[str, Any], companion: str = "친구/연인") -> str:
    """course_package에 담긴 실제 4단계 타임라인 데이터를 정밀 바인딩하여 LLM 스토리텔링 프롬프트를 구성합니다."""
    timeline = course_package.get("timeline", [])
    step_dict = {item.get("step"): item for item in timeline}

    p = step_dict.get(1, {})
    f = step_dict.get(2, {})
    r = step_dict.get(3, {})
    w = step_dict.get(4, {})

    fest_name = course_package.get("festival_name", f.get("title", "지역 축제"))
    stamina = course_package.get("user_stamina", "중")
    sigungu = course_package.get("target_sigungu", "")
    region = course_package.get("target_region", "")

    # 식당 다중 데이터 포맷팅 (최대 3곳 추천 개수대로 모두 반영)
    raw_rests = r.get("restaurants", [])
    real_rests = [
        s for s in raw_rests
        if not s.get("is_empty") and "없음" not in s.get("title", "") and not s.get("title", "").startswith("※")
    ]
    if not real_rests and r.get("restaurant"):
        single_r = r.get("restaurant", {})
        if not single_r.get("is_empty") and "없음" not in single_r.get("title", "") and not single_r.get("title", "").startswith("※"):
            real_rests = [single_r]

    if real_rests:
        r_lines = []
        for idx, st in enumerate(real_rests[:3], 1):
            m_parts = []
            if st.get("menu1"):
                m_parts.append(f"{st.get('menu1')} ({st.get('price1')}원)" if st.get("price1") else st.get("menu1"))
            if st.get("menu2"):
                m_parts.append(f"{st.get('menu2')} ({st.get('price2')}원)" if st.get("price2") else st.get("menu2"))
            m_str = ", ".join(m_parts) or st.get("menu", "가성비 추천 메뉴")
            r_lines.append(f"   [{idx}번 맛집]: {st.get('title')} (분류: {st.get('category', '착한가격업소')}, 주소: {st.get('location')}) - 대표 메뉴: {m_str} | 연락처: {st.get('phone', '현장 확인')}")
        rest_data_str = "\n".join(r_lines)
        rest_guide_instruction = f"※ 착한가격업소 맛집이 {len(real_rests[:3])}곳 제공되었습니다. 제공된 {len(real_rests[:3])}곳 모두 본문 미식 코스에 빠짐없이 각각의 상호명, 대표 메뉴(가격 포함), 가성비 포인트를 소개해 주세요."
    else:
        rest_data_str = "   - 관내 공식 착한가격업소 등록 데이터 없음 (축제장 인근 로컬 식당 및 먹거리 장터 추천)"
        rest_guide_instruction = "※ 관내 공식 착한가격업소가 없으므로, 축제장 내 먹거리 부스나 주변 로컬 식당을 이용하도록 자연스럽게 안내하세요."

    cafe_info = r.get("cafe", {})
    cafe_title = cafe_info.get("title", "주변 감성 카페")
    cafe_loc = cafe_info.get("location", "")
    cafe_menu = cafe_info.get("menu", "시그니처 커피 & 디저트")
    cafe_reason = cafe_info.get("reason", "")

    spots = f.get("photo_spots", [])
    spots_str = ", ".join(spots) if isinstance(spots, list) else str(spots)

    # 웰니스 다중 데이터 포맷팅
    w_places = w.get("wellness_places", [])
    real_w_places = [wp for wp in w_places if not wp.get("is_empty") and "없음" not in wp.get("title", "") and not wp.get("title", "").startswith("※")]

    if len(real_w_places) >= 3:
        w_guide_instruction = "※ 웰니스 명소가 3곳 제공되었습니다. 여행객의 취향/체력에 맞춰 선택할 수 있도록 [자연/숲치유, 뷰티/스파, 힐링/명상 등] 3곳의 상호명과 매력을 모두 본문에 소개해 주세요."
        w_lines = []
        for idx, wp in enumerate(real_w_places[:3], 1):
            w_lines.append(f"   [{idx}번 명소]: {wp.get('title')} (테마: {wp.get('theme', '힐링')}, 주소: {wp.get('location')}) - 프로그램: {wp.get('healing_programs')}")
        w_data_str = "\n".join(w_lines)
    elif len(real_w_places) in [1, 2]:
        w_guide_instruction = "※ 웰니스 명소가 1~2곳 제공되었습니다. 해당 명소의 치유 프로그램과 시설 공간 특징을 더욱 깊이 있고 상세하게 묘사해 주세요."
        w_lines = []
        for idx, wp in enumerate(real_w_places, 1):
            w_lines.append(f"   [{idx}번 명소]: {wp.get('title')} (테마: {wp.get('theme', '힐링')}, 주소: {wp.get('location')}) - 개요: {wp.get('overview')} | 프로그램: {wp.get('healing_programs')}")
        w_data_str = "\n".join(w_lines)
    else:
        w_guide_instruction = "※ 해당 시군구 관내 등록된 한국관광공사 웰니스 관광지가 없습니다. 가상의 시설을 절대 지어내지 말고, 축제 행사장 주변의 자연 산책로나 공원에서 가벼운 산책으로 여독을 푸는 솔직한 대체 힐링 코스로 작성하세요."
        w_data_str = f"   - 관내 공식 웰니스 등록 데이터 없음 (축제장 주변 자연 산책로 추천)"

    companion_val = companion if companion else course_package.get("companion", "연인")
    if "연인" in companion_val:
        companion_guide = "❤️ [동행 페르소나 지침 - 연인]: 달콤한 데이트 감성, 설렘과 로맨틱한 무드를 극대화하세요. 둘만의 인생 커플샷, 다정한 대화와 눈맞춤에 집중하며, 본문에 '친구'나 '가족'이라는 단어를 절대 사용하지 마세요!"
    elif "가족" in companion_val:
        companion_guide = "👨‍👩‍👧‍👦 [동행 페르소나 지침 - 가족]: 아이나 부모님과 함께하는 편안함과 안전한 동선, 남녀노소 세대 공감과 따뜻한 가족 식사 및 힐링의 정서를 풍부하게 담아내세요."
    elif "혼자" in companion_val:
        companion_guide = "🧘 [동행 페르소나 지침 - 혼자]: 타인의 방해 없는 나 홀로 온전한 여유, 사색과 쉼, 조용한 티타임과 내면의 회복에 집중하는 1인 힐링 문체로 작성하세요. 복수형 표현('친구와' 등)을 절대 쓰지 마세요."
    else:
        companion_guide = "🎉 [동행 페르소나 지침 - 친구]: 찐친들과 함께하는 활기찬 청춘 에너지, 유쾌한 추억 만들기, 장난스런 인생샷과 시끌벅적 맛있는 먹방 투어 문체로 작성하세요."

    prompt = f"""[여행 조건 및 프로필]:
- 축제 지역: {region} {sigungu}
- 메인 축제명: {fest_name}
- 여행자 체력 수준: '{stamina}' (난이도 맞춤)
- 추천 동행자: {companion_val}
- 🚨 동행 맞춤 문체 지침: {companion_guide}

[RAG 검색 검증 데이터 (100% 동일 관내 실제 데이터)]:
1. 🚗 주차장 (Step 1):
   - 주차장명: {p.get('title', '공영주차장')}
   - 위치/주소: {p.get('location', '')}
   - 요금/정보: {p.get('fee_info', '무료/유료')}
   - 연락처: {p.get('phone', '')}
   - 체력 팁: {p.get('stamina_tip', '')}

2. 🎉 메인 축제 (Step 2):
   - 축제명: {f.get('title', fest_name)}
   - 개최장소: {f.get('location', '')} ({f.get('venue', '')})
   - 축제기간: {f.get('period', '')}
   - 주요 프로그램: {f.get('programs', '')}
   - 인생샷 포토스팟: {spots_str}
   - 입장료: {f.get('fee', '현장 안내')}
   - 체력 팁: {f.get('stamina_tip', '')}

3. 🍽️ 착한가격업소 맛집 & 감성 카페 (Step 3 - 추천 개수대로 모두 반영):
{rest_data_str}
   {rest_guide_instruction}
   - 카페 상호명: {cafe_title}
   - 카페 위치: {cafe_loc}
   - 카페 대표 메뉴/특징: {cafe_menu} ({cafe_reason})
   - 체력 팁: {r.get('stamina_tip', '')}

4. 🌿 웰니스 힐링 명소 (Step 4 - 최대 3곳 연계):
{w_data_str}
   {w_guide_instruction}
   - 체력 팁: {w.get('stamina_tip', '')}

위의 실제 고유 정보를 자연스럽게 녹여내고, 지정된 **동행자({companion_val}) 전용 톤앤매너**를 철저히 반영하여 생생하고 매력적인 감성 스토리텔링 여행 코스를 작성해주세요."""

    return prompt.strip()


def generate_storytelling_fallback(course_package: Dict[str, Any], companion: str = "연인") -> str:
    """API 호출 불가 시에도 100% 완벽한 고품질 에세이 줄글을 즉시 제공하는 룰 기반 스토리텔링 폴백 생성기입니다.
    동행자(연인, 가족, 혼자, 친구)에 따라 시점, 어조, 문체, 추천 테마가 완전히 차별화됩니다."""
    timeline = course_package.get("timeline", [])
    step_dict = {item.get("step"): item for item in timeline}

    p = step_dict.get(1, {})
    f = step_dict.get(2, {})
    r = step_dict.get(3, {})
    w = step_dict.get(4, {})

    fest_title = f.get("title", course_package.get("festival_name", "지역 축제"))
    sigungu = course_package.get("target_sigungu", "")
    stamina = course_package.get("user_stamina", "중")
    comp = companion if companion else course_package.get("companion", "연인")

    # 식당 다중 데이터 포맷팅
    raw_rests = r.get("restaurants", [])
    real_rests = [
        s for s in raw_rests
        if not s.get("is_empty") and "없음" not in s.get("title", "") and not s.get("title", "").startswith("※")
    ]
    if not real_rests and r.get("restaurant"):
        single_r = r.get("restaurant", {})
        if not single_r.get("is_empty") and "없음" not in single_r.get("title", "") and not single_r.get("title", "").startswith("※"):
            real_rests = [single_r]

    def fmt_menu(st):
        m = st.get("menu1") or st.get("menu", "대표 가성비 메뉴")
        pr = f" ({st.get('price1')}원)" if st.get("price1") else ""
        return f"{m}{pr}"

    cafe = r.get("cafe", {})
    cafe_title = cafe.get("title") or "로컬 감성 카페"
    cafe_menu = cafe.get("menu", "시그니처 티 & 디저트")

    spots = f.get("photo_spots", [])
    spot_text = f"'{spots[0]}'" if isinstance(spots, list) and spots else "주요 행사장 포토존"

    # 웰니스 다중 데이터 분기 처리
    w_places = w.get("wellness_places", [])
    real_w_places = [wp for wp in w_places if not wp.get("is_empty") and "없음" not in wp.get("title", "") and not wp.get("title", "").startswith("※")]

    # ── 동행자(Companion)별 4대 맞춤형 톤앤매너 분기 생성 ──
    if "연인" in comp:
        theme_title = f"# ❤️ [{sigungu}] 연인과 함께 걷는 {fest_title} 로맨틱 힐링 데이트"
        overview_theme = "두 사람만의 달콤한 설렘과 로맨틱한 낭만, 그리고 자연 속 오붓한 쉼"
        overview_summary = f"[{sigungu}]의 설레는 축제 현장부터 오붓한 로컬 맛집, 감성 티타임과 로맨틱 웰니스까지 연인과 함께 둘만의 소중한 추억을 남기는 맞춤 데이트 여정"
        morning_lead = f"상쾌한 아침 공기 속에서 연인의 손을 꼭 잡고 오늘의 첫 기착지인 **[{p.get('title', '인근 주차장')}]**({p.get('location', '')})에 도착합니다. 복잡한 인파를 피해 여유롭게 차를 대고, 설레는 미소와 함께 축제장으로 걸어갑니다."
        morning_fest = f"축제장에 들어서자마자 화사하게 펼쳐지는 **[{fest_title}]**의 로맨틱한 풍경이 두 사람을 맞이합니다. {spot_text}에서 서로의 가장 사랑스러운 모습을 카메라에 담아주고, 다정한 커플 인생샷을 남기며 둘만의 잊지 못할 낭만을 만끽합니다."
        lunch_intro = f"축제장을 다정하게 거닐며 둘만의 감성을 채운 뒤, 마주 앉아 오붓하게 식사를 즐길 수 있는 행정안전부 인증 **[{sigungu}] 착한가격업소 맛집 {len(real_rests[:3])}선**으로 발걸음을 옮깁니다."
        cafe_desc = f"식사 후 오후의 나른한 햇살을 받으며 **[{cafe_title}]**의 아늑한 창가 테이블에 나란히 앉습니다. 향긋한 {cafe_menu}를 사이에 두고 서로의 눈을 맞추며 달콤한 귓속말과 정다운 대화를 나눕니다."
        wellness_intro = f"데이트의 마지막 여정으로, 두 사람의 몸과 마음에 온전한 편안함을 더해줄 **[{sigungu}] 로맨틱 웰니스 힐링 코스**로 향합니다."
        tip_companion = "❤️ 둘만의 데이트 꿀팁: 커플 사진 찍기 좋은 삼각대를 챙기시고, 노을 질 무렵 웰니스 산책로를 걸으면 잊지 못할 로맨틱한 순간이 완성됩니다."
    elif "가족" in comp:
        theme_title = f"# 👨‍👩‍👧‍👦 [{sigungu}] 온 가족이 함께 행복을 채우는 {fest_title} 패밀리 힐링 로드"
        overview_theme = "남녀노소 세대 공감, 부모님과 아이 모두가 편안하고 안전한 따뜻한 가족 나들이"
        overview_summary = f"[{sigungu}] 축제 현장의 풍성한 체험부터 어르신과 아이 입맛을 모두 사로잡는 착한 맛집, 넉넉한 쉼터까지 온 가족이 웃음 짓는 힐링 여정"
        morning_lead = f"부모님의 편안한 보행과 아이들의 안전을 고려하여 주차가 가장 편리한 **[{p.get('title', '인근 주차장')}]**({p.get('location', '')})에 여유롭게 입차합니다. 짐을 챙기고 온 가족이 손을 잡고 활기차게 축제장으로 걸어갑니다."
        morning_fest = f"현장에 들어서자 **[{fest_title}]**의 풍성한 볼거리와 세대 공감 문화 프로그램에 온 가족의 눈길이 머뭅니다. {spot_text}에서 할머니, 할아버지, 아이들이 다 함께 모여 환한 웃음으로 가족 단체 사진을 남깁니다."
        lunch_intro = f"신나게 축제를 체험한 후, 아이도 어르신도 모두 든든하게 속을 채울 수 있는 행정안전부 인증 **[{sigungu}] 착한가격업소 가족 맛집 {len(real_rests[:3])}선**을 제안합니다."
        cafe_desc = f"식사 후 온 가족이 편안하게 쉴 수 있는 **[{cafe_title}]**의 널찍한 패밀리 좌석으로 향합니다. 아이들이 좋아하는 디저트와 어르신을 위한 따뜻한 {cafe_menu}를 곁들이며 도란도란 가족의 정을 나눕니다."
        wellness_intro = f"가족 모두의 지친 기력을 북돋우고 안전하게 쉴 수 있는 **[{sigungu}] 가족 맞춤형 웰니스 쉼터**로 발걸음을 옮깁니다."
        tip_companion = "👨‍👩‍👧‍👦 가족 케어 꿀팁: 완만한 평지 위주의 동선으로 구성되었으며, 아이들을 위한 여벌 옷과 어르신을 위한 가벼운 외투를 챙기시면 더욱 쾌적합니다."
    elif "혼자" in comp:
        theme_title = f"# 🧘 [{sigungu}] 오롯이 나에게 집중하는 {fest_title} 사색과 치유의 홀로 여행"
        overview_theme = "일상의 소음을 내려놓고 온전히 나만의 속도로 즐기는 사색과 내면의 회복"
        overview_summary = f"[{sigungu}] 축제의 활기 속에서 나만의 관점으로 풍경을 기록하고, 정갈한 1인 로컬 미식과 고요한 웰니스에서 온전한 쉼을 누리는 나 홀로 여정"
        morning_lead = f"누구의 눈치도 볼 필요 없이 나만의 자유로운 호흡으로 **[{p.get('title', '인근 주차장')}]**({p.get('location', '')})에 차를 댑니다. 이어폰을 꽂고 좋아하는 음악을 들으며 호젓하게 축제장으로 발걸음을 옮깁니다."
        morning_fest = f"**[{fest_title}]** 현장 속을 천천히 거닐며 시선이 닿는 대로 자유롭게 관람합니다. {spot_text} 앞에 서서 고요히 풍경을 바라보며 오롯이 나만의 감성을 담아 멋진 풍경 샷을 남깁니다."
        lunch_intro = f"기분 좋은 산책 후, 혼자서도 부담 없이 정갈한 한 상을 편안하게 즐길 수 있는 행정안전부 인증 **[{sigungu}] 1인 친화 착한가격업소 {len(real_rests[:3])}선**을 제안합니다."
        cafe_desc = f"식사를 마치고 고즈넉한 **[{cafe_title}]**의 조용한 1인 창가 석에 자리를 잡습니다. 향긋한 {cafe_menu}를 천천히 음미하며 다이어리를 정리하거나 생각에 잠기는 온전한 휴식을 누립니다."
        wellness_intro = f"복잡했던 마음을 깨끗이 비워내고 스스로를 다독여주는 **[{sigungu}] 1인 사색 웰니스 명소**로 향합니다."
        tip_companion = "🧘 나 홀로 꿀팁: 타인의 속도에 맞출 필요 없이 내 체력에 맞춰 머무르고 싶은 장소에서 충분히 머물며 나만의 쉼표를 찍어보세요."
    else:  # 친구
        theme_title = f"# 🎉 [{sigungu}] 찐친들과 함께 떠나는 {fest_title} 유쾌 발랄 힐링 로드"
        overview_theme = "청춘의 에너지와 멈추지 않는 웃음, 잊지 못할 찐친들과의 추억 만들기"
        overview_summary = f"[{sigungu}] 축제의 짜릿한 볼거리부터 가성비 넘치는 찐맛집 먹방 투어, 감성 카페 수다와 웰니스까지 친구들과 하루 종일 웃음꽃을 피우는 여정"
        morning_lead = f"차 안에서부터 좋아하는 음악을 크게 틀고 신나게 달려와 **[{p.get('title', '인근 주차장')}]**({p.get('location', '')})에 주차를 마칩니다. 서로의 옷차림을 칭찬하며 유쾌한 수다와 함께 축제장으로 뛰어갑니다."
        morning_fest = f"열기가 가득한 **[{fest_title}]** 현장에 들어서자마자 친구들과 신나게 환호합니다. {spot_text}에서 익살스러운 포즈와 장난기 가득한 표정으로 서로의 인생샷을 찍어주며 배꼽을 잡고 웃습니다."
        lunch_intro = f"신나게 웃고 떠드느라 출출해진 배를 채우기 위해, 친구들과 테이블 가득 푸짐하게 나누어 먹기 좋은 행정안전부 인증 **[{sigungu}] 착한가격업소 맛집 {len(real_rests[:3])}선**으로 향합니다."
        cafe_desc = f"식사 후 끊이지 않는 수다를 이어가기 위해 핫플레이스인 **[{cafe_title}]**로 자리를 옮깁니다. 시원한 {cafe_menu}와 달콤한 디저트를 펼쳐놓고 방금 찍은 사진들을 공유하며 즐거운 에너지를 나눕니다."
        wellness_intro = f"신나게 달린 하루의 피로를 풀고 내일의 에너지를 충전하기 위해 **[{sigungu}] 친구 맞춤형 힐링 명소**로 향합니다."
        tip_companion = "🎉 친구 꿀팁: 보조 배터리를 넉넉히 챙겨 끊임없이 사진과 영상을 남기시고, 다양한 메뉴를 주문해 골고루 맛보는 것을 추천합니다."

    # 점심 식당 다중 목록 생성
    if len(real_rests) >= 3:
        r1, r2, r3 = real_rests[0], real_rests[1], real_rests[2]
        lunch_section = f"""{lunch_intro}

1. **[{r1.get('title')}]**({r1.get('location')}) : 대표 메뉴인 **{fmt_menu(r1)}**으로 유명한 곳으로, 푸짐한 양과 정갈한 손맛으로 방문객 모두의 입맛을 사로잡습니다.
2. **[{r2.get('title')}]**({r2.get('location')}) : 정성 가득한 **{fmt_menu(r2)}**을 착한 가격에 제공하여 현지 주민들도 즐겨 찾는 검증된 가성비 맛집입니다.
3. **[{r3.get('title')}]**({r3.get('location')}) : 알찬 구성의 **{fmt_menu(r3)}**이 매력적인 곳으로, 축제 관람 후 든든하게 에너지를 재충전하기에 안성맞춤입니다."""
    elif len(real_rests) == 2:
        r1, r2 = real_rests[0], real_rests[1]
        lunch_section = f"""{lunch_intro}

1. **[{r1.get('title')}]**({r1.get('location')}) : 대표 메뉴인 **{fmt_menu(r1)}**으로 유명하며, 착한 가격에 정갈하고 든든한 식사를 즐길 수 있습니다.
2. **[{r2.get('title')}]**({r2.get('location')}) : 현지 주민들이 추천하는 **{fmt_menu(r2)}** 맛집으로, 깊은 손맛과 넉넉한 인심이 돋보입니다."""
    elif len(real_rests) == 1:
        r1 = real_rests[0]
        lunch_section = f"""{lunch_intro}
대표 추천 식당인 **[{r1.get('title')}]**({r1.get('location')})의 시그니처 메뉴인 **{fmt_menu(r1)}**은 정갈하고 푸짐한 손맛으로 여행자의 입맛을 단번에 사로잡습니다. 합리적인 가격에 든든하게 속을 채우며 로컬의 따뜻한 온정을 느껴보세요."""
    else:
        lunch_section = f"""축제장을 기분 좋게 둘러본 뒤, 현장 특유의 활기가 넘치는 로컬 먹거리 장터와 주변 식당가로 발걸음을 옮깁니다. 갓 조리된 신선한 향토 먹거리와 따뜻한 음식들로 허기를 달래며 기분 좋은 점심 시간을 즐겨보세요."""

    # 웰니스 힐링 섹션 구성
    if len(real_w_places) >= 3:
        w1, w2, w3 = real_w_places[0], real_w_places[1], real_w_places[2]
        wellness_section = f"""{wellness_intro} 취향에 맞춰 선택할 수 있는 **[{sigungu}] 대표 웰니스 3선**을 소개합니다.

1. **[{w1.get('title')}]**({w1.get('location')}) : `{w1.get('theme', '힐링/스파')}` 테마로, {w1.get('healing_programs', '편안한 치유 프로그램')}을 체험하며 몸과 마음의 긴장을 풀 수 있습니다.
2. **[{w2.get('title')}]**({w2.get('location')}) : `{w2.get('theme', '자연/숲치유')}` 명소로, 맑은 자연 속 완만한 산책로를 걸으며 심신을 정화합니다.
3. **[{w3.get('title')}]**({w3.get('location')}) : `{w3.get('theme', '힐링/명상')}` 공간으로, 조용하고 아늑한 쉼터에서 하루의 피로를 녹여냅니다."""
    elif len(real_w_places) in [1, 2]:
        w1 = real_w_places[0]
        wellness_section = f"""{wellness_intro}
한국관광공사 등록 웰니스 명소인 **[{w1.get('title')}]**({w1.get('location')})은 `{w1.get('theme', '힐링/치유')}` 테마의 대표 명소로, {w1.get('overview', '자연 속 아늑한 치유 공간')}을 만끽할 수 있습니다. {w1.get('healing_programs', '피톤치드 산책과 힐링 프로그램')}에 참여하며 맑은 공기를 깊게 들이마시면 일상의 스트레스가 말끔히 씻겨 내려갑니다."""
    else:
        wellness_section = f"""오후의 여유로운 티타임을 즐긴 후, 축제 행사장 주변의 고즈넉한 자연 산책로로 발걸음을 옮깁니다. 현재 [{sigungu}] 관내에 공인 등록된 한국관광공사 웰니스 관광지는 없지만, 축제장 인근의 맑은 바람과 녹음이 우거진 공원길을 가볍게 거니는 것만으로도 충분히 지친 여독을 풀고 기분 좋은 마무리를 지을 수 있습니다."""

    return f"""{theme_title}

---

### 1. 코스 개요
* **여행 테마**: {overview_theme}
* **한 줄 요약**: {overview_summary}

---

### 2. 오전 (도착 & 준비) : 설레는 여정의 시작
{morning_lead}

{morning_fest}

---

### 3. 점심 (로컬 미식) : 현지인이 인정하는 착한 한 상
{lunch_section}

---

### 4. 오후 (휴식 & 웰니스 힐링) : 향긋한 차 한 잔과 깊은 쉼
{cafe_desc}

{wellness_section}

---

### 5. 💡 에디터의 맞춤 꿀팁
* **골든타임 활용**: 오전 10시 이전 입차를 추천하며, {sigungu} 관내 동일 생활권 동선으로 이동 시간을 대폭 줄였습니다.
* **체력 맞춤 이동**: 오늘의 체력 수준({stamina})에 최적화된 동선이므로 무리한 이동 없이 안락하게 전 코스를 완주하실 수 있습니다.
* {tip_companion}"""


# 이 스크립트를 단독 실행할 때 업데이트된 프롬프트 생성을 테스트하는 메인 블록입니다.
if __name__ == "__main__":
    # 테스트 구분을 위한 메인 헤더를 콘솔에 출력합니다.
    print("=" * 70)
    # 시스템 프롬프트 테스트 출력 헤더를 표시합니다.
    print("[1] 업데이트된 시스템 프롬프트 (주차/교통 팁 및 추천 감성 동선 포함)")
    # 구분선을 콘솔에 출력합니다.
    print("=" * 70)

    # get_system_prompt 함수를 호출하여 시스템 프롬프트를 가져옵니다.
    system_p: str = get_system_prompt()
    # 생성된 시스템 프롬프트 텍스트를 출력합니다.
    print(system_p)
    # 줄바꿈 공백을 출력합니다.
    print("\n")

    # 테스트 구분을 위한 유저 프롬프트 헤더를 콘솔에 출력합니다.
    print("=" * 70)
    # 유저 프롬프트 테스트 출력 헤더를 표시합니다.
    print("[2] 업데이트된 유저 프롬프트 합성 테스트")
    # 구분선을 콘솔에 출력합니다.
    print("=" * 70)

    # 테스트용 가상 사용자 질문을 준비합니다.
    sample_query: str = "이번 주말에 여자친구랑 갈만한 낭만적인 밤 축제 추천해줘!"
    # 테스트용 동행자 정보를 설정합니다.
    sample_companion: str = "연인"
    # 테스트용 체력 수준을 설정합니다.
    sample_stamina: str = "하(여유롭고 편안한 힐링 코스)"

    # ChromaDB 검색 결과를 가정한 샘플 축제 청크 문서 목록을 준비합니다.
    sample_context_documents: List[str] = [
        """축제명: 한강 달빛 야시장 축제
개최장소: 반포 한강공원 달빛광장
위치(주소): 서울특별시 서초구 신반포로11길 40
축제 기간: 2026-05-01 ~ 2026-06-30
축제 내용: 한강 야경을 배경으로 열리는 푸드트럭 페스티벌과 수공예 플리마켓, 버스킹 공연
[2030 감성 포인트 & 인생샷 스팟]: 달빛 무지개 분수 앞, 세빛섬 수변 데크 야경 포토존
[2030 추천 주변 감성 카페]: 서래마을 루프탑 카페 A, 반포 한강 뷰 디저트 랩 B
연락처: 02-120
홈페이지: https://hangang.seoul.go.kr
추천 동행: 연인/친구 | 소모 체력 수준: 하"""
    ]

    # build_user_prompt 함수를 호출하여 6대 필수 포맷이 적용된 유저 프롬프트를 생성합니다.
    user_p: str = build_user_prompt(
        user_query=sample_query,
        context_documents=sample_context_documents,
        companion=sample_companion,
        stamina_level=sample_stamina
    )

    # 생성된 최종 유저 프롬프트 텍스트를 콘솔에 출력합니다.
    print(user_p)
    # 테스트 완료 구분선을 출력합니다.
    print("=" * 70)
