# Skill2Salary AI Pro

Skill2Salary AI Pro is a local full-stack career intelligence website for Indian salary prediction, Resume AI, skill planning, and guided user support.

## Highlights

- Real username/password login and create-account flow
- Resume AI with ATS score, detected skills, role match, and improvement tips
- Salary Lab with Linear Regression, Decision Tree, Random Forest, Gradient Boosting, Neural Network, and final weighted ensemble
- Salary shown in Indian Rupees and LPA format
- Visible model prediction cards plus expandable Advanced Analysis
- Salary gauge, model comparison, salary growth, and skill impact charts
- What-If Analysis for future skills
- SalarAI Guide chatbot for website guidance using local NLP-style intent matching
- Professional animated background with mesh gradients, motion grid, and interactive network canvas
- Streamlit deployment version in `streamlit_app.py`

## Run Locally

### Full Website Version

```powershell
cd C:\Users\chara\Desktop\Skill2SalaryAI-Pro
py -m pip install -r requirements.txt
py app.py
```

Open:

```text
http://localhost:8501/index.html
```

### Streamlit Version

```powershell
cd C:\Users\chara\Desktop\Skill2SalaryAI-Pro
py -m pip install -r requirements.txt
py -m streamlit run streamlit_app.py
```

Open:

```text
http://localhost:8501
```

## Project Structure

```text
Skill2SalaryAI-Pro/
  app.py
  streamlit_app.py
  index.html
  requirements.txt
  README.md
  assets/
    app.js
    style.css
  docs/
    PROJECT_OVERVIEW.md
    SETUP_GUIDE.md
    API_REFERENCE.md
    ML_SALARY_MODULE.md
    USER_GUIDE.md
    STREAMLIT_DEPLOYMENT.md
```

## Documentation

- `docs/PROJECT_OVERVIEW.md`
- `docs/SETUP_GUIDE.md`
- `docs/STREAMLIT_DEPLOYMENT.md`
- `docs/API_REFERENCE.md`
- `docs/FOLDER_STRUCTURE.md`
- `docs/ML_SALARY_MODULE.md`
- `docs/USER_GUIDE.md`

## Data Notice

The included development model trains on a deterministic synthetic Indian-market salary dataset. It demonstrates the complete ML and product flow, but real production use should replace `synthetic_dataset()` in `app.py` with verified salary data.
