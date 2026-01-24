#!/bin/bash

# Quick Start Script for Deribit Price Tracker
# This script sets up the project for local development

set -e

echo "🚀 Deribit Price Tracker - Quick Start"
echo "========================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python --version
python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ ! "$python_version" > "3.10" ]]; then
    echo "❌ Python 3.11+ required"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "✓ Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your PostgreSQL and Redis credentials"
    echo "   nano .env"
    echo ""
fi

# Check PostgreSQL connection
echo "✓ Checking PostgreSQL connection..."
if ! python manage.py dbshell < /dev/null 2>/dev/null; then
    echo "⚠️  PostgreSQL not available. Please ensure:"
    echo "   - PostgreSQL is running"
    echo "   - Credentials in .env are correct"
    echo "   - Database exists: createdb deribit_db"
fi

# Run migrations
echo "✓ Running database migrations..."
python manage.py migrate

# Create superuser if needed
echo ""
echo "? Create Django superuser for admin panel?"
read -p "  (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo ""
echo "   Terminal 1 - Start Django development server:"
echo "     python manage.py runserver"
echo ""
echo "   Terminal 2 - Start Celery worker:"
echo "     celery -A config worker --loglevel=info"
echo ""
echo "   Terminal 3 - Start Celery Beat (scheduler):"
echo "     celery -A config beat --loglevel=info"
echo ""
echo "📍 Access points:"
echo "   - API: http://localhost:8000/api/prices/"
echo "   - Admin: http://localhost:8000/admin/"
echo ""
echo "📚 Documentation:"
echo "   - See README.md for detailed information"
echo "   - Examples: python examples.py"
echo ""
echo "🐳 Or use Docker:"
echo "   - docker-compose up -d"
echo ""
