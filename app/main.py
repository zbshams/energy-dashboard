from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import os
import traceback

from app.config import DEFAULT_RATES, WEATHER_LAT, WEATHER_LON
from app.processors.emporia import extract_emporia_zip, load_csv_files
from app.processors.tou import calculate_tou_costs
from app.processors.dashboard import generate_daily_html, generate_hourly_html

app = FastAPI(title="Energy Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html>
<html>
<head>
<title>Energy Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
.header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
.header h1 { margin-bottom: 5px; }
.header p { opacity: 0.9; font-size: 14px; }
.container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
.loading { text-align: center; padding: 40px; font-size: 16px; color: #666; }
.spinner { display: inline-block; width: 30px; height: 30px; border: 3px solid #ddd; border-top: 3px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.dashboard { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 20px; }
.upload-section { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 20px; margin-top: 20px; }
.form-group { margin: 15px 0; }
label { display: block; margin-bottom: 5px; color: #666; font-weight: bold; }
input[type="file"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
button:hover { background: #0056b3; }
.status { margin-top: 15px; padding: 12px; border-radius: 4px; display: none; }
.status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
</head>
<body>
<div class="header">
<h1>Energy Dashboard</h1>
<p id="timestamp">Loading data...</p>
</div>
<div class="container">
<div id="dashboardContainer" class="loading">
<div class="spinner"></div>
<p>Loading your energy data...</p>
</div>
<div class="upload-section">
<h2>Update Data</h2>
<p style="margin-bottom: 15px; color: #666;">Upload a new Emporia Vue zip file to update the dashboard with fresh data.</p>
<form id="uploadForm">
<div class="form-group">
<label>Emporia Zip File:</label>
<input type="file" id="zipFile" accept=".zip" required>
</div>
<button type="submit">Upload & Refresh Dashboard</button>
</form>
<div id="status"></div>
</div>
</div>

<script>
window.addEventListener('DOMContentLoaded', async () => {
try {
const response = await fetch('/default-data');
if (!response.ok) throw new Error('Failed to load default data');
const data = await response.json();
displayDashboard(data);
} catch (error) {
document.getElementById('dashboardContainer').innerHTML = '<p style="color: #721c24;">Error loading default data: ' + error.message + '</p>';
}
});

document.getElementById('uploadForm').onsubmit = async (e) => {
e.preventDefault();
const statusDiv = document.getElementById('status');
const formData = new FormData();
formData.append('file', document.getElementById('zipFile').files[0]);

try {
statusDiv.textContent = 'Uploading...';
statusDiv.className = 'status';
statusDiv.style.display = 'block';

const response = await fetch('/upload', {
method: 'POST',
body: formData
});

if (!response.ok) {
const error = await response.json();
throw new Error(error.error || `Upload failed: ${response.status}`);
}

const result = await response.json();
statusDiv.className = 'status success';
statusDiv.textContent = `Success! Processed ${result.date_count} days with ${result.device_count} devices.`;
displayDashboard(result);
document.getElementById('zipFile').value = '';
} catch (error) {
statusDiv.className = 'status error';
statusDiv.textContent = `Error: ${error.message}`;
}
};

function displayDashboard(data) {
const container = document.getElementById('dashboardContainer');
container.className = 'dashboard';
container.innerHTML = data.daily_html || '<p>No dashboard data available</p>';
if (data.timestamp) {
document.getElementById('timestamp').textContent = `Last updated: ${data.timestamp}`;
}
}
</script>
</body>
</html>"""

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/default-data")
async def get_default_data():
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        backup_file = os.path.join(data_dir, "7C6538Backup_Panel1DAY.csv")
        non_backup_file = os.path.join(data_dir, "74E120Non_Backup_Panel1DAY.csv")
        
        if not os.path.exists(backup_file) or not os.path.exists(non_backup_file):
            return JSONResponse({"error": "Default data files not found"}, status_code=404)
        
        processed = load_csv_files(backup_file, non_backup_file)
        daily = processed["daily"]["devices"]
        hourly = processed["hourly"]["devices"]
        dates = processed["daily"]["timestamps"]
        
        if not dates:
            return JSONResponse({"error": "No data found in CSV files"}, status_code=400)
        
        costs = calculate_tou_costs(hourly, dates, DEFAULT_RATES)
        daily_html = generate_daily_html(daily, hourly, costs)
        
        return {
            "status": "success",
            "date_count": len(dates),
            "device_count": len(daily),
            "daily_html": daily_html,
            "hourly_html": "",
            "timestamp": dates[-1] if dates else "Unknown"
        }
    except Exception as e:
        print(f"Error in /default-data: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        zip_bytes = await file.read()
        processed = extract_emporia_zip(zip_bytes)
        daily = processed["daily"]["devices"]
        hourly = processed["hourly"]["devices"]
        dates = processed["daily"]["timestamps"]

        if not dates:
            return JSONResponse({"error": "No data found in zip"}, status_code=400)

        costs = calculate_tou_costs(hourly, dates, DEFAULT_RATES)
        daily_html = generate_daily_html(daily, hourly, costs)
        hourly_html = generate_hourly_html(hourly)

        return {
            "status": "success",
            "date_count": len(dates),
            "device_count": len(daily),
            "daily_html": daily_html,
            "hourly_html": hourly_html,
            "timestamp": dates[-1] if dates else "Unknown"
        }
    except Exception as e:
        print(f"Error in /upload: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
