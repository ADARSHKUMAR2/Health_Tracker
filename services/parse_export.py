# scripts/parse_export.py
import sqlite3
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from backend.storage_s3 import download_db_from_s3, upload_db_to_s3

def parse_apple_health_xml():
    # 1. Resolve relative paths
    root_dir = Path(__file__).resolve().parent.parent
    xml_path = root_dir / "data" / "export.xml"
    db_path = root_dir / "data" / "health_data.db"
    
    if not xml_path.exists():
        print(f"❌ Could not find export.xml at {xml_path}")
        return

    download_db_from_s3()
    print("🚀 Starting stream analysis of export.xml (this might take a minute)...")
    
    # In-memory dictionaries to aggregate daily records
    daily_steps = defaultdict(float)
    daily_rhr = defaultdict(list)
    daily_sleep = defaultdict(float)

    # 2. Stream the XML file to save memory
    context = ET.iterparse(xml_path, events=("end",))
    
    count = 0
    for event, elem in context:
        if elem.tag == "Record":
            count += 1
            attr = elem.attrib
            record_type = attr.get("type")
            start_date_str = attr.get("startDate")
            value_str = attr.get("value", "0")
            
            if start_date_str:
                # Extract date string 'YYYY-MM-DD'
                date_key = start_date_str[:10]
                
                # Parse Steps
                if record_type == "HKQuantityTypeIdentifierStepCount":
                    try:
                        daily_steps[date_key] += float(value_str)
                    except ValueError:
                        pass
                        
                # Parse Resting Heart Rate
                elif record_type == "HKQuantityTypeIdentifierRestingHeartRate":
                    try:
                        daily_rhr[date_key].append(float(value_str))
                    except ValueError:
                        pass
                
                # Parse Sleep Analysis
                elif record_type == "HKCategoryTypeIdentifierSleepAnalysis":
                    # For sleep, duration is calculated from startDate and endDate
                    end_date_str = attr.get("endDate")
                    if end_date_str and "Asleep" in value_str:
                        try:
                            fmt = "%Y-%m-%d %H:%M:%S %z"
                            # Clean up string if timezone format varies
                            start_dt = datetime.strptime(start_date_str[:-6], "%Y-%m-%d %H:%M:%S")
                            end_dt = datetime.strptime(end_date_str[:-6], "%Y-%m-%d %H:%M:%S")
                            duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
                            daily_sleep[date_key] += duration_hours
                        except Exception:
                            pass

            if count % 200000 == 0:
                print(f"Processed {count} health records...")
                
        # Clear element memory safely
        elem.clear()
    
    del context # Free memory stream

    print(f"✅ Processing complete. Aggregated {len(daily_steps)} unique days.")
    print(f"💾 Saving historical data to database at: {db_path}")

    # 3. Batch save the parsed metrics into SQLite
    all_dates = set(daily_steps.keys()) | set(daily_rhr.keys()) | set(daily_sleep.keys())
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_metrics (
            date TEXT PRIMARY KEY,
            sleep_hours REAL DEFAULT 0.0,
            deep_sleep_hours REAL DEFAULT 0.0,
            resting_hr INTEGER DEFAULT 0,
            active_calories INTEGER DEFAULT 0,
            step_count INTEGER DEFAULT 0,
            workout_type TEXT DEFAULT 'None'
        )
    """)

    upsert_count = 0
    for d in sorted(all_dates):
        steps = int(daily_steps.get(d, 0))
        sleep = round(daily_sleep.get(d, 0.0), 2)
        
        # Calculate mean for resting heart rate if records exist
        rhr_list = daily_rhr.get(d, [])
        rhr = int(sum(rhr_list) / len(rhr_list)) if rhr_list else 0
        
        cursor.execute("""
            INSERT INTO daily_metrics (date, step_count, resting_hr, sleep_hours)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                step_count = excluded.step_count,
                resting_hr = max(excluded.resting_hr, daily_metrics.resting_hr),
                sleep_hours = max(excluded.sleep_hours, daily_metrics.sleep_hours)
        """, (d, steps, rhr, sleep))
        upsert_count += 1

    conn.commit()
    conn.close()
    print(f"🎉 Successfully imported {upsert_count} calendar days of historical metrics!")

    upload_db_to_s3()

if __name__ == "__main__":
    parse_apple_health_xml()