# uk-wind-forecast-dashboard
A full-stack web application that visualizes UK wind generation forecasts, compares them with actual generation data from Elexon BMRS, and evaluates forecast accuracy using key performance metrics.


## Overview

Electricity suppliers purchasing power in the day-ahead wholesale market need reliable wind generation forecasts. Forecast errors can affect purchasing decisions, so understanding forecast accuracy is important.

This application compares actual UK wind generation with forecasts available before an assumed purchasing cutoff. It provides accuracy metrics, visual comparisons, and interval-level forecast errors for January 2026.

## Features

- Retrieves actual wind generation from Elexon's FUELHH dataset.
- Retrieves wind forecasts from Elexon's WINDFOR dataset.
- Selects the latest eligible forecast available before the configured cutoff.
- Compares forecast and actual generation by delivery interval.
- Calculates Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), forecast bias, and Mean Absolute Percentage Error (MAPE).
- Reports interval coverage and missing data.
- Displays actual and forecast generation in a React dashboard.
- Provides a Python API using FastAPI.
- Supports local development and Docker Compose.

## Technology Stack

**Frontend**
- React
- Vite
- Recharts
- CSS

**Backend**
- Python
- FastAPI
- Pandas
- HTTPX

**Testing and deployment**
- Pytest
- Docker
- Docker Compose
- Nginx for serving the production frontend build

## Project Structure

```text
uk-wind-forecast-dashboard/
├── backend/
│   ├── app/
│   │   └── services/
│   │       ├── elexon_client.py
│   │       └── forecast_analysis.py
│   ├── tests/
│   │   ├── test_forecast_analysis.py
│   │   └── test_api.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

The directory structure describes the intended organization; some component, page, or service directories may currently be empty.

## Data Sources

### Actual wind generation

- Dataset: Elexon BMRS FUELHH
- API documentation: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- Used to retrieve actual wind generation readings at half-hourly intervals.

### Wind generation forecasts

- Dataset: Elexon BMRS WINDFOR
- API documentation: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- Provides forecast generation by delivery time and publication time.

The application retrieves data from the Elexon API when the analysis endpoint is requested.

## Forecast Selection Methodology

The analysis covers delivery intervals from 1 January through 31 January 2026.

For each delivery interval:

1. Read the delivery timestamp and forecast publication timestamp.
2. Determine the configured forecast cutoff.
3. Exclude forecasts published after that cutoff.
4. Select the most recently published eligible forecast for the delivery interval.
5. Match the selected forecast with actual generation using UTC-normalized delivery timestamps.
6. Calculate forecast errors and aggregate accuracy metrics.

### Purchasing cutoff assumption

The current implementation assumes a cutoff of **10:00 UTC on the day before delivery**.

This is a configurable analytical assumption, not a confirmed market rule. It is used to demonstrate how a purchasing team could evaluate the information available when making day-ahead decisions.

Forecasts published after the cutoff are excluded to avoid look-ahead bias.

### Time aggregation

Actual generation is provided at half-hourly intervals. The current analysis averages the two half-hourly generation readings to produce an hourly value.

This assumes the `generation` field represents average power in MW. The aggregation and units should be verified against the relevant dataset documentation before using the results for operational decisions.

## Accuracy Metrics

Let:

- `Actual` represent actual wind generation.
- `Forecast` represent the selected forecast.
- `Error = Actual - Forecast`.

The dashboard calculates:

- **MAE:** Mean Absolute Error; the average magnitude of forecast errors.
- **RMSE:** Root Mean Squared Error; penalizes larger errors more heavily.
- **Bias:** Mean signed error. Negative bias means the forecasts overestimated actual generation on average.
- **MAPE:** Mean Absolute Percentage Error, excluding intervals with zero actual generation.
- **Coverage:** The percentage of expected hourly intervals with matched actual and eligible forecast data.

A forecast error is not the same as a financial loss. The available datasets do not include purchase volumes, electricity prices, demand, or other generation positions, so the application does not estimate actual procurement costs or savings.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome message |
| GET | `/api/health` | Health check |
| GET | `/api/analysis` | Retrieves data and returns forecast accuracy analysis |

Interactive API documentation is available at `/docs` while the backend is running.

## Run Locally

### Prerequisites

- Python 3.12 or a compatible Python version
- Node.js and npm
- Git

### 1. Start the backend

Open PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The backend runs at:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

If PowerShell blocks virtual-environment activation, run this in the same PowerShell session before activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Start the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

http://localhost:5173

The frontend uses `VITE_API_URL` if configured; otherwise, it defaults to `http://127.0.0.1:8000`.

## Run with Docker

Ensure Docker Desktop is running.

From the project root:

```powershell
docker compose up --build
```

Open the dashboard:

http://localhost:8080

Backend health check:

http://localhost:8000/api/health

To stop the Docker Compose services, press `Ctrl+C` in the terminal running Compose. To remove the stopped containers, run:

```powershell
docker compose down
```

## Run Tests

From the project root:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m