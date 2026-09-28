@echo off
chcp 65001 > nul
echo ========================================================
echo [Fest & Rest] 참고용 데모 애플리케이션을 실행합니다...
echo ========================================================
cd latest_demo
streamlit run app.py
pause
