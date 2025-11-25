#!/bin/bash
source .venv/bin/activate
nohup streamlit run app.py --server.port 8501 > streamlit.log 2>&1 &
echo $! > app.pid
