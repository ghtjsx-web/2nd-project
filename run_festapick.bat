@echo off
chcp 65001 > nul
echo ========================================================
echo [페스타픽 (FestaPick)] 메인 애플리케이션을 실행합니다...
echo ========================================================
streamlit run festapick/app.py
pause
