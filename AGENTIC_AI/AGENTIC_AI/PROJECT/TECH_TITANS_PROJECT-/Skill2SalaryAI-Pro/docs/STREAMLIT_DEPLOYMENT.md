# Streamlit Deployment Guide

This project includes a Streamlit version in `streamlit_app.py`.

## Run Streamlit Locally

Open the folder in VS Code:

```powershell
cd C:\Users\chara\Desktop\Skill2SalaryAI-Pro
code .
```

Create and activate a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

Run:

```powershell
py -m streamlit run streamlit_app.py
```

Streamlit normally opens:

```text
http://localhost:8501
```

## Deploy To Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload this complete project folder.
3. Go to Streamlit Community Cloud.
4. Click `New app`.
5. Select your GitHub repo.
6. Set the main file path:

```text
streamlit_app.py
```

7. Click `Deploy`.

## Files Streamlit Needs

```text
streamlit_app.py
requirements.txt
app.py
.streamlit/config.toml
docs/
```

## Streamlit Features

- Overview page
- Resume AI
- Salary Lab
- Linear Regression prediction
- Decision Tree prediction
- Random Forest prediction
- Gradient Boosting prediction
- Neural Network prediction
- Weighted Ensemble final salary
- Model comparison chart
- Salary growth chart
- Skill impact chart
- What-If Analysis
- SalarAI Guide chatbot

## Important Deployment Note

The current model trains on a synthetic Indian-market dataset. This is fine for demo and project submission. For production, replace `synthetic_dataset()` in `app.py` with a real cleaned salary dataset.
