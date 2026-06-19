# Skill2Salary AI Pro - Project Overview

Skill2Salary AI Pro is a local full-stack career intelligence website for Indian technology salary guidance.

## Main Modules

- Authentication: local username and password accounts with hashed passwords and session cookies.
- Resume AI: resume text analysis, skill extraction, ATS readiness score, role match, and improvement tips.
- Salary Lab: multi-model ML salary prediction in Indian Rupees and LPA.
- What-If Analysis: compares current predicted salary with future salary after learning new skills.
- SalarAI Guide: built-in NLP-style chatbot that answers questions about the website and guides users.
- Career Roadmap: simple 90-day plan based on target role and missing skills.

## Current ML Models

- Linear Regression
- Decision Tree Regressor
- Random Forest Regressor
- Gradient Boosting Regressor
- Neural Network using MLP Regressor
- Weighted Ensemble used as the final salary prediction

## Important Data Note

The current salary model trains on a deterministic synthetic Indian-market dataset for demonstration and development. Replace it with cleaned real salary data before making production salary claims.
