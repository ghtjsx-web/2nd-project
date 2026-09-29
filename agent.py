# -*- coding: utf-8 -*-
"""
페스타픽 (FestaPick) - 루트 agent.py 엔트리포인트
================================================================================
프로젝트 루트(c:\\workAI\\2차프로젝트)에서 `import agent` 또는 `python agent.py`를
실행할 때 festapick/agent.py의 AI 에이전트 및 프롬프트를 즉시 제공하는 브릿지 파일입니다.
================================================================================
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FESTAPICK_DIR = os.path.join(CURRENT_DIR, "festapick")
if FESTAPICK_DIR not in sys.path:
    sys.path.insert(0, FESTAPICK_DIR)

from festapick.agent import *

if __name__ == "__main__":
    agent_target_path = os.path.join(FESTAPICK_DIR, "agent.py")
    with open(agent_target_path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, agent_target_path, "exec"), globals())
