# app/routers/dashboard.py
from fastapi import APIRouter, HTTPException
# Import your specific functions
from services.analytics import get_daily_summary, get_period_stats
import traceback

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard")
async def get_dashboard(user_id: str):
    try:
        # Call your analytics logic safely
        data = get_daily_summary(user_id)
        return data
    except Exception as e:
        # If it fails, print the error instead of crashing the server
        print(f"❌ Dashboard Logic Error: {e}")
        traceback.print_exc()
        # Return a 500 error so the frontend knows something is wrong
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/period")
async def get_analytics_period(user_id: str, start_date: str, end_date: str):
    try:
        stats = get_period_stats(user_id, start_date, end_date)
        return {"stats": stats}
    except Exception as e:
        print(f"❌ Analytics Period Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
