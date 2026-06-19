"""Streamlit deployment app for Skill2Salary AI Pro."""

from __future__ import annotations

import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app import (
    ROLE_SKILLS,
    ROLES,
    SKILLS,
    SalaryEngine,
    chatbot_reply,
)


MODEL_LABELS = {
    "linear": "Linear Regression",
    "decision_tree": "Decision Tree",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
    "neural_network": "Neural Network",
}

EDUCATION = ["Diploma", "Bachelor's", "Master's", "PhD"]
CITIES = ["Tier 3", "Tier 2", "Tier 1"]
INDUSTRIES = ["Services", "SaaS", "FinTech", "E-commerce", "Product"]

SKILL_ALIASES = {
    "Python": ["python"],
    "SQL": ["sql"],
    "Machine Learning": ["machine learning", "scikit-learn", "sklearn"],
    "Generative AI": ["generative ai", "large language model", "llm", "prompt engineering"],
    "NLP": ["nlp", "natural language processing"],
    "MLOps": ["mlops", "model deployment", "model monitoring"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "React": ["react", "reactjs", "react.js"],
    "FastAPI": ["fastapi"],
    "Power BI": ["power bi", "powerbi"],
    "Statistics": ["statistics", "statistical analysis"],
    "Leadership": ["leadership", "mentored", "stakeholder management"],
}


st.set_page_config(
    page_title="Skill2Salary AI Pro",
    page_icon="S2S",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Training salary models...")
def get_engine() -> SalaryEngine:
    return SalaryEngine()


def format_lpa(value: float) -> str:
    return f"Rs. {value:.1f} LPA"


def extract_skills(text: str) -> list[str]:
    clean = text.lower()
    detected: list[str] = []
    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            pattern = rf"(^|[^a-z0-9]){re.escape(alias)}([^a-z0-9]|$)"
            if re.search(pattern, clean):
                detected.append(skill)
                break
    return detected


def score_resume(text: str, skills: list[str]) -> tuple[int, list[str]]:
    checks = [
        (12, re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", text, re.I), "Add a professional email address."),
        (10, re.search(r"linkedin\.com|github\.com|portfolio", text, re.I), "Add LinkedIn, GitHub, or portfolio links."),
        (14, re.search(r"\b\d+(?:\.\d+)?%|rs\.?|inr|\$|\b\d+\+\b", text, re.I), "Quantify achievements with percentages, scale, time, or revenue."),
        (12, re.search(r"experience|employment|work history|internship", text, re.I), "Add a clearly labelled experience section."),
        (12, re.search(r"project|case study|application|platform", text, re.I), "Include relevant projects with links and outcomes."),
        (14, re.search(r"improved|reduced|increased|built|launched|designed|led|automated", text, re.I), "Start bullets with strong action verbs."),
        (14, len(skills) >= 5, "Add a focused technical skills section with at least five relevant skills."),
        (12, len(text.strip().split()) >= 90, "Add enough evidence: responsibilities, decisions, tools, and results."),
    ]
    score = sum(weight for weight, passed, _ in checks if passed)
    tips = [tip for _, passed, tip in checks if not passed]
    return score, tips


def render_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
          background:
            radial-gradient(circle at 15% 10%, rgba(139,92,246,.24), transparent 32%),
            radial-gradient(circle at 85% 15%, rgba(34,211,238,.18), transparent 28%),
            linear-gradient(135deg, #070810 0%, #101323 55%, #070810 100%);
          color: #f8fafc;
        }
        [data-testid="stSidebar"] {
          background: rgba(10, 14, 25, .78);
          border-right: 1px solid rgba(148, 163, 184, .18);
        }
        .hero {
          border: 1px solid rgba(148,163,184,.18);
          border-radius: 28px;
          padding: 2rem;
          background: linear-gradient(145deg, rgba(255,255,255,.09), rgba(255,255,255,.03));
          box-shadow: 0 24px 80px rgba(0,0,0,.28);
        }
        .metric-card {
          border: 1px solid rgba(148,163,184,.18);
          border-radius: 20px;
          padding: 1rem;
          background: rgba(255,255,255,.055);
        }
        .small-muted { color: #98a2b3; font-size: .9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def salary_lab(engine: SalaryEngine) -> None:
    st.subheader("Salary Lab")
    st.caption("Enter user details. Every model predicts salary, and the weighted ensemble is the final salary.")

    left, right = st.columns([0.95, 1.05], gap="large")
    with left:
        with st.form("salary_form"):
            role = st.selectbox("Target role", ROLES)
            experience = st.number_input("Experience in years", min_value=0.0, max_value=25.0, value=3.0, step=0.5)
            education = st.selectbox("Highest education", EDUCATION, index=1)
            city = st.selectbox("City category", CITIES, index=1)
            industry = st.selectbox("Industry", INDUSTRIES)
            current_lpa = st.number_input("Current salary in LPA", min_value=0.0, max_value=100.0, value=6.0, step=0.5)
            resume_score = st.slider("Resume score", min_value=0, max_value=100, value=65)
            skills = st.multiselect("Current skills", SKILLS, default=["Python", "SQL"])
            submitted = st.form_submit_button("Generate salary prediction", use_container_width=True)

    if not submitted and "prediction" not in st.session_state:
        with right:
            st.info("Fill the form and generate prediction to see all model outputs.")
        return

    if submitted:
        profile = {
            "role": role,
            "experience": experience,
            "education": education,
            "city": city,
            "industry": industry,
            "current_lpa": current_lpa,
            "resume_score": resume_score,
            "skills": skills,
        }
        st.session_state.profile = profile
        st.session_state.prediction = engine.predict(profile)

    result = st.session_state.prediction
    profile = st.session_state.profile

    with right:
        st.markdown('<div class="hero">', unsafe_allow_html=True)
        st.caption("FINAL WEIGHTED ENSEMBLE")
        st.title(format_lpa(result["ensemble_lpa"]))
        st.write(f"Expected range: **{format_lpa(result['range'][0])} - {format_lpa(result['range'][1])}**")
        st.progress(result["confidence"] / 100, text=f"{result['confidence']}% confidence")
        st.markdown("</div>", unsafe_allow_html=True)

    model_rows = [
        {
            "Model": MODEL_LABELS[name],
            "Prediction": result["predictions"][name],
            "Prediction LPA": format_lpa(result["predictions"][name]),
            "Weight": result["weights"][name],
            "MAE": result["metrics"][name]["mae"],
            "RMSE": result["metrics"][name]["rmse"],
            "R2": result["metrics"][name]["r2"],
        }
        for name in MODEL_LABELS
    ]
    model_df = pd.DataFrame(model_rows)

    st.markdown("### All Model Salary Predictions")
    cols = st.columns(len(model_rows))
    for col, row in zip(cols, model_rows):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                  <div class="small-muted">{row['Model']}</div>
                  <h3>{row['Prediction LPA']}</h3>
                  <div class="small-muted">Weight {row['Weight']:.0%} | R2 {row['R2']:.3f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    chart_df = pd.concat(
        [
            model_df[["Model", "Prediction"]],
            pd.DataFrame([{"Model": "Weighted Ensemble", "Prediction": result["ensemble_lpa"]}]),
        ],
        ignore_index=True,
    )
    st.plotly_chart(px.bar(chart_df, x="Model", y="Prediction", color="Model", title="Model Comparison Chart"), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        growth_df = pd.DataFrame({"Year": ["Now", "Y1", "Y2", "Y3", "Y4", "Y5"], "Salary LPA": result["growth"]})
        st.plotly_chart(px.line(growth_df, x="Year", y="Salary LPA", markers=True, title="Salary Growth Chart"), use_container_width=True)
    with c2:
        skills_df = pd.DataFrame(result["top_skills"])
        if not skills_df.empty:
            st.plotly_chart(px.bar(skills_df, x="skill", y="impact_lpa", title="Skill Impact Chart"), use_container_width=True)
        else:
            st.success("You already cover the core role skill set.")

    st.markdown("### Career Insights")
    for insight in result["insights"]:
        st.write(f"- {insight}")

    st.markdown("### What-If Analysis")
    current_skills = set(profile["skills"])
    possible = [skill for skill in SKILLS if skill not in current_skills]
    future_skills = st.multiselect("Skills you plan to learn", possible, default=possible[:1] if possible else [])
    if st.button("Predict future salary", use_container_width=True):
        future_profile = {**profile, "skills": sorted(current_skills.union(future_skills))}
        future = engine.predict(future_profile)
        delta = future["ensemble_lpa"] - result["ensemble_lpa"]
        st.success(f"Current: {format_lpa(result['ensemble_lpa'])} | Future: {format_lpa(future['ensemble_lpa'])} | Change: {delta:+.1f} LPA")

    with st.expander("Advanced Analysis"):
        st.dataframe(model_df, use_container_width=True, hide_index=True)
        st.caption(result["disclaimer"])


def resume_ai() -> None:
    st.subheader("Resume AI")
    st.caption("Paste resume text to detect skills, score ATS readiness, and get improvement tips.")
    sample = (
        "AI Engineer with 3 years of experience building Python and FastAPI services. "
        "Built a Generative AI support assistant that reduced resolution time by 32%. "
        "Deployed Docker services on AWS and implemented model monitoring. "
        "GitHub: github.com/arjun/portfolio Email: arjun@example.com."
    )
    resume = st.text_area("Resume content", height=280, value=sample)
    role = st.selectbox("Target role for resume match", ROLES, key="resume_role")
    if st.button("Analyze resume", use_container_width=True):
        skills = extract_skills(resume)
        score, tips = score_resume(resume, skills)
        required = ROLE_SKILLS[role]
        role_match = round(len(set(skills).intersection(required)) / len(required) * 100)
        c1, c2, c3 = st.columns(3)
        c1.metric("ATS score", score)
        c2.metric("Role match", f"{role_match}%")
        c3.metric("Skills detected", len(skills))
       # st.write("Detected skills:", ", ".join(skills) if skills else "No catalog skills detected.")
       # missing = [skill for skill in required if skill not in skills]
        #if missing:
          #  tips.append(f"Build evidence for role-critical skills: {', '.join(missing[:3])}.")
        #st.markdown("### Priority improvements")
        for tip in tips:
            st.write(f"- {tip}")


def salar_ai_guide() -> None:
    st.subheader("SalarAI Guide")
    st.caption("Ask about the website, salary prediction, Resume AI, models, charts, setup, or deployment.")
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hi, I am SalarAI Guide. Ask me anything about Skill2Salary."}
        ]
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    prompt = st.chat_input("Ask SalarAI Guide...")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        reply = chatbot_reply(prompt)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply["answer"]})
        st.rerun()


def overview() -> None:
    st.markdown(
        """
        <div class="hero">
          <p class="small-muted">SKILL TO SALARY</p>
          <h1>Skill2Salary AI Pro</h1>
          <p>Predict Indian salary with five ML models, analyze resumes, test future skills, and guide users with SalarAI Guide.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.metric("ML models", "5")
    c2.metric("Final output", "Ensemble")
    c3.metric("Currency", "Indian LPA")
    st.markdown("### Models Included")
    st.write("Linear Regression, Decision Tree, Random Forest, Gradient Boosting, Neural Network, and a weighted ensemble.")


def main() -> None:
    render_css()
    engine = get_engine()
    st.sidebar.title("Skill2Salary AI Pro")
    page = st.sidebar.radio("Navigation", ["Overview", "Resume AI", "Salary Lab", "SalarAI Guide", "Documentation"])
    st.sidebar.caption("Streamlit deployment version")
    if page == "Overview":
        overview()
    elif page == "Resume AI":
        resume_ai()
    elif page == "Salary Lab":
        salary_lab(engine)
    elif page == "SalarAI Guide":
        salar_ai_guide()
    else:
        st.subheader("Documentation")
        st.write("Open the `docs/` folder in VS Code for full project documentation.")
        st.write("- PROJECT_OVERVIEW.md")
        st.write("- SETUP_GUIDE.md")
        st.write("- STREAMLIT_DEPLOYMENT.md")
        st.write("- API_REFERENCE.md")
        st.write("- ML_SALARY_MODULE.md")
        st.write("- USER_GUIDE.md")


if __name__ == "__main__":
    main()
