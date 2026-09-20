# Energy Dashboard Web Application

A FastAPI web application that processes Emporia Vue energy data and generates interactive dashboards.

## Features

- **Emporia Integration**: Processes Emporia Vue zip exports (dual-panel support)
- **Weather Data**: Integrates Open-Meteo weather API for contextual energy analysis
- **Time-of-Use Calculations**: Applies PECO Smart Time rates to calculate electricity costs
- **Interactive Dashboards**: Generates self-contained HTML dashboards
- **Secure Upload**: API key authentication for file uploads
- **Cloud Ready**: Designed for Google Cloud Run deployment

## Project Structure

```
energy-dashboard/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration & environment variables
│   ├── auth.py                # API key authentication
│   ├── main.py                # FastAPI application & endpoints
│   └── processors/
│       ├── emporia.py         # Emporia CSV parsing
│       ├── weather.py         # Weather data fetching
│       ├── tou.py             # Time-of-Use calculations
│       └── dashboard.py       # HTML dashboard generation
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Setup Instructions

### 1. Create Python Virtual Environment

```bash
cd ~/Claude\ Cowork/energy-dashboard
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you encounter PyPI network errors, proceed directly to cloud deployment.

### 3. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```
API_KEY_ZUBE=your-unique-key-here
API_KEY_ASSISTANT=your-assistant-key-here
```

### 4. Run Locally

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` to access the upload form.

## API Endpoints

- `GET /` - Upload form UI
- `GET /health` - Health check
- `POST /upload` - Upload Emporia zip file
  - Header: `X-API-Key: <your-api-key>`
  - Body: Multipart form with zip file

## Cloud Deployment (Google Cloud Run)

See `Dockerfile` and Cloud Build configuration for deployment steps.

## Configuration

Key settings in `app/config.py`:

- **API Keys**: Set via `API_KEY_ZUBE` and `API_KEY_ASSISTANT` environment variables
- **Weather Location**: Default Wayne, PA (40.0426°N, 75.3899°W)
- **TOU Rates**: PECO Smart Time schedule configured in `DEFAULT_RATES`
- **Cache TTL**: 86,400 seconds (1 day) for weather data

## Testing

Test the upload endpoint with curl:

```bash
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: dev-key-zube-12345" \
  -F "file=@your-emporia-export.zip"
```

## Troubleshooting

### Network Errors
If pip install fails due to network restrictions, deploy to Google Cloud Run which has full internet access.

### Missing Dependencies
Verify Python 3.8+ is installed:
```bash
python3 --version
```

### Import Errors
Ensure virtual environment is activated:
```bash
source venv/bin/activate
```
