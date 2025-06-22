#!/bin/bash
# Secure setup script for FinWave
# Ensures credentials are properly configured without exposing them

set -e

echo "🔐 FinWave Secure Setup"
echo "======================"

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Copy example if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example"
    cp .env.example .env
fi

# Function to safely prompt for secrets
read_secret() {
    local var_name=$1
    local prompt=$2
    local current_value=$(grep "^$var_name=" .env | cut -d'=' -f2)
    
    if [ -n "$current_value" ] && [ "$current_value" != "your_${var_name,,}_here" ]; then
        echo "✓ $var_name is already set"
    else
        echo -n "$prompt: "
        read -s value
        echo
        sed -i.bak "s|^$var_name=.*|$var_name=$value|" .env
    fi
}

echo ""
echo "📝 Setting up QuickBooks credentials"
echo "-----------------------------------"
read_secret "QB_CLIENT_ID" "Enter QuickBooks Client ID"
read_secret "QB_CLIENT_SECRET" "Enter QuickBooks Client Secret"
read_secret "QB_COMPANY_ID" "Enter QuickBooks Company ID"

echo ""
echo "🔑 Optional: OAuth tokens"
echo "------------------------"
echo "If you have a refresh token, enter it. Otherwise press Enter to skip."
read_secret "QB_REFRESH_TOKEN" "Enter QuickBooks Refresh Token (optional)"

echo ""
echo "☁️  Optional: AWS S3 Configuration"
echo "---------------------------------"
read -p "Configure S3? (y/N): " configure_s3
if [[ $configure_s3 =~ ^[Yy]$ ]]; then
    read_secret "AWS_ACCESS_KEY_ID" "Enter AWS Access Key ID"
    read_secret "AWS_SECRET_ACCESS_KEY" "Enter AWS Secret Access Key"
    read_secret "FINWAVE_S3_BUCKET" "Enter S3 Bucket Name"
fi

echo ""
echo "📊 Optional: Google Sheets Configuration"
echo "---------------------------------------"
read -p "Configure Google Sheets? (y/N): " configure_gs
if [[ $configure_gs =~ ^[Yy]$ ]]; then
    echo "Place your service account JSON file in the credentials/ directory"
    echo "Then update GOOGLE_SHEETS_JSON in .env with the path"
fi

# Clean up backup files
rm -f .env.bak

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔒 Security checklist:"
echo "   - .env is in .gitignore ✓"
echo "   - Never commit .env file"
echo "   - Use 'git status' to verify .env is not staged"
echo "   - Consider using Doppler or AWS Secrets Manager for production"
echo ""
echo "🚀 Next steps:"
echo "   1. source venv/bin/activate"
echo "   2. export \$(grep -v '^#' .env | xargs)"
echo "   3. make test-qb-connection"