@echo off
title Olist E-Commerce BI Dashboard
cd /d "%~dp0"
set PYTHONPATH=E:\DataAnalytics\site-packages;%PYTHONPATH%
set TEMP=E:\temp
set TMP=E:\temp
echo =========================================================================
echo Launching Olist E-Commerce Business Intelligence Web Cockpit...
echo =========================================================================
streamlit run app.py
pause
