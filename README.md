# InvestiGator — Smart Investment Platform

InvestiGator is a full-stack investment education and simulation platform featuring AI-driven risk assessment, virtual trading, historical backtesting, and live portfolio tracking.

## Architecture

*   **Frontend**: React (Vite), React Router, Recharts, Lucide Icons, Axios. Black & Gold theme.
*   **Backend**: Python, FastAPI, SQLAlchemy (SQLite/Async), APScheduler, yfinance, Polars.
*   **AI Engine**: Local DeepSeek R1 model via Ollama.

## Setup & Running the Project

### Prerequisites

1.  **Python 3.10+** (for the backend).
2.  **Node.js 18+** & **npm** (for the frontend).
3.  *(Optional but recommended)* **Ollama** installed with the `deepseek-r1:1.5b` model downloaded (`ollama run deepseek-r1:1.5b`) for the AI Advisor feature.

### 1. Backend Setup

Open a terminal and navigate to the `backend` directory:

```bash
cd backend
```

**Install requirements:**
```bash
pip install -r requirements.txt
```

**Environment Variables:**
The backend uses a `.env` file for configuration. A default `.env` has already been created for you (based on `.env.example`). It uses a local SQLite database by default.

**Run the Backend Server:**
```bash
python -m uvicorn app.main:app --reload --port 8000
```
*The backend API will be available at `http://localhost:8000`. It will automatically create the SQLite database (`investigator.db`) on the first run.*

---

### 2. Frontend Setup

Open a **new** terminal and navigate to the `frontend` directory:

```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Run the Frontend Development Server:**
```bash
npm run dev
```
*The frontend will be available at `http://localhost:5173`. Open this URL in your browser to access the application.*

## Features Supported
- **Dashboard**: High-level overview, portfolio history, asset allocation pie-chart, and live watchlist.
- **Real Portfolio**: Track your actual holdings securely (notes are encrypted using AES-256).
- **Virtual Simulator**: Practice trading with ₹1,00,000 in virtual cash using live market prices. 
- **Backtest**: MapReduce-powered historical backtesting across large datasets using Polars.
- **AI Advisor**: DeepSeek-R1 powered analysis of your virtual portfolio, offering risk scores and suggestions.
