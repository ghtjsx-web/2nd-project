# -*- coding: utf-8 -*-
"""
페스타픽 (FestaPick) - 루트 실행 엔트리포인트
================================================================================
프로젝트 루트(c:\\workAI\\2차프로젝트)에서 `streamlit run app.py`를 실행할 때도
festapick/app.py의 모든 기능이 정상 구동되도록 지원하는 루트 브릿지 파일입니다.
================================================================================
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FESTAPICK_DIR = os.path.join(CURRENT_DIR, "festapick")
if FESTAPICK_DIR not in sys.path:
    sys.path.insert(0, FESTAPICK_DIR)

# festapick/app.py 실행
app_target_path = os.path.join(FESTAPICK_DIR, "app.py")
with open(app_target_path, "r", encoding="utf-8") as f:
    code = f.read()

exec(compile(code, app_target_path, "exec"), globals())
