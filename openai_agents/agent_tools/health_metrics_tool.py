import sqlite3
from pathlib import Path
from agents import function_tool

@function_tool
def fetch_health_metrics(start_date: str, end_date: str) -> str:
    """
    Fetches the user's daily health metrics along with clean, pre-calculated 
    summary statistics directly from the database engine. 
    Use this tool whenever the user asks for summaries, averages, or trends.
    """
    db_path = Path(__file__).resolve().parent.parent.parent / "data" / "health_data.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Let SQL handle the math perfectly, ignoring 0s for heart rate
    cursor.execute("""
        SELECT 
            CAST(AVG(step_count) AS INTEGER),
            CAST(AVG(CASE WHEN resting_hr > 0 THEN resting_hr END) AS INTEGER),
            COUNT(CASE WHEN resting_hr > 0 THEN 1 END)
        FROM daily_metrics 
        WHERE date BETWEEN ? AND ?
    """, (start_date, end_date))
    
    avg_steps, avg_rhr, valid_rhr_days = cursor.fetchone()
    
    # 2. Fetch the daily breakdown so the agent can still see historical trends
    cursor.execute("""
        SELECT date, sleep_hours, resting_hr, step_count 
        FROM daily_metrics 
        WHERE date BETWEEN ? AND ?
        ORDER BY date ASC
    """, (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "No health data found for this date range."
        
    # 3. Construct a clear, unambiguous text package for the LLM
    output = f"--- Database Calculated Statistics ({start_date} to {end_date}) ---\n"
    output += f"- Calculated Average Steps: {avg_steps if avg_steps else 0} steps/day\n"
    output += f"- Calculated Average RHR: {avg_rhr if avg_rhr else 'N/A'} bpm (Based on {valid_rhr_days} tracked days)\n\n"
    
    output += "--- Raw Daily Trends ---\n"
    for row in rows:
        rhr_text = f"{row[2]} bpm" if row[2] > 0 else "Missing/Not Tracked"
        output += f"- {row[0]}: Steps: {row[3]} | RHR: {rhr_text} | Sleep: {row[1]}h\n"
        
    return output