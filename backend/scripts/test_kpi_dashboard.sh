#!/bin/bash
# Test KPI Dashboard with CRM integration

echo "🧪 Testing KPI Dashboard Integration"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run: make dev-setup"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for CRM credentials
echo -e "\n1️⃣ Checking CRM configuration..."
CRM_TYPE=${CRM_TYPE:-salesforce}
echo "   CRM Type: $CRM_TYPE"

if [ "$CRM_TYPE" = "salesforce" ]; then
    if [ -z "$SF_ACCESS_TOKEN" ]; then
        echo "   ⚠️  Salesforce credentials not found"
        echo "   📝 Using sample data mode"
    else
        echo "   ✅ Salesforce credentials found"
    fi
else
    if [ -z "$HUBSPOT_ACCESS_TOKEN" ]; then
        echo "   ⚠️  HubSpot credentials not found"
        echo "   📝 Using sample data mode"
    else
        echo "   ✅ HubSpot credentials found"
    fi
fi

# Test CRM connection
echo -e "\n2️⃣ Testing CRM connection..."
cd integrations/crm && python test_crm.py $CRM_TYPE
cd ../..

# Test field mappings
echo -e "\n3️⃣ Validating field mappings..."
python -c "
from config.field_mapper import FieldMapper
mapper = FieldMapper('config/field_maps/crm.yml')
print('   ✅ CRM field mappings loaded')
"

# Check if template exists
echo -e "\n4️⃣ Checking KPI Dashboard template..."
TEMPLATE_PATH="assets/templates/registered/Cube - KPI Dashboard.xlsx"
if [ -f "$TEMPLATE_PATH" ]; then
    echo "   ✅ Template found: $TEMPLATE_PATH"
else
    echo "   ❌ Template not found at: $TEMPLATE_PATH"
    echo "   Run: make template-register FILE='path/to/template' NAME='Cube - KPI Dashboard'"
    exit 1
fi

# Test populate command
echo -e "\n5️⃣ Testing KPI Dashboard population..."
echo "   Running: make populate-kpi-real"

# Set date range
export SINCE="2024-01-01"
export UNTIL="2024-12-31"

# Run population
cd templates
../venv/bin/python populate_kpi_dashboard_v2.py \
    --since $SINCE \
    --until $UNTIL \
    --crm $CRM_TYPE \
    --debug

RESULT=$?
cd ..

if [ $RESULT -eq 0 ]; then
    echo -e "\n✅ KPI Dashboard populated successfully!"
    
    # Check for output file
    OUTPUT_FILE=$(ls -t templates/populated/kpi_dashboard_populated_*.xlsx 2>/dev/null | head -1)
    if [ -n "$OUTPUT_FILE" ]; then
        echo "   📊 Output file: $OUTPUT_FILE"
        echo "   📏 File size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
    fi
else
    echo -e "\n❌ KPI Dashboard population failed"
    exit 1
fi

# Test API endpoints
echo -e "\n6️⃣ Testing CRM API endpoints..."
if curl -s http://localhost:8000/crm/status > /dev/null 2>&1; then
    echo "   Testing /crm/status..."
    curl -s http://localhost:8000/crm/status | python -m json.tool | head -10
    
    echo -e "\n   Testing /crm/metrics..."
    curl -s http://localhost:8000/crm/metrics | python -m json.tool | head -10
else
    echo "   ⚠️  API server not running. Start with: make server"
fi

echo -e "\n✨ KPI Dashboard integration test complete!"
echo ""
echo "Next steps:"
echo "1. Start the API server: make server"
echo "2. Test in browser: http://localhost:3000/templates"
echo "3. View CRM metrics: http://localhost:8000/crm/metrics"
echo "4. Schedule regular updates: make scheduler"