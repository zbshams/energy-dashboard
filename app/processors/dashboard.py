import json

CAT_MAP = {
    "HVAC": "HVAC",
    "Laundry": "Laundry",
    "Refrigeration": "Refrigeration",
    "Kitchen": "Kitchen",
    "Water Heating": "Water Heating",
    "EV Charging": "EV Charging",
    "Pool & Outdoor": "Pool & Outdoor",
    "Outlets & Misc": "Outlets & Misc"
}

CAT_ORDER = ["HVAC", "Kitchen", "Laundry", "Refrigeration", "Water Heating", "EV Charging", "Pool & Outdoor", "Outlets & Misc"]

def build_daily_data(daily_data, costs):
    """Build daily summary data"""
    daily = {"summary": {}, "devices": {}}
    
    for date, values in daily_data.items():
        daily["summary"][date] = {
            "cost": costs.get(date, 0),
            "total_kwh": sum(values) if isinstance(values, list) else 0
        }
    
    return daily

def build_hourly_data(hourly_data):
    """Build hourly breakdown data"""
    return {"by_hour": hourly_data}

def generate_daily_html(daily_data, hourly_data, daily_costs):
    """Generate daily dashboard HTML"""
    daily_summary = build_daily_data(daily_data, daily_costs)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Energy Dashboard - Daily View</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
        .card h3 {{ margin: 0 0 10px 0; color: #333; }}
        .metric {{ font-size: 24px; color: #007bff; font-weight: bold; }}
        .label {{ color: #666; font-size: 12px; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Energy Dashboard</h1>
        <div class="summary">
            <div class="card">
                <div class="label">Total Usage</div>
                <div class="metric" id="total-kwh">Loading...</div>
            </div>
            <div class="card">
                <div class="label">Total Cost</div>
                <div class="metric" id="total-cost">Loading...</div>
            </div>
            <div class="card">
                <div class="label">Average Daily Cost</div>
                <div class="metric" id="avg-cost">Loading...</div>
            </div>
        </div>
        <table id="daily-table">
            <thead>
                <tr><th>Date</th><th>Usage (kWh)</th><th>Cost</th></tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
    <script>
        const data = {json.dumps(daily_summary)};
        let totalKwh = 0, totalCost = 0, days = 0;
        
        Object.entries(data.summary).forEach(([date, info]) => {{
            totalKwh += info.total_kwh;
            totalCost += info.cost;
            days++;
            
            const row = document.createElement('tr');
            row.innerHTML = `<td>${{date}}</td><td>${{info.total_kwh.toFixed(2)}}</td><td>${{info.cost.toFixed(2)}}</td>`;
            document.querySelector('#daily-table tbody').appendChild(row);
        }});
        
        document.getElementById('total-kwh').textContent = totalKwh.toFixed(2) + ' kWh';
        document.getElementById('total-cost').textContent = '$' + totalCost.toFixed(2);
        document.getElementById('avg-cost').textContent = '$' + (totalCost / days || 0).toFixed(2);
    </script>
</body>
</html>"""
    return html

def generate_hourly_html(hourly_data):
    """Generate hourly dashboard HTML"""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Energy Dashboard - Hourly View</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; border-bottom: 2px solid #28a745; padding-bottom: 10px; }
        .placeholder { color: #999; padding: 40px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hourly View</h1>
        <div class="placeholder">Hourly breakdown data is being prepared...</div>
    </div>
</body>
</html>"""
    return html
