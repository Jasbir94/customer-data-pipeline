# ⚡ DataPipeline 360

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-00a393?style=for-the-badge&logo=fastapi)
![Vanilla JS](https://img.shields.io/badge/Vanilla_JS-ES6-yellow?style=for-the-badge&logo=javascript)
![Chart.js](https://img.shields.io/badge/Chart.js-4.4.0-ff6384?style=for-the-badge&logo=chartdotjs)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ed?style=for-the-badge&logo=docker)

An end-to-end data engineering and fullstack visualization pipeline. This project transforms noisy, raw CSV data into clean, business-ready analytics and serves it through a blazing-fast REST API and an interactive frontend dashboard.

## ✨ Features & Implementation

### 🧹 Part 1: Data Cleaning (`clean_data.py`)
- **Robust Date Parsing:** Handles multi-format dates (`YYYY-MM-DD`, `DD/MM/YYYY`, `MM-DD-YYYY`) and safely casts invalid entries to `NaT`.
- **String Normalization:** Cleans up whitespace and standardizes null representations across categorical fields like `region`.
- **Data Deduplication:** Merges duplicate customer records, ensuring the most recent `signup_date` is preserved.
- **Validation:** Implements regex-based email validation and dynamically flags malformed entries.
- **Smart Imputation:** Fills missing monetary amounts using historical per-product medians.

### 🧠 Part 2: Merge & Analysis (`analyze.py`)
- **Relational Merging:** Executes precise `LEFT JOIN` operations across `orders`, `customers`, and `products` tracking unmatched rows.
- **Business Logic Modules:** Generates 5 distinct analytical targets:
  - 📈 Monthly Revenue Trends
  - 🏆 Top 10 Customers by Spend (with 90-day churn indicators)
  - 📦 Category Performance (Avg Order Value, Total Revenue)
  - 🌍 Regional Analysis

### 🚀 Part 3: Fullstack Dashboard
- **FastAPI Backend:** Lightweight API providing endpoints for all analytical outputs with built-in CORS and error handling.
- **Zero-Dependency Frontend:** A pure HTML/CSS/Vanilla JS dashboard.
- **Dynamic Visuals:** Interactive charts powered by a locally hosted instance of Chart.js (Zero CDN tracking!).
- **Rich UI/UX:** Features loading states, error boundaries, responsive grid layouts, and polished dark-mode aesthetics.
- **Bonus Interactivity:** Includes custom date-range filters for revenue graphs and real-time search filtering for the customer table.

## 📂 Project Structure
```text
.
├── backend/            # FastAPI REST API serving the analytical outputs
│   ├── main.py         # API Endpoints and Static File serving
│   └── requirements.txt
├── data/
│   ├── processed/      # Cleaned and aggregated CSV outputs
│   └── raw/            # Generated dummy datasets (noisy)
├── frontend/           # Vanilla JS Dashboard UI
│   ├── app.js          # Chart rendering and API fetching logic
│   ├── chart.umd.min.js# Locally hosted Chart.js library
│   ├── index.html      # Dashboard markup
│   └── style.css       # Custom styling system
├── tests/              # Pytest unit tests for core pipeline logic
│   └── test_cleaning.py
├── analyze.py          # Pipeline Step 2: Relational Merging & Analysis
├── clean_data.py       # Pipeline Step 1: Raw Data Cleaning
├── generate_data.py    # Utility to generate raw noisy datasets
├── docker-compose.yml  # Container orchestration
├── Dockerfile          # Fullstack application container
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

## 🛠️ Setup & Running Locally

### Prerequisites
- Python 3.9+ 
- (Optional) Docker for containerized deployment

### 1. Local Python Environment

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Data Pipeline:**
   Generate dummy data, clean it, and run the analytical models.
   ```bash
   python generate_data.py   # Populates data/raw
   python clean_data.py      # Outputs to data/processed
   python analyze.py         # Generates analytical views
   ```

3. **Start the Application Server:**
   Launch the FastAPI backend (which also serves the frontend):
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
   *Navigate to [http://localhost:8000](http://localhost:8000) in your browser.*

### 2. Docker Deployment

Want to run everything in a container? 

1. Generate the pipeline data locally first:
   ```bash
   python generate_data.py && python clean_data.py && python analyze.py
   ```
2. Build and spin up the Docker container:
   ```bash
   docker-compose up --build
   ```

## 🧪 Testing
The data cleaning logic is backed by `pytest` unit tests ensuring robust date parsing, email validation, and deduplication logic.

Run the test suite via module invocation:
```bash
python -m pytest tests/
```

## 📌 Technical Assumptions
- Text similarity and random string generation in `generate_data.py` sufficiently mirrors real-world noisy OCR/ETL dumps.
- Orders belonging to non-existent products or customers are retained in raw joins but flagged appropriately, and may be excluded from specific aggregations (like Regional Analysis) if customer data cannot be inferred.
- Missing integer `amount` fields on orders are best imputed using the historical median of that specific item type.
