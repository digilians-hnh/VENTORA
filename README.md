# VENTORA

## AI-Driven Smart Inventory Analytics for Perishable Retail

VENTORA is an end-to-end decision-support platform designed to help retail inventory managers identify perishable inventory at risk of spoilage, prioritize the batches that require attention, recommend practical interventions, and quantify the potential business value of acting on those recommendations.

The system follows a simple decision chain:

> **Predict → Prioritize → Recommend → Measure Impact**

VENTORA combines demand forecasting, spoilage-risk classification, inventory exposure analysis, deterministic business recommendations, and scenario-based business-value simulation into one traceable workflow.

---

## Demo & Presentation

### 🖥️ VENTORA Dashboard

Run the VENTORA frontend locally and open the dashboard:

**[Open VENTORA — AI Inventory Risk Intelligence](https://ventora.onrender.com/)**


### 📊 Final Project Presentation

**[View the VENTORA Final Presentation](./docs/VENTORA_Final_Presentation.pdf)**

The presentation covers the project problem and scope, data and methodology, XGBoost demand forecasting, LightGBM spoilage classification, the Inventory Risk Engine, recommendations, business-value simulation, system architecture, validation, limitations, and future work.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Business Problem](#business-problem)
- [Objectives](#objectives)
- [System Architecture](#system-architecture)
- [How VENTORA Works](#how-ventora-works)
- [Key Features](#key-features)
- [Machine Learning Models](#machine-learning-models)
- [Inventory Risk Engine](#inventory-risk-engine)
- [Recommendation Engine](#recommendation-engine)
- [Business-Value Simulation](#business-value-simulation)
- [Results](#results)
- [Application Interfaces](#application-interfaces)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Running the Backend](#running-the-backend)
- [Running the Frontend](#running-the-frontend)
- [Running the Streamlit Dashboard](#running-the-streamlit-dashboard)
- [Testing](#testing)
- [Deployment and Reproducibility](#deployment-and-reproducibility)
- [Data and Scope](#data-and-scope)
- [Limitations](#limitations)
- [Future Work](#future-work)
- [Team](#team)
- [Demo & Presentation](#demo--presentation)
- [Acknowledgements](#acknowledgements)

---

## Project Overview

Perishable retail inventory is difficult to manage because demand changes over time while products have finite shelf lives. Traditional FIFO/FEFO practices help organize stock consumption, but they do not quantify how much inventory is likely to remain unsold before expiry or which batches deserve immediate intervention.

VENTORA addresses this problem by combining:

1. Historical retail demand data.
2. Shelf-life information.
3. Machine-learning demand forecasting.
4. Machine-learning spoilage classification.
5. Batch-level inventory and expiry information.
6. A composite inventory risk score.
7. Deterministic business recommendations.
8. Business-value simulation.

The final system was evaluated on **35,165 reconstructed inventory batches** from the scoped M5 FOODS / CA_1 dataset.

---

## Business Problem

Inventory managers need to answer five practical questions:

1. **What inventory is currently at risk?**
2. **Why is it at risk?**
3. **How much inventory is potentially exposed to waste?**
4. **What action should be taken?**
5. **What potential value could those actions create?**

Traditional inventory rules generally do not combine expected demand, remaining shelf life, inventory quantity, and learned spoilage likelihood into a single prioritization mechanism.

VENTORA converts these signals into an interpretable decision-support workflow.

---

## Objectives

The project was designed to:

- Forecast near-term retail demand.
- Estimate the probability that an inventory batch will spoil.
- Combine demand, inventory, shelf life, and spoilage probability into a batch-level risk signal.
- Rank inventory using a 0–100 Risk Score.
- Categorize batches into LOW, MEDIUM, HIGH, and CRITICAL risk levels.
- Translate risk levels into concrete and auditable business actions.
- Estimate potential waste reduction under documented intervention scenarios.
- Provide an interactive manager-facing analytics interface.
- Maintain reproducibility through frozen deployment artifacts and automated validation.

---

## System Architecture

VENTORA is organized as an end-to-end pipeline:

```text
                    ┌──────────────────────────────┐
                    │       Public Data Sources    │
                    │                              │
                    │  M5 Retail Sales Dataset     │
                    │  USDA FoodKeeper Shelf Life  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Data Preparation &           │
                    │ Batch Reconstruction         │
                    │                              │
                    │ • Item-level sales           │
                    │ • Category demand            │
                    │ • Shelf-life mapping         │
                    │ • Batch reconstruction      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Feature Engineering &        │
                    │ Leakage Prevention           │
                    │                              │
                    │ • Lag features               │
                    │ • Rolling demand features   │
                    │ • Calendar/promotional data │
                    │ • Expiry embargo             │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐          ┌──────────────────┐
          │ XGBoost          │          │ LightGBM         │
          │ Demand Forecast  │          │ Spoilage Model   │
          └────────┬─────────┘          └────────┬─────────┘
                   │                             │
                   └──────────────┬──────────────┘
                                  ▼
                    ┌──────────────────────────────┐
                    │ Inventory Risk Engine        │
                    │                              │
                    │ Expected Demand Before       │
                    │ Expiry                       │
                    │          ↓                   │
                    │ Potential Excess Inventory   │
                    │          ↓                   │
                    │ Expected Waste Exposure      │
                    │          ↓                   │
                    │ 0–100 Risk Score             │
                    │          ↓                   │
                    │ LOW / MEDIUM / HIGH /        │
                    │ CRITICAL                     │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌──────────────────┐          ┌──────────────────┐
          │ Recommendation   │          │ Business-Value   │
          │ Engine           │          │ Simulation       │
          │                  │          │                  │
          │ Action by risk   │          │ FIFO/FEFO vs AI  │
          │ level             │          │ scenarios        │
          └────────┬─────────┘          └────────┬─────────┘
                   │                             │
                   └──────────────┬──────────────┘
                                  ▼
                    ┌──────────────────────────────┐
                    │ VENTORA Decision-Support     │
                    │ Interfaces                   │
                    │                              │
                    │ Overview • Risk Explorer     │
                    │ Recommendations • Business   │
                    │ Impact • Data Input           │
                    └──────────────────────────────┘
```

---

## How VENTORA Works

### 1. Demand Forecasting

The XGBoost model forecasts category-level daily demand using historical lag, rolling, calendar, and category features.

The category forecast is then allocated to individual items using their historical share of category demand.

### 2. Spoilage Prediction

The LightGBM classifier estimates:

> **Spoilage Probability** = probability that a batch will be discarded before expiry.

The model uses information available when the batch is received, including shelf-life, quantity, historical demand signals, calendar/promotional context, and demand variability.

### 3. Expected Waste Exposure

For each batch:

```text
Expected Demand Before Expiry
        ↓
Potential Excess Inventory
        ↓
Expected Waste Exposure
```

The core relationship is:

```text
Potential Excess Inventory
    = max(Current Inventory - Expected Demand Before Expiry, 0)

Expected Waste Exposure
    = Spoilage Probability × Potential Excess Inventory
```

### 4. Risk Score

Expected Waste Exposure is transformed into a **0–100 composite Risk Score**.

The Risk Score is a prioritization measure — **not a probability of loss**.

Risk levels are:

| Risk Score | Risk Level |
|---:|---|
| 0–25 | LOW |
| 25–50 | MEDIUM |
| 50–75 | HIGH |
| 75–100 | CRITICAL |

### 5. Recommendations

The deterministic Recommendation Engine converts risk into an operational action.

| Risk Level | Typical Action |
|---|---|
| CRITICAL | Immediate discount / prioritize sale / redistribution |
| HIGH | Discount or redistribute; reduce next replenishment |
| MEDIUM | Monitor and adjust future replenishment |
| LOW | Normal inventory management |

The recommendation layer contains no fitted parameters or randomness, making the decisions auditable.

### 6. Business Impact

The Business-Value Simulation compares a reconstructed FIFO/FEFO no-intervention baseline with simulated AI-assisted interventions for HIGH and CRITICAL batches.

Three scenarios are reported:

- Conservative
- Base
- Optimistic

These figures are **simulation estimates under explicit assumptions**, not measured real-world impact.

---

## Key Features

### Executive Overview

Provides a portfolio-level view of:

- Total batches and units.
- HIGH + CRITICAL inventory.
- Expected Waste Exposure.
- Risk distribution.
- Spoilage rate by risk level.
- Intervention scope.
- Business-value indicators.

### Risk Explorer

Provides batch-level investigation with:

- Product/category.
- Batch.
- Days to expiry.
- Current inventory.
- Expected demand.
- Potential excess inventory.
- Spoilage Probability.
- Expected Waste Exposure.
- Risk Score.
- Risk Level.
- Recommendation.

Filtering and sorting support category, risk level, and days-to-expiry analysis.

### Recommendations

Organizes actions by:

- CRITICAL
- HIGH
- MEDIUM
- LOW

This allows managers to focus first on the batches where intervention can affect the current inventory outcome.

### Business Impact

Compares:

- FIFO/FEFO baseline.
- AI-assisted simulated outcomes.
- Conservative scenario.
- Base scenario.
- Optimistic scenario.
- Waste reduction.
- Spoilage-rate change.
- Intervention population.

### Data Input

The company-facing application supports:

- Demo Mode using the verified evaluation artifacts.
- Basic CSV schema validation and preview.
- Advanced scoring when uploaded data already contains the engineered features required by the frozen inference layer.

A plain inventory CSV cannot independently produce a valid Risk Score because the frozen models require historical/engineered demand features.

---

## Machine Learning Models

### XGBoost — Demand Forecasting

**Task:** Category-level daily demand forecasting.

**Final metrics:**

| Metric | Result |
|---|---:|
| MAE | 86.59 units |
| RMSE | 140.30 units |
| MAPE | 10.82% |

The model uses an 80/20 chronological train/test split.

### LightGBM — Spoilage Classification

**Task:** Predict whether an inventory batch will spoil.

**Final metrics:**

| Metric | Result |
|---|---:|
| ROC-AUC | 0.8249 |
| PR-AUC | 0.7592 |
| F1 | 0.6779 |
| Precision | 0.6738 |
| Recall | 0.6821 |

A 0.40 classification threshold was selected to balance precision and recall in a business context where missing an actually at-risk batch is costly.

---

## Leakage Prevention

The project explicitly addresses temporal leakage.

Key safeguards include:

- Trailing demand and price features use `shift(1)` before rolling calculations.
- The spoilage model uses an expiry-date embargo.
- Training and test populations are separated by time.
- Batch IDs are checked for train/test overlap.
- Batches whose evaluation windows straddle the split boundary are excluded.

These safeguards are important because spoilage outcomes may only become observable after a batch's expiry window.

---

## Results

The final evaluation population contains:

**35,165 batches**

### Risk Engine Validation

Observed spoilage rates increase monotonically with risk level:

| Risk Level | Actual Spoilage Rate |
|---|---:|
| LOW | 31.5% |
| MEDIUM | 36.7% |
| HIGH | 48.2% |
| CRITICAL | 64.7% |

This monotonic relationship is a central validation result for the Risk Engine.

### Intervention Population

The HIGH + CRITICAL population contains:

**6,587 batches (18.7% of the evaluation population)**

### Business-Value Simulation

| Scenario | Simulated Waste Reduction |
|---|---:|
| Conservative | 12.91% |
| Base | 22.50% |
| Optimistic | 30.05% |

The baseline contains **36,448 waste units**.

> **Important:** The 22.5% Base scenario is a simulated estimate under documented intervention assumptions. It must not be interpreted as measured real-world waste reduction.

---

## Application Interfaces

The project contains two layers of delivery:

### Analytical Streamlit Dashboard

The original dashboard is a read-only presentation layer over the verified analytical artifacts.

It provides:

- Executive Overview
- Risk Explorer
- Business Impact
- Recommendations

### Company-Facing Web Application

The newer VENTORA interface adds:

- Home page.
- Data Input workflow.
- CSV validation and preview.
- Advanced scoring path.
- The same core analytical views.

The current repository also separates the company-facing delivery layer into a frontend and backend:

```text
React / TypeScript frontend
            │
            ▼
      FastAPI backend
            │
            ▼
Frozen analytical / inference artifacts
```

The analytical logic and verified artifacts remain the source of truth for the decision-support results.

---

## Technology Stack

### Data & Machine Learning

- Python
- Pandas
- NumPy
- XGBoost
- LightGBM
- Scikit-learn

### Analytical Dashboard

- Streamlit
- Plotly

### Backend

- FastAPI
- Python
- Pydantic
- Uvicorn

### Frontend

- React
- TypeScript
- Vite
- npm

### Testing & Validation

- Pytest
- Artifact integrity checks
- Inference regression tests
- Data integrity checks
- Application runtime checks

### Version Control

- Git
- GitHub

---

## Repository Structure

```text
VENTORA/
│
├── .gitignore
│
├── backend_api/
│   ├── core/
│   │   ├── config.py
│   │   ├── data_access.py
│   │   ├── inference_adapter.py
│   │   ├── scoring_schema.py
│   │   ├── scoring_service.py
│   │   ├── scoring_validation.py
│   │   └── serialization.py
│   │
│   ├── routers/
│   │   ├── analytics.py
│   │   ├── health.py
│   │   ├── recommendations.py
│   │   └── scoring.py
│   │
│   ├── schemas/
│   │   ├── requests.py
│   │   └── responses.py
│   │
│   ├── tests/
│   │   ├── test_business_value.py
│   │   ├── test_data_integrity.py
│   │   ├── test_health.py
│   │   ├── test_input_schema.py
│   │   ├── test_metadata.py
│   │   ├── test_recommendations.py
│   │   ├── test_risk_df.py
│   │   ├── test_score_demo.py
│   │   ├── test_score_json.py
│   │   ├── test_score_upload.py
│   │   └── ...
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── theme/
│   │   └── types/
│   │
│   ├── .env.example
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   └── ...
│
└── ventora_app/
    ├── dashboard/
    │   ├── app.py
    │   ├── data/
    │   └── requirements.txt
    │
    ├── data/
    │   ├── business_value_comparison.csv
    │   ├── category_daily_FINAL v7.csv
    │   ├── demo_live_inference_batches.csv
    │   ├── demo_live_inference_category_demand.csv
    │   └── risk_df_recommendations_FINAL.pkl
    │
    ├── deployment_artifacts/
    │   ├── extracted_booster.bin
    │   ├── feature_config.json
    │   ├── item_share_lookup.parquet
    │   └── model_metadata.json
    │
    ├── app.py
    ├── requirements.txt
    ├── sample_upload_invalid.csv
    ├── sample_upload_valid.csv
    ├── test_app.py
    └── test_inference.py
```

---

# Getting Started

## Prerequisites

Recommended environment:

- Python 3.10+
- Node.js 18+
- npm
- Git

Clone the repository:

```bash
git clone https://github.com/digilians-hnh/VENTORA.git
cd VENTORA
```

---

# Running the Backend

Create and activate a Python virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r backend_api/requirements.txt
```

Start the FastAPI application:

```powershell
uvicorn backend_api.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

> If the application is configured with a different host or port in `backend_api/core/config.py`, use that configuration instead.

---

# Running the Frontend

Open a second terminal and navigate to the frontend:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create the local environment file from the example:

```powershell
Copy-Item .env.example .env.development
```

Set the API URL in `.env.development`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the Vite development server:

```powershell
npm run dev
```

The frontend URL will be displayed in the terminal, typically:

```text
http://localhost:5173
```

### Security note

Do not commit `.env.development` or other environment-specific secret files.

Only `.env.example` should be committed when it contains non-secret configuration templates.

---

# Running the Streamlit Dashboard

The verified analytical dashboard can be run independently.

Navigate to:

```powershell
cd ventora_app/dashboard
```

Create/activate a Python virtual environment if needed and install the dashboard requirements:

```powershell
pip install -r requirements.txt
```

Run:

```powershell
streamlit run app.py
```

The dashboard is intentionally artifact-backed and read-only. It does not retrain the models or silently recompute the verified analytical results.

---

# Testing

## Backend Tests

From the repository root:

```powershell
pytest backend_api/tests -q
```

The backend test suite covers areas including:

- Health endpoints.
- Input schema validation.
- Data integrity.
- Metadata consistency.
- Risk dataframe integrity.
- Recommendations.
- Business-value outputs.
- Demo scoring.
- JSON scoring.
- Upload scoring.
- Regression protection around frozen artifacts.

## Analytical Application Tests

Run:

```powershell
pytest ventora_app/test_app.py ventora_app/test_inference.py -q
```

The project verification record reports:

- **27/27 application checks passed**
- **13/13 inference checks passed**
- Frozen artifact integrity checks passed.
- Cross-artifact consistency checks passed.
- Application runtime health checks returned HTTP 200.

---

# Deployment and Reproducibility

VENTORA is packaged as a **local/hostable decision-support prototype**.

It is not presented as a production retail deployment.

The project emphasizes reproducibility through:

- Pinned dependency files.
- Frozen model/deployment artifacts.
- SHA-256 artifact hashes.
- Deterministic recommendation logic.
- Regression tests.
- Data-integrity assertions.
- Chronological evaluation.
- Expiry-date embargo.
- Cross-artifact validation.

The verification record confirms:

- All **35,165 evaluation batch IDs** matched the frozen reference.
- Frozen artifacts matched their recorded SHA-256 hashes.
- Spoilage-probability cross-check maximum absolute difference was approximately `1.11e-16`.
- Reloaded versus original in-memory spoilage and demand predictions had zero maximum absolute difference.
- Application and inference test suites passed.

No cloud production deployment or live retail integration is claimed.

---

# Data and Scope

VENTORA uses two public data sources:

### M5 Forecasting Competition

The project uses the **FOODS department for store CA_1** from the M5 retail sales dataset.

The scoped data includes:

- Daily unit sales.
- Calendar events.
- SNAP indicators.
- Selling prices.

### USDA FoodKeeper

FoodKeeper provides shelf-life reference values used to support the reconstructed inventory-batch representation.

### Important Scope Note

The original M5 dataset does not directly contain real inventory batches or observed spoilage labels.

VENTORA therefore reconstructs batch-level inventory and spoilage outcomes through a documented inventory-consumption/replenishment methodology.

The evaluation scope was narrowed to:

```text
FOODS
Store: CA_1
Evaluation population: 35,165 batches
```

Favorita and Rossmann datasets were not used in the final implementation.

---

# Important Interpretation Notes

VENTORA intentionally distinguishes between four different concepts:

| Term | Meaning |
|---|---|
| Spoilage Probability | LightGBM model output for the positive/spoiled class |
| Expected Waste Exposure | Predicted quantity of inventory potentially exposed to waste |
| Risk Score | 0–100 composite prioritization score |
| Risk Level | LOW / MEDIUM / HIGH / CRITICAL category |

### Risk Score is not probability

A CRITICAL Risk Score does **not** mean that the batch has a 75% or higher probability of spoilage.

The Risk Score is a relative prioritization mechanism derived from Expected Waste Exposure.

### Simulation results are not measured impact

The reported 22.5% Base scenario waste reduction is:

> A simulated estimate under documented intervention assumptions.

It is **not** evidence that a real retailer has already achieved a 22.5% reduction.

---

# Limitations

The project has several documented limitations:

- The evaluation relies on public M5 data rather than live retailer data.
- Inventory batches and spoilage outcomes are reconstructed rather than directly observed.
- The model is evaluated on a restricted FOODS / CA_1 scope.
- Item-level expected demand is allocated from category-level forecasts using historical item shares.
- Risk levels use documented fixed score bins.
- The business-value results depend on explicit intervention assumptions.
- No live intervention pilot was conducted.
- No production retail integration is implemented.
- The optional SHAP explainability dashboard page was not built.
- Broader production monitoring, staging, and operational hardening remain future work.

---

# Future Work

Potential future improvements include:

- Validation using real Egyptian retail data.
- Multi-store and multi-category evaluation.
- Direct item-level demand forecasting.
- Live ERP/inventory-system integration.
- Production deployment and monitoring.
- Automated model retraining pipelines.
- More extensive sensitivity analysis.
- Expanded explainability through a dedicated SHAP interface.
- Real-world intervention pilots.
- Integration with pricing, redistribution, and replenishment workflows.

---

# Team

| Team Member | Role |
|---|---|
| Hoda Mohamed Ezzat Elhamahmy | Data Preparation & EDA |
| Nada Fahmy Fahmy Altohamy | Machine Learning & Model Development |
| Hayam Medhat Ahmed Wahdan | AI Solution Integration & Deployment |

### Responsibilities

**Data Preparation & EDA**
- Data sourcing and validation.
- Data quality analysis.
- Exploratory analysis.
- Cleaning and preprocessing.
- Feature engineering.
- Leakage-free data splitting.

**Machine Learning & Model Development**
- Demand forecasting.
- Spoilage classification.
- Model comparison.
- Threshold and hyperparameter tuning.
- Model evaluation.
- Final model selection.

**AI Solution Integration & Deployment**
- Model integration.
- Inventory Risk Engine.
- Recommendation Engine.
- Business-value simulation.
- Dashboard and web application.
- Deployment validation and testing.

---

# Acknowledgements

The project acknowledges the support of:

- Military Technical College.
- Department of Computer Engineering and Artificial Intelligence.
- Digilians — MCIT Digital Pioneers Initiative.
- Project mentors and instructors.

The project also acknowledges the public data resources that supported development and evaluation, particularly the M5 Forecasting Competition dataset and USDA FoodKeeper.

---

## Project Status

**Status:** Completed academic decision-support prototype

**Core pipeline:**

```text
Data
  ↓
Batch Reconstruction
  ↓
Feature Engineering
  ↓
Demand Forecasting
  ↓
Spoilage Classification
  ↓
Inventory Risk Engine
  ↓
Recommendations
  ↓
Business-Value Simulation
  ↓
Decision-Support Application
```

**VENTORA turns inventory data into prioritized, explainable actions for reducing perishable inventory waste.**
