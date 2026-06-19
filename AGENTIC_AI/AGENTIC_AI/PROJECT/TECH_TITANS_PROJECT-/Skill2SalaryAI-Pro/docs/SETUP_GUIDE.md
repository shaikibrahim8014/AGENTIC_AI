# Setup Guide

## Requirements

- Python 3.10 or newer
- pip
- Modern browser

## Install

```powershell
cd C:\Users\chara\Desktop\Skill2SalaryAI-Pro
py -m pip install -r requirements.txt
```

## Run

```powershell
py app.py
```

Open:

```text
http://localhost:8501/index.html
```

## Run Streamlit Version

```powershell
py -m streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## Project Files

```text
Skill2SalaryAI-Pro/
  app.py                  Backend server, auth, chatbot API, salary ML engine
  index.html              Website structure
  requirements.txt        Python dependencies
  streamlit_app.py        Streamlit deployment version
  README.md               Main project documentation
  skill2salary.db         Local SQLite database, created automatically
  assets/
    app.js                Frontend behavior, charts, Resume AI, chatbot UI
    style.css             Modern UI, animations, responsive layout
  docs/
    PROJECT_OVERVIEW.md
    SETUP_GUIDE.md
    API_REFERENCE.md
    ML_SALARY_MODULE.md
    USER_GUIDE.md
    STREAMLIT_DEPLOYMENT.md
```
