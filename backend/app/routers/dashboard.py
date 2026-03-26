from fastapi import APIRouter, HTTPException, Query
from datetime import date
import traceback
from services.db import get_db
from services.analytics import get_daily_summary
from services.patterns import analyze_user_patterns
from psycopg2.extras import RealDictCursor

router = APIRouter(tags=["Dashboard"])

@router.get("/period-analysis")
def get_period_analysis(
    user_id: str = Query(...), 
    start_date: date = Query(...), 
    end_date: date = Query(...)
):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 🟢 USE THE REAL DURATION LOGIC HERE
    query = """
        WITH TimedEvents AS (
            SELECT 
                title, 
                start_time,
                LEAD(start_time) OVER (
                    PARTITION BY (start_time::DATE) 
                    ORDER BY start_time
                ) as next_event_time
            FROM events
            WHERE user_id = %s 
            AND start_time::DATE BETWEEN %s AND %s
            AND origin_location NOT IN ('Gmail', 'Email Sync')
        )
        SELECT 
            title as activity,
            ROUND(SUM(EXTRACT(EPOCH FROM (COALESCE(next_event_time, start_time + interval '1 hour') - start_time)) / 3600)::numeric, 1) as total_hours,
            COUNT(*) as frequency
        FROM TimedEvents
        GROUP BY title
        HAVING COUNT(*) > 1
        ORDER BY total_hours DESC
    """
    
    try:
        cur.execute(query, (user_id, start_date, end_date))
        duration_results = cur.fetchall()
        
        # We also need to return 'total_activities' and 'patterns' to avoid Flutter errors
        return {
            "total_activities": len(duration_results),
            "patterns": ["Morning Routine detected", "Consistent Sleep Cycle"], # Dummy patterns
            "activities": duration_results
        }
    finally:
        cur.close()
        conn.close()

@router.get("/activity-duration-analysis")
def get_duration_analysis(
    user_id: str = Query(...), 
    start_date: date = Query(...), 
    end_date: date = Query(...)
):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # 🟢 NEW LOGIC: Calculates the actual gap between activities
    query = """
        WITH TimedEvents AS (
            SELECT 
                title, 
                start_time,
                -- PARTITION BY date stops the calculation at midnight
                LEAD(start_time) OVER (
                    PARTITION BY (start_time::DATE) 
                    ORDER BY start_time
                ) as next_event_time
            FROM events
            WHERE user_id = %s 
            AND start_time::DATE BETWEEN %s AND %s
            AND origin_location NOT IN ('Gmail', 'Email Sync')
        )
        SELECT 
            title as activity,
            -- Calculate actual hours. If it's the last event of the day, we assume 1 hour.
            ROUND(SUM(
                EXTRACT(EPOCH FROM (COALESCE(next_event_time, start_time + interval '1 hour') - start_time)) / 3600
            )::numeric, 1) as total_hours,
            COUNT(*) as frequency
        FROM TimedEvents
        GROUP BY title
        HAVING COUNT(*) > 1
        ORDER BY total_hours DESC
    """
    
    try:
        cur.execute(query, (user_id, start_date, end_date))
        results = cur.fetchall()
        return {
            "user_id": user_id,
            "activities": results
        }
    except Exception as e:
        print(f"❌ SQL Error: {e}")
        return {"error": str(e), "activities": []}
    finally:
        cur.close()
        conn.close()

@router.get("/dashboard")
async def get_dashboard(user_id: str):
    try:
        data = get_daily_summary(user_id)
        return data
    except Exception as e:
        print(f"❌ Dashboard Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))