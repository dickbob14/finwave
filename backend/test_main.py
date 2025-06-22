"""
Minimal test FastAPI app for Block D testing
"""
from fastapi import FastAPI

app = FastAPI(
    title="FinWave Test API",
    description="Minimal test for Block D functionality",
    version="3.0.0"
)

@app.get("/")
def root():
    return {"message": "FinWave Block D Test Server", "status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "sqlite_test",
        "features": ["charts", "export", "insights"]
    }

# Import Block D routes one by one to isolate issues
try:
    from routes.charts import router as charts_router
    app.include_router(charts_router, prefix="/charts", tags=["charts"])
    print("✓ Charts router loaded")
except Exception as e:
    print(f"✗ Charts router failed: {e}")

try:
    from routes.export import router as export_router
    app.include_router(export_router, prefix="/export", tags=["export"])
    print("✓ Export router loaded")
except Exception as e:
    print(f"✗ Export router failed: {e}")

try:
    from routes.insight import router as insight_router
    app.include_router(insight_router, prefix="/insight", tags=["insights"])
    print("✓ Insight router loaded")
except Exception as e:
    print(f"✗ Insight router failed: {e}")

try:
    from routes.report import router as report_router
    app.include_router(report_router, prefix="/report", tags=["reports"])
    print("✓ Report router loaded")
except Exception as e:
    print(f"✗ Report router failed: {e}")