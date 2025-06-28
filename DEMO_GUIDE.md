# 🚀 FinWave Demo Guide

## Quick Start (One Command!)

```bash
cd /Users/alexandermillar/finwave
./start_demo.sh
```

This single command will:
1. Kill any existing processes on ports 3000 and 8000
2. Start the backend API server
3. Start the frontend development server
4. Show you the URLs to access

## Manual Start (If You Prefer)

### Terminal 1 - Backend:
```bash
cd /Users/alexandermillar/finwave/backend
source venv/bin/activate
python init_production.py  # Only needed first time
uvicorn app.main:app --reload --port 8000
```

### Terminal 2 - Frontend:
```bash
cd /Users/alexandermillar/finwave/frontend
npm run dev
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000 (or http://localhost:3002 if 3000 is busy)
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 📱 Demo Flow

### 1. Landing Page (http://localhost:3000)
- Shows FinWave branding with your Deep Navy/Ocean Teal colors
- Click "Get Started" or navigate to Dashboard

### 2. Empty Dashboard 
- Initially shows "No data yet" state
- Click "Connect Data Source" button

### 3. OAuth Configuration (The Magic!)
- Choose "QuickBooks" (or any integration)
- Click "Configure OAuth App"
- Enter your Intuit Developer credentials:
  ```
  Client ID: [Your Intuit App Client ID]
  Client Secret: [Your Intuit App Client Secret]
  Environment: Sandbox (for demo)
  ```
- Click "Save Configuration"

### 4. Connect & Authorize
- Click "Connect QuickBooks"
- You'll be redirected to Intuit's OAuth page
- Log in with your Intuit developer account
- Select your sandbox company
- Authorize the connection

### 5. Real-Time Data Sync
- After authorization, you're redirected back
- The system automatically starts syncing data
- Progress bar shows sync status
- Takes 30-60 seconds for full sync

### 6. Live Dashboard
Now you have real data! Navigate to:
- **Dashboard** (`/dashboard`) - KPIs and metrics from actual QuickBooks data
- **Reports** (`/reports`) - Generate board reports with real financials
- **Metrics** (`/metrics`) - Detailed time-series of actual metrics
- **Alerts** (`/alerts`) - Variance alerts based on real data
- **Forecast** (`/forecast`) - Scenario planning with actual baseline

### 7. Board Report Generation
- Go to Reports page
- Click "Generate Board Report"
- Select date range
- Click "Generate PDF"
- Downloads a professional report with:
  - Your FinWave branding
  - Real financial statements
  - AI-generated insights
  - Variance analysis

## 🔑 Key Demo Points

1. **No Mock Data** - Everything comes from real APIs
2. **Live OAuth Flow** - Shows actual enterprise integration
3. **Real-Time Sync** - Watch as data flows in
4. **Professional Output** - Board-ready PDFs with your branding
5. **AI Insights** - GPT-4 analysis of actual variances

## 🛠️ Troubleshooting

### Frontend won't start?
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Backend import errors?
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Port already in use?
```bash
# Kill processes on ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### WeasyPrint error?
This is just a warning - PDF generation will still work using the fallback renderer.

## 📊 Demo Data Sources

You can connect:
- **QuickBooks** - Financial data (P&L, Balance Sheet, GL)
- **Salesforce** - Customer & pipeline data
- **HubSpot** - Marketing metrics
- **Gusto** - Payroll data

Each requires your own developer account credentials.

## 🎯 Demo Script Suggestions

1. **Opening**: "Let me show you how FinWave transforms financial reporting..."
2. **OAuth Setup**: "First, I'll connect my QuickBooks sandbox - notice this is the same OAuth flow your team would use..."
3. **Data Sync**: "Watch as we pull in real financial data - no manual entry needed..."
4. **Report Generation**: "Now with one click, we generate a board-ready report..."
5. **AI Insights**: "Notice how the AI automatically identifies and explains variances..."

## 🛑 Stopping Everything

Press `Ctrl+C` in the terminal running `start_demo.sh`, or:

```bash
# Manual stop
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

---

Ready to demo? Just run `./start_demo.sh` and you're live in seconds!