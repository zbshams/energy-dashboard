from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.processors.emporia import extract_emporia_zip
from app.processors.weather import fetch_weather
from app.processors.tou import calculate_tou_costs
from app.processors.dashboard import generate_daily_html
import json
from datetime import datetime
import traceback

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Energy Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header h1 { font-size: 24px; margin-bottom: 4px; }
            .header-meta { font-size: 13px; opacity: 0.9; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .controls { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
            .controls button { padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; transition: all 0.2s; }
            .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
            .btn-secondary { background: #e0e0e0; color: #333; }
            .btn-secondary:hover { background: #d0d0d0; }
            .rate-inputs { display: flex; gap: 12px; align-items: center; }
            .rate-inputs input { width: 80px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; }
            .rate-inputs label { font-size: 12px; color: #666; }
            .dashboard-view { display: none; }
            .dashboard-view.active { display: block; }
            .upload-form { display: none; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .upload-form.active { display: block; }
            .form-group { margin-bottom: 16px; }
            label { display: block; margin-bottom: 6px; color: #555; font-weight: 500; font-size: 14px; }
            input[type="file"] { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; }
            .error { background: #ffebee; color: #c62828; padding: 12px; border-radius: 6px; margin-top: 12px; display: none; font-size: 13px; }
            .success { background: #e8f5e9; color: #2e7d32; padding: 12px; border-radius: 6px; margin-top: 12px; display: none; }
            .progress { display: none; margin-top: 12px; }
            .progress-bar { width: 100%; height: 6px; background: #e0e0e0; border-radius: 3px; overflow: hidden; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); width: 0%; transition: width 0.3s; }
            #dashboardContent { background: white; border-radius: 8px; padding: 20px; }
            .empty-state { text-align: center; padding: 40px; color: #999; }
            .empty-state h2 { margin-bottom: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚡ Energy Dashboard</h1>
            <div class="header-meta" id="headerMeta">Loading...</div>
        </div>

        <div class="container">
            <div class="controls">
                <button class="btn-primary" id="toggleUpload">📤 Upload New Data</button>
                <div class="rate-inputs" id="rateControls" style="display: none;">
                    <label>Update Rates (¢/kWh):</label>
                    <input type="number" id="rateSOp" placeholder="0.053" step="0.001" min="0">
                    <input type="number" id="rateOp" placeholder="0.076" step="0.001" min="0">
                    <input type="number" id="ratePk" placeholder="0.32" step="0.001" min="0">
                    <button class="btn-secondary" id="applyRates">Apply Rates</button>
                </div>
            </div>

            <div class="dashboard-view active" id="dashboardView">
                <div class="empty-state" id="emptyState">
                    <h2>Loading Dashboard...</h2>
                </div>
                <div id="dashboardContent"></div>
            </div>

            <div class="upload-form" id="uploadForm">
                <h2 style="margin-bottom: 16px;">Upload New Emporia Data</h2>
                <div class="form-group">
                    <label for="zipFile">Select Zip File</label>
                    <input type="file" id="zipFile" accept=".zip" required>
                </div>
                <button class="btn-primary" id="submitBtn">Upload & Generate</button>
                <div class="error" id="error"></div>
                <div class="success" id="success"></div>
                <div class="progress" id="progress">
                    <div class="progress-bar"><div class="progress-fill"></div></div>
                </div>
            </div>
        </div>

        <script>
            let currentData = null;
            let currentRates = { sop: 0.053, op: 0.076, pk: 0.32 };

            async function loadDefaultData() {
                try {
                    const response = await fetch('/default-data');
                    if (response.ok) {
                        const data = await response.json();
                        currentData = data;
                        currentRates = data.rates || currentRates;
                        renderDashboard();
                        document.getElementById('rateControls').style.display = 'flex';
                        updateHeaderMeta(data.uploadDate);
                        document.getElementById('emptyState').style.display = 'none';
                    }
                } catch (e) {
                    console.error('Failed to load default data:', e);
                    document.getElementById('emptyState').innerHTML = '<h2>Ready to Upload</h2><p>Click "Upload New Data" to get started</p>';
                }
            }

            function updateHeaderMeta(uploadDate) {
                const date = uploadDate ? new Date(uploadDate).toLocaleDateString() : new Date().toLocaleDateString();
                document.getElementById('headerMeta').textContent = `As of: ${date} | Rates: ${(currentRates.sop*100).toFixed(1)}¢ SOp, ${(currentRates.op*100).toFixed(1)}¢ Op, ${(currentRates.pk*100).toFixed(1)}¢ Pk`;
            }

            function renderDashboard() {
                if (!currentData) return;
                const container = document.getElementById('dashboardContent');
                container.innerHTML = currentData.html;
            }

            document.getElementById('toggleUpload').addEventListener('click', () => {
                const form = document.getElementById('uploadForm');
                form.classList.toggle('active');
            });

            document.getElementById('submitBtn').addEventListener('click', async () => {
                const zipFile = document.getElementById('zipFile').files[0];
                const errorDiv = document.getElementById('error');
                const successDiv = document.getElementById('success');
                const progressDiv = document.getElementById('progress');

                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';

                if (!zipFile) {
                    errorDiv.textContent = 'Please select a zip file';
                    errorDiv.style.display = 'block';
                    return;
                }

                const formData = new FormData();
                formData.append('file', zipFile);
                formData.append('custom_rates', JSON.stringify(currentRates));

                progressDiv.style.display = 'block';

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        const text = await response.text();
                        throw new Error(text || `Upload failed: ${response.status}`);
                    }

                    const data = await response.json();
                    
                    currentData = data;
                    localStorage.setItem('energyDashboardData', JSON.stringify({
                        data: currentData,
                        rates: currentRates,
                        uploadDate: new Date().toISOString()
                    }));

                    progressDiv.style.display = 'none';
                    successDiv.textContent = '✓ Data uploaded! Refresh to see updates.';
                    successDiv.style.display = 'block';

                    setTimeout(() => {
                        location.reload();
                    }, 1500);

                } catch (error) {
                    progressDiv.style.display = 'none';
                    errorDiv.textContent = `Error: ${error.message}`;
                    errorDiv.style.display = 'block';
                }
            });

            document.getElementById('applyRates').addEventListener('click', async () => {
                const sop = parseFloat(document.getElementById('rateSOp').value) || currentRates.sop;
                const op = parseFloat(document.getElementById('rateOp').value) || currentRates.op;
                const pk = parseFloat(document.getElementById('ratePk').value) || currentRates.pk;

                currentRates = { sop, op, pk };
                updateHeaderMeta(new Date().toISOString());
                renderDashboard();
            });

            // Load default data on page load
            loadDefaultData();
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/default-data")
async def get_default_data():
    """Load default dashboard data if it exists"""
    try:
        # Try to load from localStorage data (would be set after first upload)
        saved = None
        # For now, return empty - will be populated after first upload
        raise HTTPException(status_code=404, detail="No default data")
    except Exception as e:
        raise HTTPException(status_code=404, detail="No data available")

@app.post("/upload")
async def upload(file: UploadFile = File(...), custom_rates: str = Form(None)):
    try:
        contents = await file.read()
        
        if not contents:
            raise ValueError("File is empty")
        
        # Extract and process Emporia data
        daily_data, hourly_data, mains_daily, mains_hourly = extract_emporia_zip(contents)
        
        if not daily_data:
            raise ValueError("No data found in zip file")
        
        # Get date range for weather
        dates = list(daily_data.keys())
        weather_data = fetch_weather(dates)
        
        # Parse custom rates if provided
        rates_override = None
        if custom_rates:
            try:
                rates_dict = json.loads(custom_rates)
                rates_override = {}
                for date_str in daily_data.keys():
                    rates_override[date_str] = {}
                    if rates_dict.get('sop'):
                        rates_override[date_str]['sop'] = rates_dict['sop']
                    if rates_dict.get('op'):
                        rates_override[date_str]['op'] = rates_dict['op']
                    if rates_dict.get('pk'):
                        rates_override[date_str]['pk'] = rates_dict['pk']
            except Exception as e:
                print(f"Error parsing rates: {e}")
        
        # Calculate TOU costs
        daily_with_costs = calculate_tou_costs(daily_data, mains_daily, rates_override)
        daily_html = generate_daily_html(daily_with_costs, weather_data)
        
        return {
            "status": "success",
            "date_count": len(daily_data),
            "device_count": sum(len(v) for v in daily_data.values()) if daily_data else 0,
            "html": daily_html,
            "rates": json.loads(custom_rates) if custom_rates else {"sop": 0.053, "op": 0.076, "pk": 0.32},
            "uploadDate": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
