# ML Salary Prediction Module

## Goal

Predict Indian salary in LPA using multiple machine learning models and show the weighted ensemble as the final salary.

## Models Trained

- Linear Regression
- Decision Tree Regressor
- Random Forest Regressor
- Gradient Boosting Regressor
- Neural Network, MLP Regressor

## Metrics

Each model is evaluated with:

- MAE: Mean Absolute Error
- RMSE: Root Mean Squared Error
- R2 Score

## Ensemble Logic

The app calculates model weights using inverse MAE:

```text
weight = 1 / model_mae
```

Weights are normalized so they sum to 1. The final salary is:

```text
ensemble = sum(model_prediction * model_weight)
```

## User-Facing Output

Normal users see:

- Final estimated salary
- Salary range
- Confidence score
- Career insights
- Top skills to increase salary
- Visible model predictions for Linear Regression, Decision Tree, Random Forest, Gradient Boosting, Neural Network, and Ensemble

Advanced users can expand Advanced Analysis to see model metrics, weights, and chart comparison.

## Production Improvement

Replace `synthetic_dataset()` in `app.py` with a verified dataset containing role, experience, education, city, industry, skills, resume strength, and salary.
