# FinWave QuickStart Guide 🚀

## 🔐 First Time Setup (5 minutes)

```bash
# 1. Clone and enter project
git clone <repo>
cd finwave/backend

# 2. Create virtual environment
make dev-setup
source venv/bin/activate

# 3. Install dependencies
make install

# 4. Configure credentials securely
./scripts/secure_setup.sh

# 5. Run smoke tests
./scripts/smoke_test.sh
```

## 🧪 Daily Development Flow

```bash
# Always start with
source venv/bin/activate
export $(grep -v '^#' .env | xargs)

# Test QuickBooks connection
make test-qb-connection

# Generate templates with real data
make populate-3statement-real SINCE=2024-01-01 UNTIL=2024-12-31

# Start API server
uvicorn app.main:app --reload
```

## 📊 Key API Endpoints

### Refresh 3-Statement Model
```bash
curl -X POST "http://localhost:8000/templates/3statement/refresh?start_date=2024-01-01&end_date=2024-12-31" \
  -o 3statement.xlsx
```

### Get KPI Snapshot
```bash
curl "http://localhost:8000/templates/kpi_dashboard/snapshot?metrics=revenue_mtd,expenses_mtd"
```

### List All Templates
```bash
curl http://localhost:8000/templates/
```

## 🆕 Adding New Templates

1. **Upload template file**
   ```bash
   cp ~/Downloads/NewTemplate.xlsx templates/files/
   ```

2. **Validate structure**
   ```bash
   make template-validate FILE=templates/files/NewTemplate.xlsx
   ```

3. **Register template**
   ```bash
   make template-register FILE=templates/files/NewTemplate.xlsx NAME=new_template
   ```

4. **Generate populator with Claude**
   ```bash
   cd templates
   python register_template.py prompt --name new_template > claude_prompt.txt
   # Copy prompt to Claude, save response as populate_new_template.py
   ```

## 🔍 Troubleshooting

### No QuickBooks Data?
- Check date range - sandbox may have limited data
- Try previous year: `SINCE=2023-01-01 UNTIL=2023-12-31`
- Check logs: `tail -f templates/logs/*.log`

### Token Expired?
- Delete `qb_tokens.json` and re-run connection test
- OAuth tokens expire after 1 hour

### Field Mapping Issues?
- Edit `config/field_maps/quickbooks.yml`
- No code changes needed!
- Run `make test-qb-integration` to verify

## 🚨 Security Reminders

1. **NEVER** commit `.env` or `*_tokens.json`
2. Always run `git status` before committing
3. Use GitHub Secrets for CI/CD
4. Rotate credentials regularly

## 📚 Key Files

- `.env` - Your credentials (git-ignored)
- `config/field_maps/quickbooks.yml` - Field mappings
- `templates/populated/` - Generated reports
- `integrations/quickbooks/client.py` - QB API client
- `routes/templates.py` - API endpoints

## 🎯 Next Steps

1. **Frontend**: Build template browser UI
2. **Insights**: Add GPT-4 commentary engine
3. **Integrations**: Connect Salesforce, HubSpot
4. **Automation**: Schedule nightly refreshes

---

**Need help?** Check `scripts/smoke_test.sh` output or ping the team!