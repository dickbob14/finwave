# FinWave Backend Makefile
# Convenient shortcuts for common tasks

# Virtual environment configuration
VENV ?= venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip

.PHONY: help templates etl test-templates server qb-server all clean forecast variance scheduler

help:
	@echo "FinWave Backend Commands:"
	@echo "  make templates     - Generate Excel board pack template"
	@echo "  make etl          - Populate template with QuickBooks data"
	@echo "  make test         - Run template tests"
	@echo "  make server       - Start QuickBooks integration server"
	@echo "  make demo-server  - Start demo server (no QB required)"
	@echo "  make all          - Generate template and run ETL"
	@echo "  make clean        - Remove generated files"
	@echo ""
	@echo "Forecasting & Alerts:"
	@echo "  make forecast      - Generate metric forecasts"
	@echo "  make variance      - Check variance rules and generate alerts"
	@echo "  make scheduler     - Run all scheduled jobs"

# Generate Excel template
templates:
	@echo "🏗️  Generating FinWave Board Pack template..."
	@cd templates && ../$(PYTHON) -m make_templates
	@echo "✅ Template created at: backend/assets/templates/finwave_board_pack.xlsx"

# Run ETL to populate template
etl:
	@echo "📊 Populating template with QuickBooks data..."
	@cd templates && ../$(PYTHON) -m etl_qb_to_excel --template ../assets/templates/finwave_board_pack.xlsx
	@echo "✅ Populated template saved"

# Run template tests
test-templates:
	@echo "🧪 Running template tests..."
	@cd templates && ../$(PYTHON) test_templates.py

# Start QuickBooks server
server:
	@echo "🚀 Starting QuickBooks integration server..."
	@$(PYTHON) qb_server.py

# Start demo server
demo-server:
	@echo "🚀 Starting demo server..."
	@$(PYTHON) demo_server.py

# Generate template and populate with data
all: templates etl
	@echo "✅ Board pack ready!"

# Populate 3-Statement Model
populate-3statement:
	@echo "📊 Populating 3-Statement Model..."
	@cd templates && ../$(PYTHON) populate_3statement.py --since $${SINCE:-2024-01-01} --until $${UNTIL:-2024-12-31}
	@echo "✅ 3-Statement Model populated"

# Populate KPI Dashboard
populate-kpi:
	@echo "📊 Populating KPI Dashboard..."
	@cd templates && ../$(PYTHON) populate_kpi_dashboard.py --since $${SINCE:-2024-01-01} --until $${UNTIL:-2024-12-31}
	@echo "✅ KPI Dashboard populated"

# Populate KPI Dashboard with CRM data
populate-kpi-real:
	@echo "📊 Populating KPI Dashboard with QuickBooks + CRM data..."
	@cd templates && ../$(PYTHON) populate_kpi_dashboard_v2.py --since $${SINCE:-2024-01-01} --until $${UNTIL:-2024-12-31} --crm $${CRM:-salesforce}
	@echo "✅ KPI Dashboard populated with real data"

# Populate Payroll Summary
populate-payroll:
	@echo "👥 Populating Payroll Summary..."
	@cd templates && ../$(PYTHON) populate_payroll_summary.py --since $${SINCE:-2024-01-01} --until $${UNTIL:-2024-12-31} --payroll $${PAYROLL:-gusto}
	@echo "✅ Payroll Summary populated"

# List available templates
list-templates:
	@echo "📋 Available Financial Templates:"
	@cd templates && ../$(PYTHON) template_manager.py list

# Test QuickBooks integration
test-qb-integration:
	@echo "🧪 Testing QuickBooks integration..."
	@cd integrations/quickbooks && ../../$(PYTHON) test_integration.py

# Test QuickBooks connection
test-qb-connection:
	@echo "🔌 Testing QuickBooks connection..."
	@cd integrations/quickbooks && ../../$(PYTHON) test_connection.py

# Register a new template
template-register:
	@echo "📝 Registering template..."
	@cd templates && ../$(PYTHON) register_template.py register --file $${FILE} --name $${NAME} --version $${VERSION}

# Validate a template
template-validate:
	@echo "🔍 Validating template..."
	@cd templates && ../$(PYTHON) register_template.py validate --file $${FILE}

# Populate 3-Statement with REAL QuickBooks data
populate-3statement-real:
	@echo "📊 Populating 3-Statement Model with QuickBooks data..."
	@cd templates && ../$(PYTHON) populate_3statement_v2.py --since $${SINCE:-2024-01-01} --until $${UNTIL:-2024-12-31}
	@echo "✅ 3-Statement Model populated with real data"

# Run scheduler
scheduler:
	@echo "🕐 Starting template scheduler..."
	@cd scheduler && ../$(PYTHON) template_scheduler.py run

# Run scheduler once for a template
scheduler-once:
	@echo "🔄 Running single template refresh..."
	@cd scheduler && ../$(PYTHON) template_scheduler.py once --template $${TEMPLATE:-3_statement_model}

# List scheduled templates
scheduler-list:
	@echo "📅 Listing scheduled templates..."
	@cd scheduler && ../$(PYTHON) template_scheduler.py list

# Test insight engine
test-insights:
	@echo "💡 Testing insight engine..."
	@cd insights && ../$(PYTHON) test_insights.py

# Test CRM connection
test-crm-connection:
	@echo "🔌 Testing CRM connection..."
	@cd integrations/crm && ../../$(PYTHON) -c "from client import create_crm_client, test_crm_connection; test_crm_connection('$${CRM:-salesforce}')"

# Test Payroll connection
test-payroll-connection:
	@echo "👥 Testing Payroll connection..."
	@cd integrations/payroll && ../../$(PYTHON) -c "from client import create_payroll_client, test_payroll_connection; test_payroll_connection('$${PAYROLL:-gusto}')"

# Test all integrations
test-integrations: test-qb-connection test-crm-connection test-payroll-connection
	@echo "✅ All integration tests complete"

# Metric store commands
ingest-metrics:
	@echo "📊 Ingesting metrics from Excel..."
	@cd metrics && ../$(PYTHON) -m ingest --workspace $${WORKSPACE:-demo} --file $${FILE}

test-metrics:
	@echo "🧪 Testing metric store..."
	@cd scripts && ../$(PYTHON) test_metrics.py

test-metrics-pytest:
	@echo "🧪 Running metric store unit tests..."
	@$(PYTHON) -m pytest tests/test_metrics.py -v

migrate-db:
	@echo "🗄️  Running database migrations..."
	@cd migrations && alembic upgrade head

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -f templates/finwave_board_pack_populated_*.xlsx
	@rm -f templates/3statement_populated_*.xlsx
	@rm -f templates/kpi_dashboard_populated_*.xlsx
	@rm -f templates/*.pyc
	@rm -rf templates/__pycache__
	@rm -rf templates/populated
	@rm -rf templates/logs
	@echo "✅ Cleaned"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

# Development setup with virtual environment
dev-setup:
	@echo "🔧 Setting up development environment..."
	@python3 -m venv $(VENV)
	@echo "✅ Virtual environment created"
	@echo "👉 Run: source $(VENV)/bin/activate && make install"

# Database and workspace management
init-db:
	@echo "🗄️  Initializing database..."
	@cd scripts && ../$(PYTHON) manage_workspace.py init-db

create-workspace:
	@echo "🏢 Creating workspace..."
	@cd scripts && ../$(PYTHON) manage_workspace.py create $${ID} "$${NAME}" \
		--billing-status $${STATUS:-trial} \
		--seats $${SEATS:-5} \
		--trial-days $${TRIAL:-14}

list-workspaces:
	@echo "📋 Listing workspaces..."
	@cd scripts && ../$(PYTHON) manage_workspace.py list

show-workspace:
	@echo "🔍 Showing workspace details..."
	@cd scripts && ../$(PYTHON) manage_workspace.py show $${ID}

delete-workspace:
	@echo "🗑️  Deleting workspace..."
	@cd scripts && ../$(PYTHON) manage_workspace.py delete $${ID} $${FORCE}

# Forecasting & Alerts
forecast:
	@echo "📈 Generating metric forecasts..."
	@$(PYTHON) scheduler/run_jobs.py forecast_update
	@echo "✅ Forecasts generated"

# Populate forecast drivers
populate-forecast-drivers:
	@echo "🎯 Populating forecast drivers..."
	@cd templates && ../$(PYTHON) populate_forecast_drivers.py --workspace $${WORKSPACE:-demo-corp} --since $${SINCE:-2024-01-01} --scenario $${SCENARIO:-base}
	@echo "✅ Forecast drivers populated"

# Check variance rules
variance:
	@echo "🚨 Checking variance rules..."
	@$(PYTHON) scheduler/run_jobs.py variance_check
	@echo "✅ Variance check complete"

# Run all scheduled jobs
scheduler-all:
	@echo "⏰ Running all scheduled jobs..."
	@$(PYTHON) scheduler/run_jobs.py all
	@echo "✅ All jobs complete"

# Development shortcuts
quick-setup:
	./scripts/dev_quick_setup.sh

demo-workspace:
	@$(PYTHON) scripts/seed_demo.py