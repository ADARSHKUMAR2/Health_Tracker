import sqlite3
from agents import function_tool

@function_tool
def fetch_health_metrics(start_date: str, end_date: str) -> str:
    """
    Fetches the user's daily health and biometric metrics for a given date range.
    Use this tool whenever the user asks about their sleep, heart rate, or calories.
    
    Args:
        start_date: The start date in YYYY-MM-DD format.
        end_date: The end date in YYYY-MM-DD format.
    """
    # Connect to your SQLite database
    conn = sqlite3.connect("health_data.db")
    cursor = conn.cursor()
    
    query = """
        SELECT date, sleep_hours, deep_sleep_hours, resting_hr, active_calories 
        FROM daily_metrics 
        WHERE date BETWEEN ? AND ?
    """
    cursor.execute(query, (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return "No health data found for this date range."
        
    # Format the data into a readable string for the LLM
    result = "Health Data:\n"
    for row in rows:
        result += f"- {row[0]}: Sleep: {row[1]}h (Deep: {row[2]}h), RHR: {row[3]}bpm, Burned: {row[4]}kcal\n"
        
    return result
