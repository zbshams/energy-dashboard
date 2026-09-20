from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import json

from app.auth import verify_api_key
from app.config import DEFAULT_RATES, WEATHER_LAT, WEATHER_LON
from app.processors.emporia import extract_emporia_zip
from app.processors.weather import fetch_weather
from app.processors.tou import calculate_tou_costs
from app.processors.dashboard import generate_daily_html, generate_hourly_html

app = FastAPI(title="Energy Dashboard")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve upload form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Energy Dashboard - Upload</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; color: #666; font-weight: bold; }
            input[type="text"], input[type="file"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            #status { margin-top: 20px; padding: 10px; border-radius: 4px; display: none; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Energy Dashboard Upload</h1>
            <form id="uploadForm">
                <div class="form-group">
                    <label>API Key:</label>
                    <input type="text" id="apiKey" placeholder="Enter your API key" required>
                </div>
                <div class="form-group">
                    <label>Emporia Zip File:</label>
                    <input type="file" id="zipFile" accept=".zip" required>
                </div>
                <button type="submit">Upload & Generate Dashboard</button>
            </form>
            <div id="status"></div>
        </div>
        <script>
            document.getElementById('uploadForm').onsubmit = async (e) => {
                e.preventDefault();
                const statusDiv = document.getElementById('status');
                statusDiv.style.display = 'none';
                
                const formData = new FormData();
                formData.append('file', document.getElementById('zipFile').files[0]);
                
                try {
                    statusDiv.textContent = 'Uploading...';
                    statusDiv.className = '';
                    statusDiv.style.display = 'block';
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        headers: {'X-API-Key': document.getElementById('apiKey').value},
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Upload failed: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    statusDiv.className = 'success';
                    statusDiv.innerHTML = `<strong>Success!</strong><br>Processed ${result.date_count} days with ${result.device_count} devices.<br><a href="#" onclick="showDashboard('daily')">View Daily Dashboard</a> | <a href="#" onclick="showDashboard('hourly')">View Hourly Dashboard</a>`;
                    window.dashboardHtml = result;
                } catch (error) {
                    statusDiv.className = 'error';
                    statusDiv.textContent = `Error: ${error.message}`;
                }
            };
            
            function showDashboard(type) {
                const html = window.dashboardHtml[type === 'daily' ? 'daily_html' : 'hourly_html'];
                const newWindow = window.open();
                newWindow.document.write(html);
                newWindow.document.close();
            }
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), api_key: str = Depends(verify_api_key)):
    """Handle file upload and generate dashboards"""
    try:
        zip_bytes = await file.read()
        
        # Extract and process zip
        processed = extract_emporia_zip(zip_bytes)
        daily = processed["daily"]["devices"]
        hourly = processed["hourly"]["devices"]
        dates = processed["daily"]["timestamps"]
        
        if not dates:
            return JSONResponse({"error": "No data found in zip"}, status_code=400)
        
        # Fetch weather
        weather = fetch_weather(dates, WEATHER_LAT, WEATHER_LON)
        
        # Calculate costs
        costs = calculate_tou_costs(hourly, dates, DEFAULT_RATES)
        
        # Generate dashboards
        daily_html = generate_daily_html(daily, hourly, costs)
        hourly_html = generate_hourly_html(hourly)
        
        return {
            "status": "success",
            "date_count": len(dates),
            "device_count": len(daily),
            "daily_html": daily_html,
            "hourly_html": hourly_html
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
