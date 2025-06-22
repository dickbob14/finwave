# FinWave - AI-Powered Financial Analytics Platform

Transform your financial reporting with real-time QuickBooks integration, automated KPI tracking, and board-ready PDF reports.

![FinWave Dashboard](https://via.placeholder.com/800x400?text=FinWave+Dashboard)

## 🚀 Quick Start

Get FinWave running in minutes with QuickBooks sandbox data:

```bash
# Clone the repository
git clone https://github.com/yourusername/finwave.git
cd finwave

# Copy environment variables and add your credentials
cp backend/.env.example backend/.env

# Run the automated setup script
cd backend
chmod +x scripts/dev_quick_setup.sh
./scripts/dev_quick_setup.sh
```

The setup script will:
1. ✅ Initialize the database
2. ✅ Create a demo workspace for Craig's Design & Landscaping
3. ✅ Sync QuickBooks sandbox data
4. ✅ Calculate metrics and generate forecasts
5. ✅ Start both backend and frontend servers

## 📋 Manual Setup

If you prefer manual setup:

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
make init-db

# Create demo workspace and sync data
python scripts/seed_demo.py

# Run all scheduler jobs
make scheduler-all

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

## 🔑 Environment Variables

Edit `backend/.env` with your credentials:

```env
# QuickBooks Sandbox (required)
QB_CLIENT_ID=your_quickbooks_client_id
QB_CLIENT_SECRET=your_quickbooks_client_secret
QB_COMPANY_ID=9341454888200521  # Craig's Design & Landscaping
QB_ENVIRONMENT=sandbox

# OpenAI (required for AI insights)
OPENAI_API_KEY=your_openai_api_key

# Database (default: DuckDB)
DATABASE_URL=duckdb:///dev.duckdb

# Security
FERNET_SECRET=generate_with_python_cryptography
JWT_SECRET=your_secret_key
```

## 🎯 Key Features

### 1. **QuickBooks Integration**
- Real-time sync with QuickBooks Online
- Automatic metric calculation
- Historical data import

### 2. **KPI Dashboard**
- Revenue, burn rate, runway tracking
- Real-time variance monitoring
- Custom metric definitions

### 3. **Board Reports**
- One-click PDF generation
- Professional formatting
- AI-powered insights

### 4. **Scenario Planning**
- Interactive what-if analysis
- Driver-based forecasting
- Multiple scenario comparison

### 5. **Variance Alerts**
- Automatic anomaly detection
- Customizable thresholds
- Email notifications

## 🏗️ Architecture

```
finwave/
├── backend/
│   ├── app/               # FastAPI application
│   ├── models/            # SQLAlchemy models
│   ├── routes/            # API endpoints
│   ├── integrations/      # QuickBooks, CRM, Payroll
│   ├── metrics/           # Metric store & calculations
│   ├── reports/           # PDF generation
│   ├── scheduler/         # Background jobs
│   └── templates/         # Excel templates
│
└── frontend/
    ├── src/
    │   ├── app/           # Next.js pages
    │   ├── components/    # React components
    │   └── lib/           # Utilities
    └── public/            # Static assets
```

## 📡 API Endpoints

- `GET /api/oauth/dev/quick_setup` - Quick demo setup
- `GET /api/{workspace_id}/metrics` - List metrics
- `GET /api/{workspace_id}/reports/board-pack.pdf` - Generate PDF
- `POST /api/{workspace_id}/forecast/scenario` - Run scenarios
- `GET /api/{workspace_id}/alerts` - Variance alerts

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm run test
```

## 🚢 Deployment

### Using Docker

```bash
docker-compose up -d
```

### Manual Deployment

1. Set production environment variables
2. Run database migrations
3. Configure reverse proxy (nginx)
4. Set up SSL certificates
5. Configure monitoring

## 📚 Documentation

- [API Documentation](http://localhost:8000/api/docs)
- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🆘 Support

- Email: support@finwave.io
- Documentation: https://docs.finwave.io
- Issues: https://github.com/yourusername/finwave/issues

---

Built with ❤️ by the FinWave team