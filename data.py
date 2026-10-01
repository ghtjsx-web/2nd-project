# -*- coding: utf-8 -*-
"""
페스타픽 (FestaPick) - 루트 data.py 엔트리포인트 & 브릿지
================================================================================
프로젝트 루트에서 `import data` 또는 `from data import ...`를 실행할 때
festapick/data_pipeline.py의 모든 파이프라인과 함수를 즉시 제공하는 브릿지 파일입니다.
================================================================================
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FESTAPICK_DIR = os.path.join(CURRENT_DIR, "festapick")
if FESTAPICK_DIR not in sys.path:
    sys.path.insert(0, FESTAPICK_DIR)

from festapick.data_pipeline import *

if __name__ == "__main__":
    data_target_path = os.path.join(FESTAPICK_DIR, "data_pipeline.py")
    with open(data_target_path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, data_target_path, "exec"), globals())