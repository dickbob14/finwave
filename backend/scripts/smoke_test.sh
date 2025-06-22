#!/bin/bash
# FinWave Smoke Test Suite
# Run this after setup to verify everything works

set -e

echo "🧪 FinWave Smoke Test Suite"
echo "=========================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run test and report result
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "Testing $test_name... "
    
    if eval $test_command > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  Error output:"
        tail -5 /tmp/test_output.log | sed 's/^/    /'
        return 1
    fi
}

# Check environment
echo "1️⃣ Environment Check"
echo "-------------------"

# Check for .env file
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
else
    echo -e "${RED}✗${NC} .env file missing - run ./scripts/secure_setup.sh"
    exit 1
fi

# Check for credentials
source .env
required_vars=("QB_CLIENT_ID" "QB_CLIENT_SECRET" "QB_COMPANY_ID")
all_set=true

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗${NC} $var not set"
        all_set=false
    else
        echo -e "${GREEN}✓${NC} $var is configured"
    fi
done

if [ "$all_set" = false ]; then
    echo ""
    echo "Please run ./scripts/secure_setup.sh to configure credentials"
    exit 1
fi

# Export environment
export $(grep -v '^#' .env | xargs)

echo ""
echo "2️⃣ Python Dependencies"
echo "---------------------"

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠${NC}  Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    
    # Try to activate it
    if [ -f venv/bin/activate ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓${NC} Activated virtual environment"
    fi
fi

# Check key packages
run_test "pandas" "python -c 'import pandas'"
run_test "openpyxl" "python -c 'import openpyxl'"
run_test "requests" "python -c 'import requests'"
run_test "yaml" "python -c 'import yaml'"

echo ""
echo "3️⃣ QuickBooks Integration"
echo "------------------------"

# Test connection
run_test "QB connection" "cd integrations/quickbooks && python test_connection.py"

# Test field mapper
run_test "field mapper" "cd config && python field_mapper.py"

# Test integration
run_test "QB integration tests" "cd integrations/quickbooks && python test_integration.py"

echo ""
echo "4️⃣ Template System"
echo "-----------------"

# Check template directory
if [ -d "templates/files" ]; then
    template_count=$(ls -1 templates/files/*.xlsx 2>/dev/null | wc -l)
    if [ $template_count -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $template_count template files"
    else
        echo -e "${YELLOW}⚠${NC}  No template files found"
        echo "   Run: python templates/setup_templates.py"
    fi
else
    echo -e "${RED}✗${NC} Template directory missing"
fi

# Test template validation
if [ -f "templates/files/Basic 3-Statement Model-2.xlsx" ]; then
    run_test "template validation" "cd templates && python register_template.py validate --file 'files/Basic 3-Statement Model-2.xlsx'"
fi

echo ""
echo "5️⃣ Data Population Test"
echo "----------------------"

# Try to populate with recent data
current_year=$(date +%Y)
current_month=$(date +%m)

# Calculate date range (last 3 months)
if [ $current_month -gt 3 ]; then
    start_month=$((current_month - 3))
    start_year=$current_year
else
    start_month=$((12 + current_month - 3))
    start_year=$((current_year - 1))
fi

start_date=$(printf "%04d-%02d-01" $start_year $start_month)
end_date=$(date +%Y-%m-%d)

echo "Testing data fetch for $start_date to $end_date"

# Test population (dry run - just fetch data)
if run_test "QB data fetch" "cd templates && python -c \"
from populate_3statement_v2 import ThreeStatementPopulator
p = ThreeStatementPopulator('files/Basic 3-Statement Model-2.xlsx')
data = p.fetch_quickbooks_data('$start_date', '$end_date')
print(f'Fetched {len(data.get(\"gl\", []))} GL entries')
\""; then
    echo -e "${GREEN}✓${NC} Successfully fetched QuickBooks data"
else
    echo -e "${YELLOW}⚠${NC}  No data found - trying previous year"
    # Try previous year
    start_date=$(printf "%04d-%02d-01" $((start_year - 1)) $start_month)
    end_date=$(printf "%04d-%02d-01" $((current_year - 1)) $current_month)
fi

echo ""
echo "6️⃣ API Endpoints"
echo "---------------"

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API server is running"
    
    # Test template endpoints
    run_test "template list" "curl -s http://localhost:8000/templates/"
    run_test "template health" "curl -s http://localhost:8000/templates/health"
else
    echo -e "${YELLOW}⚠${NC}  API server not running"
    echo "   Run: uvicorn app.main:app --reload"
fi

echo ""
echo "📊 Summary"
echo "---------"

# Final summary
echo ""
if [ -f templates/populated/3statement_populated_*.xlsx ]; then
    echo -e "${GREEN}✅ System is fully operational!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open populated Excel files to verify formulas"
    echo "2. Test the API: POST /templates/3statement/refresh"
    echo "3. Configure Google Sheets for live dashboards"
else
    echo -e "${YELLOW}⚠️  System is configured but no populated files yet${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: make populate-3statement-real SINCE=$start_date UNTIL=$end_date"
    echo "2. Check templates/populated/ for output files"
    echo "3. Review logs in templates/logs/ if issues occur"
fi

echo ""
echo "🔒 Security reminder:"
echo "   - Never commit .env or token files"
echo "   - Use 'git status' before every commit"
echo "   - Consider Doppler/AWS Secrets for production"

# Clean up
rm -f /tmp/test_output.log