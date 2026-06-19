# API Reference

All API routes are served from `app.py`.

## Auth

### POST `/api/signup`

Creates a local user account and starts a session.

Body:

```json
{ "username": "demo_user", "password": "password123" }
```

### POST `/api/login`

Signs in an existing user.

### POST `/api/logout`

Clears the current session.

### GET `/api/me`

Returns the signed-in user and saved salary profile.

## Salary

### POST `/api/predict`

Requires login. Runs all salary models and returns the final ensemble prediction.

Returns:

- `ensemble_lpa`
- `range`
- `confidence`
- `predictions.linear`
- `predictions.decision_tree`
- `predictions.random_forest`
- `predictions.gradient_boosting`
- `predictions.neural_network`
- `metrics`
- `weights`
- `top_skills`
- `insights`
- `growth`

### POST `/api/what-if`

Requires login. Runs prediction with extra planned skills, but does not save the profile.

## Chatbot

### POST `/api/chat`

Requires login. Sends a user message to SalarAI Guide.

Body:

```json
{ "message": "How is salary predicted?" }
```

Returns:

- `intent`
- `answer`
- `suggestions`
