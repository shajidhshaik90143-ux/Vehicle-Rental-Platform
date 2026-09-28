@echo off
title Vehicle Rental Platform
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python seed.py
streamlit run app.py
pause
