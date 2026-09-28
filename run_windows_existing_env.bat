@echo off
call .venv\Scripts\activate
python seed.py
streamlit run app.py
pause
