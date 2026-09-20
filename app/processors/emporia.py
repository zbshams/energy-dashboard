import zipfile
import io
import pandas as pd
from datetime import datetime

NAME_MAP = {
    "mains_a": "Mains", "mains_b": "Mains", "mains_c": "Mains",
    "hvac": "HVAC", "ac": "HVAC", "furnace": "HVAC",
    "dryer": "Laundry", "washer": "Laundry", "laundry": "Laundry",
    "refrigerator": "Refrigeration", "fridge": "Refrigeration", "freezer": "Refrigeration",
    "microwave": "Kitchen", "oven": "Kitchen", "stove": "Kitchen", "dishwasher": "Kitchen",
    "water heater": "Water Heating", "heater": "Water Heating",
    "pool pump": "Pool & Outdoor", "spa": "Pool & Outdoor", "outdoor": "Pool & Outdoor",
    "ev charger": "EV Charging", "tesla": "EV Charging", "charger": "EV Charging",
    "lights": "Outlets & Misc", "outlets": "Outlets & Misc", "misc": "Outlets & Misc"
}

SKIP = {"mains_a", "mains_b", "mains_c"}

def normalize_device_name(name):
    """Normalize device name to standard format"""
    normalized = name.lower().strip().replace("_", " ")
    for key, value in NAME_MAP.items():
        if key in normalized:
            return value
    return normalized.title()

def extract_emporia_zip(zip_bytes):
    """Extract and classify Emporia CSVs"""
    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
        daily_data = {}
        hourly_data = {}
        mains_daily = {}
        mains_hourly = {}
        
        for file in zip_file.namelist():
            if file.endswith("1DAY.csv"):
                panel_type = "Backup" if "Backup" in file else "Non_Backup"
                daily_data[panel_type] = parse_csv(zip_file.read(file).decode())
            elif file.endswith("1H.csv"):
                panel_type = "Backup" if "Backup" in file else "Non_Backup"
                hourly_data[panel_type] = parse_csv(zip_file.read(file).decode())
        
        merged_daily = merge_panels(daily_data)
        merged_hourly = merge_panels(hourly_data)
        
        return {
            "daily": merged_daily,
            "hourly": merged_hourly,
            "mains_daily": mains_daily,
            "mains_hourly": mains_hourly
        }
    except Exception as e:
        raise ValueError(f"Failed to process zip: {e}")

def parse_csv(csv_content):
    """Parse CSV data"""
    try:
        df = pd.read_csv(io.StringIO(csv_content))
        data = {}
        
        for col in df.columns:
            if col.lower() != "date" and col not in SKIP:
                device_name = normalize_device_name(col)
                data[device_name] = df[col].tolist()
        
        return {"timestamps": df["date"].tolist() if "date" in df.columns else [], "devices": data}
    except Exception as e:
        raise ValueError(f"CSV parsing failed: {e}")

def merge_panels(panel_data):
    """Merge Backup and Non_Backup panel data"""
    if not panel_data:
        return {"timestamps": [], "devices": {}}
    
    # Combine data from both panels
    merged_devices = {}
    timestamps = None
    
    for panel_type, data in panel_data.items():
        if data.get("timestamps"):
            timestamps = data["timestamps"]
        for device, values in data.get("devices", {}).items():
            if device not in merged_devices:
                merged_devices[device] = values
    
    return {"timestamps": timestamps or [], "devices": merged_devices}

def load_csv_files(backup_path, non_backup_path):
    """Load and process CSV files directly from filesystem"""
    try:
        daily_data = {}
        hourly_data = {}
        
        # Load backup panel daily data
        with open(backup_path, 'r') as f:
            daily_data["Backup"] = parse_csv(f.read())
        
        # Load non-backup panel daily data
        with open(non_backup_path, 'r') as f:
            daily_data["Non_Backup"] = parse_csv(f.read())
        
        # Create hourly data from daily (simple approach: assume hourly is same as daily for now)
        hourly_data = daily_data
        
        merged_daily = merge_panels(daily_data)
        merged_hourly = merge_panels(hourly_data)
        
        return {
            "daily": merged_daily,
            "hourly": merged_hourly,
            "mains_daily": {},
            "mains_hourly": {}
        }
    except Exception as e:
        raise ValueError(f"Failed to load CSV files: {e}")
