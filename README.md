# TrustAgri 🌾

AI-powered crop recommendation engine for Indian farmers.  
Given a **state** and **district**, TrustAgri recommends the **top 3 crops** by combining machine learning yield prediction, live market prices, and historical supply data.

---

## System Architecture

```
POST /recommend-crops  (state, district)
         │
         ▼
  revenue_forecast.py  (orchestrator)
     ├── weather_service.py
     │    ├── OpenWeatherMap API  → temperature, humidity
     │    └── Open-Meteo Archive → annual rainfall (mm/year, last 365 days)
     │
     └── crop_recommendation_engine.py
          ├── predict_model.py       → RandomForestRegressor (yield in hg/ha)
          ├── agmarknet_price_service.py → Agmarknet API + CSV fallback
          ├── supply_analysis.py     → crop production CSV (supply index)
          ├── market_balance_engine.py  → Oversupplied / Balanced / High Demand
          └── risk_analysis.py       → Low / Medium / High risk
```

### Scoring Formula

```
score = (predicted_yield_t_ha × market_price_INR) / supply_index
```

Top 3 crops by score are returned.

---

## ML Model

| Property        | Value                        |
|-----------------|------------------------------|
| Algorithm       | RandomForestRegressor        |
| Input features  | Year, annual_rainfall_mm, pesticides_tonnes, avg_temp, crop (encoded) |
| Target          | Crop yield in hg/ha          |
| Training data   | FAO-style global crop yield dataset (`data/yield_df.csv`) |
| Artifacts       | `models/yield_model.pkl`, `models/crop_encoder.pkl` |

> **Rainfall unit:** The model was trained on **annual** mm/year values (range ~200–3000).  
> Weather Service fetches 12-month historical precipitation from Open-Meteo to match this scale exactly.

---

## Datasets

| File | Size | Purpose |
|------|------|---------|
| `data/yield_df.csv` | ~1.4 MB | ML training data |
| `data/India Agriculture Crop Production.csv` | ~26 MB | Supply index computation |
| `data/Agriculture_price_dataset.csv` | ~53 MB | Offline price fallback |

> All datasets are excluded from version control via `.gitignore`.  
> Store them locally in `data/` before running the server.

---

## API Endpoints

### `GET /`
Health check.

### `GET /supported-crops`
Returns all crop names the ML model supports.

### `POST /recommend-crops`
Run the full pipeline.

**Request:**
```json
{ "state": "Tamil Nadu", "district": "Thanjavur" }
```

**Response:**
```json
{
  "state": "Tamil Nadu",
  "district": "Thanjavur",
  "weather": {
    "temperature": 31.4,
    "humidity": 72,
    "rainfall_mm": 1143.2,
    "rainfall_source": "open_meteo"
  },
  "crop_list_evaluated": ["Rice, paddy", "Maize", "Wheat", "Potatoes"],
  "recommended_crops": [
    {
      "crop": "Rice, paddy",
      "predicted_yield": 4.21,
      "market_price": 2180.0,
      "supply_index": 2.1832,
      "supply_level": "High Demand",
      "market_recommendation": "Few farmers grow this crop. Market demand is higher.",
      "expected_revenue": 9177.8,
      "score": 4204.76,
      "risk_level": "Low",
      "risk_reason": "Favorable farming conditions mapping high viability"
    }
  ]
}
```

### `POST /weather`
Real-time weather + annual rainfall for a district.

**Request:** `{ "district": "Thanjavur" }`

### `POST /supply`
Supply index for all crops in a region.

**Request:** `{ "state": "Tamil Nadu", "district": "Thanjavur" }`

---

## Project Structure

```
TrustAgri/
├── ai_modules/
│   ├── __init__.py
│   └── yield_prediction/
│       ├── __init__.py               # Public API exports
│       ├── config.py                 # Shared constants & paths
│       ├── train_model.py            # Model training script
│       ├── predict_model.py          # ML inference wrapper
│       ├── crop_recommendation_engine.py
│       ├── revenue_forecast.py       # Main orchestrator
│       ├── weather_service.py        # OpenWeather + Open-Meteo
│       ├── agmarknet_price_service.py
│       ├── supply_analysis.py
│       ├── risk_analysis.py
│       └── market_balance_engine.py
├── api/
│   ├── __init__.py
│   └── main.py                       # FastAPI server
├── models/                           # .pkl files (git-ignored)
│   ├── yield_model.pkl
│   └── crop_encoder.pkl
├── data/                             # CSV datasets (git-ignored)
│   ├── yield_df.csv
│   ├── India Agriculture Crop Production.csv
│   └── Agriculture_price_dataset.csv
├── tests/
│   ├── __init__.py
│   └── test_core.py                  # pytest test suite
├── .env                              # Your real keys (git-ignored)
├── .env.example                      # Template — safe to commit
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup & Running Locally

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd TrustAgri
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

Required keys:
- `OPENWEATHER_API_KEY` — [openweathermap.org/api](https://openweathermap.org/api)
- `AGMARKNET_API_KEY` — [data.gov.in](https://data.gov.in/)

### 3. Place datasets and models

Download the datasets and place them in `data/`.  
Place `yield_model.pkl` and `crop_encoder.pkl` in `models/`.

To retrain the model from scratch:
```bash
python -m ai_modules.yield_prediction.train_model
```

### 4. Start the API server

```bash
uvicorn api.main:app --reload
```

Server will be available at: `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

---

## Running Tests

```bash
# Fast unit tests only (no network, no API keys needed)
pytest tests/ -v -m "not integration"

# Full suite including live API calls
pytest tests/ -v
```

---

## External APIs Used

| API | Purpose | Key Required |
|-----|---------|-------------|
| [OpenWeatherMap](https://openweathermap.org/api) | Temperature, humidity | Yes (`OPENWEATHER_API_KEY`) |
| [Open-Meteo Archive](https://archive-api.open-meteo.com) | Annual rainfall (last 365 days) | No (free) |
| [Open-Meteo Geocoding](https://geocoding-api.open-meteo.com) | City → lat/lon | No (free) |
| [Agmarknet / data.gov.in](https://data.gov.in/) | Live crop market prices | Yes (`AGMARKNET_API_KEY`) |
