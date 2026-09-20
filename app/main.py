from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.auth import verify_api_key
from app.processors.emporia import extract_emporia_zip
from app.processors.weather import fetch_weather
from app.processors.tou import calculate_tou_costs
from app.processors.dashboard import generate_daily_html, generate_hourly_html
import json
from datetime import datetime

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
        <title>Energy Dashboard Upload</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
            .container { background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; max-width: 600px; width: 100%; }
            h1 { color: #333; margin-bottom: 30px; font-size: 28px; }
            .form-group { margin-bottom: 24px; }
            label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; font-size: 14px; }
            input[type="text"], input[type="file"], input[type="number"], select { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border-color 0.3s; }
            input[type="text"]:focus, input[type="file"]:focus, input[type="number"]:focus, select:focus { outline: none; border-color: #667eea; }
            .rate-fields { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
            .rate-fields input { margin-bottom: 0; }
            .rate-label { font-size: 12px; color: #888; margin-top: 4px; }
            button { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
            button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4); }
            button:active { transform: translateY(0); }
            .error { background: #ffebee; color: #c62828; padding: 12px; border-radius: 8px; margin-top: 20px; display: none; }
            .success { background: #e8f5e9; color: #2e7d32; padding: 12px; border-radius: 8px; margin-top: 20px; display: none; }
            .progress { display: none; margin-top: 20px; }
            .progress-bar { width: 100%; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); width: 0%; transition: width 0.3s; }
            .progress-text { font-size: 13px; color: #666; margin-top: 8px; }
            .collapse-toggle { cursor: pointer; color: #667eea; font-weight: 500; user-select: none; display: inline-block; }
            .rate-section { display: none; }
            .rate-section.expanded { display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ Energy Dashboard</h1>
            <form id="uploadForm">
                <div class="form-group">
                    <label for="apiKey">API Key</label>
                    <input type="text" id="apiKey" placeholder="Enter your API key" required>
                </div>
                
                <div class="form-group">
                    <label for="zipFile">Emporia Zip File</label>
                    <input type="file" id="zipFile" accept=".zip" required>
                </div>

                <div class="form-group">
                    <div><span class="collapse-toggle" id="rateToggle">⚙️ Customize Rates (Optional)</span></div>
                    <div class="rate-section" id="rateSection">
                        <p style="margin: 12px 0 16px; color: #666; font-size: 13px;">Override default PECO TOU rates</p>
                        <div class="rate-fields">
                            <div>
                                <input type="number" id="superOffPeak" placeholder="0.053" step="0.001" min="0">
                                <div class="rate-label">Super Off-Peak (¢/kWh)</div>
                            </div>
                            <div>
                                <input type="number" id="offPeak" placeholder="0.076" step="0.001" min="0">
                                <div class="rate-label">Off-Peak (¢/kWh)</div>
                            </div>
                            <div>
                                <input type="number" id="peak" placeholder="0.32" step="0.001" min="0">
                                <div class="rate-label">Peak (¢/kWh)</div>
                            </div>
                        </div>
                    </div>
                </div>

                <button type="submit">Upload & Generate Dashboard</button>
                <div class="error" id="error"></div>
                <div class="success" id="success"></div>
                <div class="progress" id="progress">
                    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
                    <div class="progress-text" id="progressText">Processing...</div>
                </div>
            </form>
        </div>

        <script>
            // Load API key from localStorage
            const apiKeyInput = document.getElementById('apiKey');
            const savedKey = localStorage.getItem('energyDashboardApiKey');
            if (savedKey) {
                apiKeyInput.value = savedKey;
            }

            // Toggle rate section
            document.getElementById('rateToggle').addEventListener('click', () => {
                document.getElementById('rateSection').classList.toggle('expanded');
            });

            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const apiKey = document.getElementById('apiKey').value;
                const zipFile = document.getElementById('zipFile').files[0];
                const errorDiv = document.getElementById('error');
                const successDiv = document.getElementById('success');
                const progressDiv = document.getElementById('progress');

                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';

                if (!apiKey || !zipFile) {
                    errorDiv.textContent = 'Please enter API key and select a file';
                    errorDiv.style.display = 'block';
                    return;
                }

                // Save API key to localStorage
                localStorage.setItem('energyDashboardApiKey', apiKey);

                // Prepare form data
                const formData = new FormData();
                formData.append('file', zipFile);
                
                // Add custom rates if provided
                const sop = document.getElementById('superOffPeak').value;
                const op = document.getElementById('offPeak').value;
                const pk = document.getElementById('peak').value;
                if (sop || op || pk) {
                    formData.append('custom_rates', JSON.stringify({
                        'sop': sop ? parseFloat(sop) : null,
                        'op': op ? parseFloat(op) : null,
                        'pk': pk ? parseFloat(pk) : null
                    }));
                }

                progressDiv.style.display = 'block';
                document.getElementById('progressText').textContent = 'Uploading and processing...';
                document.getElementById('progressFill').style.width = '30%';

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        headers: {
                            'X-API-Key': apiKey
                        },
                        body: formData
                    });

                    document.getElementById('progressFill').style.width = '70%';

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Server error: ${response.status}`);
                    }

                    const data = await response.json();
                    document.getElementById('progressFill').style.width = '100%';
                    document.getElementById('progressText').textContent = `✓ Generated ${data.date_count} days of data with ${data.device_count} devices`;
                    
                    setTimeout(() => {
                        progressDiv.style.display = 'none';
                        successDiv.textContent = '✓ Dashboard generated! Check your downloads or look for the dashboard file.';
                        successDiv.style.display = 'block';
                    }, 500);

                } catch (error) {
                    progressDiv.style.display = 'none';
                    errorDiv.textContent = `Error: ${error.message}`;
                    errorDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), custom_rates: str = Form(None), api_key: str = Depends(verify_api_key)):
    try:
        # Read the uploaded zip file
        contents = await file.read()
        
        # Extract and process Emporia data
        daily_data, hourly_data, mains_daily, mains_hourly = extract_emporia_zip(contents)
        
        # Get date range for weather
        if daily_data:
            dates = list(daily_data.keys())
            weather_data = fetch_weather(dates)
        else:
            weather_data = {}
        
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
            except:
                pass
        
        # Calculate TOU costs
        daily_with_costs = calculate_tou_costs(daily_data, mains_daily, rates_override)
        hourly_with_costs = calculate_tou_costs(hourly_data, mains_hourly, rates_override)
        
        # Generate dashboards
        daily_html = generate_daily_html(daily_with_costs, weather_data)
        hourly_html = generate_hourly_html(hourly_with_costs, weather_data)
        
        return {
            "status": "success",
            "date_count": len(daily_data),
            "device_count": sum(len(v) for v in daily_data.values()) if daily_data else 0,
            "daily_html": daily_html,
            "hourly_html": hourly_html
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
