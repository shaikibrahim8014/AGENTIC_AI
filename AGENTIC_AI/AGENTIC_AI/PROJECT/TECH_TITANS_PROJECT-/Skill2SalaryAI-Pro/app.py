"""Skill2Salary local web server, authentication API, and salary ML service."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import secrets
import sqlite3
import time
import webbrowser
from http import cookies
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor


PORT = 8501
ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "skill2salary.db"
SESSION_SECONDS = 60 * 60 * 24 * 7

ROLES = ["AI Engineer", "Data Scientist", "ML Engineer", "Full-Stack Developer", "Data Analyst", "Product Manager"]
EDUCATION = ["Diploma", "Bachelor's", "Master's", "PhD"]
CITIES = ["Tier 3", "Tier 2", "Tier 1"]
INDUSTRIES = ["Services", "SaaS", "FinTech", "E-commerce", "Product"]
SKILLS = ["Python", "SQL", "Machine Learning", "Generative AI", "NLP", "MLOps", "Docker", "Kubernetes", "AWS", "React", "FastAPI", "Power BI", "Statistics", "Leadership"]

ROLE_SKILLS = {
    "AI Engineer": ["Python", "Generative AI", "NLP", "MLOps", "Docker", "AWS", "FastAPI"],
    "Data Scientist": ["Python", "SQL", "Machine Learning", "Statistics", "NLP", "Power BI"],
    "ML Engineer": ["Python", "Machine Learning", "MLOps", "Docker", "Kubernetes", "AWS"],
    "Full-Stack Developer": ["React", "SQL", "Docker", "AWS", "FastAPI", "Python"],
    "Data Analyst": ["SQL", "Python", "Power BI", "Statistics"],
    "Product Manager": ["Leadership", "SQL", "Statistics", "Power BI"],
}

SKILL_VALUE = {
    "Generative AI": 2.8, "MLOps": 2.3, "Kubernetes": 2.0, "Machine Learning": 1.9,
    "AWS": 1.6, "NLP": 1.5, "FastAPI": 1.3, "Docker": 1.2, "Python": 1.1,
    "React": 1.0, "SQL": 0.9, "Statistics": 0.9, "Leadership": 1.4, "Power BI": 0.8,
}

CHAT_INTENTS = {
    "salary": {
        "keywords": {"salary", "predict", "prediction", "lpa", "package", "estimate", "income", "pay"},
        "answer": "Open Salary Lab, enter your role, experience, education, city, industry, current LPA, and skills. The final salary shown to users is the weighted ensemble result in Indian LPA.",
    },
    "models": {
        "keywords": {"model", "linear", "regression", "decision", "tree", "random", "forest", "neural", "network", "mlp", "gradient", "boosting", "ensemble", "mae", "rmse", "score"},
        "answer": "The salary module trains Linear Regression, Decision Tree Regressor, Random Forest Regressor, Gradient Boosting Regressor, and Neural Network MLP Regressor. It evaluates MAE, RMSE, and R2, then combines the models with inverse-error weighted averaging.",
    },
    "resume": {
        "keywords": {"resume", "cv", "ats", "skill", "skills", "project", "keyword", "match"},
        "answer": "Resume AI extracts known skills, checks ATS signals like contact details, links, quantified outcomes, projects, action verbs, and role alignment, then gives improvement tips.",
    },
    "what_if": {
        "keywords": {"what", "if", "future", "learn", "new", "upskill", "increase", "growth"},
        "answer": "Use What-If Analysis after generating a salary prediction. Select new skills you plan to learn, and the app compares your current estimate with the future modeled estimate.",
    },
    "account": {
        "keywords": {"login", "signin", "sign", "account", "password", "username", "create", "signup", "logout"},
        "answer": "Use the Sign in and Create account tabs on the login screen. Passwords are hashed locally with PBKDF2, and the app uses an HTTP-only session cookie.",
    },
    "charts": {
        "keywords": {"chart", "graph", "gauge", "visual", "visualization", "growth", "impact"},
        "answer": "The dashboard includes a salary gauge meter, salary growth chart, skill impact chart, and model comparison chart in Advanced Analysis.",
    },
    "docs": {
        "keywords": {"documentation", "docs", "folder", "structure", "setup", "run", "install", "api"},
        "answer": "Check the docs folder for the complete project guide, API reference, model notes, and user guide. To run locally, install requirements and start app.py.",
    },
}


def chatbot_reply(message: str) -> dict[str, Any]:
    tokens = {part.strip(".,!?;:()[]{}\"'").lower() for part in message.split()}
    compact = message.lower()
    scores: list[tuple[str, int]] = []
    for name, intent in CHAT_INTENTS.items():
        keyword_hits = len(tokens.intersection(intent["keywords"]))
        phrase_hits = sum(1 for keyword in intent["keywords"] if len(keyword) > 4 and keyword in compact)
        scores.append((name, keyword_hits + phrase_hits))
    best_name, best_score = max(scores, key=lambda item: item[1])
    if best_score <= 0:
        return {
            "intent": "general",
            "answer": "I am SalarAI Guide. I can help with Skill2Salary features: salary prediction, ML models, Resume AI, What-If Analysis, charts, login, setup, and documentation. Ask me about any part of the website.",
            "suggestions": ["How is salary predicted?", "What does Resume AI check?", "How do I increase my salary?"],
        }
    intent = CHAT_INTENTS[best_name]
    suggestions = {
        "salary": ["Which model is final?", "Show What-If Analysis", "How is confidence calculated?"],
        "models": ["Explain ensemble weights", "What metrics are used?", "Why use multiple models?"],
        "resume": ["How to improve ATS score?", "Which skills are detected?", "How does role match work?"],
        "what_if": ["Which skills should I learn?", "How does future salary work?", "Open Salary Lab"],
        "account": ["How to create account?", "Is password saved safely?", "How to logout?"],
        "charts": ["What is salary gauge?", "Explain model chart", "What is skill impact?"],
        "docs": ["How to run project?", "Where is API docs?", "Explain folder structure"],
    }
    return {"intent": best_name, "answer": intent["answer"], "suggestions": suggestions.get(best_name, [])}


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash BLOB NOT NULL,
                salt BLOB NOT NULL,
                profile TEXT NOT NULL DEFAULT '{}',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        db.execute("DELETE FROM sessions WHERE expires_at < ?", (int(time.time()),))


def password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)


def feature_row(payload: dict[str, Any]) -> list[float]:
    role = payload.get("role", ROLES[0])
    education = payload.get("education", EDUCATION[1])
    city = payload.get("city", CITIES[1])
    industry = payload.get("industry", INDUSTRIES[0])
    skills = set(payload.get("skills", []))
    return [
        float(ROLES.index(role) if role in ROLES else 0),
        max(0.0, min(25.0, float(payload.get("experience", 0)))),
        float(EDUCATION.index(education) if education in EDUCATION else 1),
        float(CITIES.index(city) if city in CITIES else 1),
        float(INDUSTRIES.index(industry) if industry in INDUSTRIES else 0),
        max(0.0, min(100.0, float(payload.get("resume_score", 50)))),
        max(0.0, min(50.0, float(payload.get("current_lpa", 0)))),
        float(len(skills)),
        sum(SKILL_VALUE.get(skill, 0) for skill in skills),
        float(len(skills.intersection(ROLE_SKILLS.get(role, [])))),
    ]


def synthetic_dataset(size: int = 3200) -> tuple[np.ndarray, np.ndarray]:
    """Create a deterministic development dataset until verified market data is supplied."""
    rng = np.random.default_rng(42)
    rows: list[list[float]] = []
    targets: list[float] = []
    role_base = [8.0, 7.2, 8.5, 6.5, 4.5, 9.0]
    for _ in range(size):
        role_i = int(rng.integers(0, len(ROLES)))
        exp = float(np.clip(rng.gamma(2.0, 2.1), 0, 20))
        edu = int(rng.choice(4, p=[0.08, 0.58, 0.29, 0.05]))
        city = int(rng.choice(3, p=[0.16, 0.36, 0.48]))
        industry = int(rng.integers(0, 5))
        resume = float(np.clip(rng.normal(66, 16), 20, 98))
        count = int(np.clip(rng.poisson(5.5), 1, 13))
        selected = rng.choice(SKILLS, count, replace=False).tolist()
        value = sum(SKILL_VALUE[s] for s in selected)
        match = len(set(selected).intersection(ROLE_SKILLS[ROLES[role_i]]))
        latent = role_base[role_i] + 1.75 * exp + 0.10 * exp ** 1.65 + edu * 1.15 + city * 1.4 + industry * 0.55 + resume * 0.025 + value * 0.42 + match * 0.55
        current = max(0.0, latent * float(rng.uniform(0.55, 0.88)) if exp > 0.5 else 0.0)
        salary = latent + current * 0.23 + float(rng.normal(0, 1.35 + exp * 0.10))
        rows.append([role_i, exp, edu, city, industry, resume, current, count, value, match])
        targets.append(max(2.4, salary))
    return np.asarray(rows), np.asarray(targets)


class SalaryEngine:
    def __init__(self) -> None:
        x, y = synthetic_dataset()
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.22, random_state=42)
        self.models = {
            "linear": make_pipeline(StandardScaler(), LinearRegression()),
            "decision_tree": DecisionTreeRegressor(max_depth=10, min_samples_leaf=8, random_state=42),
            "random_forest": RandomForestRegressor(n_estimators=180, max_depth=14, min_samples_leaf=2, random_state=42, n_jobs=-1),
            "gradient_boosting": GradientBoostingRegressor(n_estimators=180, learning_rate=0.045, max_depth=3, loss="huber", random_state=42),
            "neural_network": make_pipeline(StandardScaler(), MLPRegressor(hidden_layer_sizes=(64, 32), early_stopping=True, max_iter=550, random_state=42)),
        }
        self.metrics: dict[str, dict[str, float]] = {}
        for name, model in self.models.items():
            model.fit(x_train, y_train)
            predicted = model.predict(x_test)
            self.metrics[name] = {
                "mae": float(mean_absolute_error(y_test, predicted)),
                "rmse": float(math.sqrt(mean_squared_error(y_test, predicted))),
                "r2": float(r2_score(y_test, predicted)),
            }
        inverse_error = {name: 1 / max(values["mae"], 0.01) for name, values in self.metrics.items()}
        total = sum(inverse_error.values())
        self.weights = {name: value / total for name, value in inverse_error.items()}

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = np.asarray([feature_row(payload)])
        predictions = {name: max(2.4, float(model.predict(row)[0])) for name, model in self.models.items()}
        ensemble = sum(predictions[name] * self.weights[name] for name in predictions)
        spread = float(np.std(list(predictions.values())))
        validation_rmse = sum(self.metrics[name]["rmse"] * self.weights[name] for name in self.metrics)
        uncertainty = max(1.0, validation_rmse * 1.15 + spread * 0.65)
        confidence = int(np.clip(96 - uncertainty * 3.2 - spread * 2.0, 62, 95))
        role = payload.get("role", ROLES[0])
        skills = set(payload.get("skills", []))
        top_skills = sorted(
            ({"skill": skill, "impact_lpa": SKILL_VALUE.get(skill, 0) * 0.7 + 0.4} for skill in ROLE_SKILLS.get(role, []) if skill not in skills),
            key=lambda item: item["impact_lpa"], reverse=True,
        )[:5]
        experience = float(payload.get("experience", 0))
        insights = [
            f"Your profile aligns with an estimated {ensemble:.1f} LPA for {role} roles.",
            "Target measurable project outcomes; portfolio proof improves both screening strength and negotiation leverage.",
            "Prioritise product companies and Tier 1 markets for the strongest modeled salary uplift." if payload.get("city") != "Tier 1" else "Your Tier 1 market selection already captures the model's strongest location premium.",
        ]
        if experience < 2:
            insights.append("At this stage, depth in one production-ready project matters more than collecting many shallow skills.")
        elif experience >= 7:
            insights.append("Leadership, architecture ownership, and business impact become stronger salary signals at your experience level.")
        return {
            "ensemble_lpa": round(ensemble, 2),
            "range": [round(max(2.4, ensemble - uncertainty), 2), round(ensemble + uncertainty, 2)],
            "confidence": confidence,
            "predictions": {name: round(value, 2) for name, value in predictions.items()},
            "metrics": {name: {key: round(value, 3) for key, value in metrics.items()} for name, metrics in self.metrics.items()},
            "weights": {name: round(value, 3) for name, value in self.weights.items()},
            "top_skills": top_skills,
            "insights": insights,
            "growth": [round(ensemble * 1.09 ** year, 2) for year in range(6)],
            "disclaimer": "Development estimate trained on synthetic Indian-market data; replace with verified salary records before production use.",
        }


ENGINE: SalaryEngine | None = None


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("Request is too large")
        return json.loads(self.rfile.read(length) or b"{}")

    def send_json(self, status: int, payload: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def current_user(self) -> sqlite3.Row | None:
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        morsel = jar.get("s2s_session")
        if not morsel:
            return None
        token_hash = hashlib.sha256(morsel.value.encode()).hexdigest()
        with sqlite3.connect(DB_PATH) as db:
            db.row_factory = sqlite3.Row
            return db.execute(
                "SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires_at>?",
                (token_hash, int(time.time())),
            ).fetchone()

    def require_user(self) -> sqlite3.Row | None:
        user = self.current_user()
        if not user:
            self.send_json(401, {"error": "Please sign in to continue."})
        return user

    def do_GET(self) -> None:
        if self.path == "/api/me":
            user = self.current_user()
            if not user:
                self.send_json(401, {"authenticated": False})
                return
            self.send_json(200, {"authenticated": True, "username": user["username"], "profile": json.loads(user["profile"])})
            return
        if self.path == "/api/model-info":
            if not self.require_user():
                return
            assert ENGINE is not None
            self.send_json(200, {"metrics": ENGINE.metrics, "weights": ENGINE.weights})
            return
        super().do_GET()

    def do_POST(self) -> None:
        try:
            body = self.json_body()
            if self.path == "/api/signup":
                self.handle_signup(body)
            elif self.path == "/api/login":
                self.handle_login(body)
            elif self.path == "/api/logout":
                self.handle_logout()
            elif self.path in {"/api/predict", "/api/what-if"}:
                self.handle_predict(body)
            elif self.path == "/api/chat":
                self.handle_chat(body)
            else:
                self.send_json(404, {"error": "Endpoint not found"})
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc) or "Invalid request"})
        except Exception as exc:
            print(f"API error: {exc}")
            self.send_json(500, {"error": "The server could not complete this request."})

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with sqlite3.connect(DB_PATH) as db:
            db.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)", (token_hash, user_id, int(time.time()) + SESSION_SECONDS))
        return f"s2s_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_SECONDS}"

    def handle_signup(self, body: dict[str, Any]) -> None:
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))
        if len(username) < 3 or len(username) > 32 or not username.replace("_", "").isalnum():
            raise ValueError("Username must be 3-32 letters, numbers, or underscores.")
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")
        salt = secrets.token_bytes(16)
        try:
            with sqlite3.connect(DB_PATH) as db:
                cursor = db.execute("INSERT INTO users(username,password_hash,salt,created_at) VALUES(?,?,?,?)", (username, password_hash(password, salt), salt, int(time.time())))
                user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            self.send_json(409, {"error": "That username is already registered."})
            return
        self.send_json(201, {"username": username}, {"Set-Cookie": self.create_session(user_id)})

    def handle_login(self, body: dict[str, Any]) -> None:
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))
        with sqlite3.connect(DB_PATH) as db:
            db.row_factory = sqlite3.Row
            user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not user or not hmac.compare_digest(user["password_hash"], password_hash(password, user["salt"])):
            self.send_json(401, {"error": "Incorrect username or password."})
            return
        self.send_json(200, {"username": user["username"]}, {"Set-Cookie": self.create_session(user["id"])})

    def handle_logout(self) -> None:
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        morsel = jar.get("s2s_session")
        if morsel:
            with sqlite3.connect(DB_PATH) as db:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(morsel.value.encode()).hexdigest(),))
        self.send_json(200, {"ok": True}, {"Set-Cookie": "s2s_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"})

    def handle_predict(self, body: dict[str, Any]) -> None:
        user = self.require_user()
        if not user:
            return
        assert ENGINE is not None
        result = ENGINE.predict(body)
        if self.path == "/api/predict":
            with sqlite3.connect(DB_PATH) as db:
                db.execute("UPDATE users SET profile=? WHERE id=?", (json.dumps(body), user["id"]))
        self.send_json(200, result)

    def handle_chat(self, body: dict[str, Any]) -> None:
        if not self.require_user():
            return
        message = str(body.get("message", "")).strip()
        if len(message) < 2:
            raise ValueError("Please type a question for the assistant.")
        if len(message) > 700:
            raise ValueError("Please keep chat messages under 700 characters.")
        self.send_json(200, chatbot_reply(message))


def main() -> None:
    global ENGINE
    print("Training salary models...")
    init_db()
    ENGINE = SalaryEngine()
    for name, metrics in ENGINE.metrics.items():
        print(f"  {name:18} MAE {metrics['mae']:.2f} | RMSE {metrics['rmse']:.2f} | R2 {metrics['r2']:.3f}")
    server = ThreadingHTTPServer(("localhost", PORT), AppHandler)
    url = f"http://localhost:{PORT}/index.html"
    print(f"Skill2Salary AI Pro is running at {url}")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
