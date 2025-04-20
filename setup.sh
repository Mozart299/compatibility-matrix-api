#!/bin/bash
# setup.sh - Setup script for Compatibility Matrix API

# Exit on error
set -e

# Display ASCII art banner
echo "========================================================"
echo "  _____                            _   _ _     _ _ _ _         "
echo " / ____|                          | | (_) |   (_) (_) |        "
echo "| |     ___  _ __ ___  _ __   __ _| |_ _| |__  _| |_| |_ _   _ "
echo "| |    / _ \| '_ \` _ \| '_ \ / _\` | __| | '_ \| | | | __| | | |"
echo "| |___| (_) | | | | | | |_) | (_| | |_| | |_) | | | | |_| |_| |"
echo " \_____\___/|_| |_| |_| .__/ \__,_|\__|_|_.__/|_|_|_|\__|\__, |"
echo "                       | |                                 __/ |"
echo " __  __       _        |_|      _    ____ ___            |___/ "
echo "|  \/  | __ _| |_ _ __ (_)_  __    / \  |  _ \_ __            "
echo "| |\/| |/ _\` | __| '__| \ \/ /   / _ \ | |_) | '__|           "
echo "| |  | | (_| | |_| |  | |>  <   / ___ \|  __/| |              "
echo "|_|  |_|\__,_|\__|_|  |_/_/\_\ /_/   \_\_|   |_|              "
echo "                                                               "
echo "========================================================"
echo "Setting up Compatibility Matrix API development environment"
echo "========================================================"

# Check for Python 3.10+
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.10 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "Python 3.10 or later is required. Found $PYTHON_VERSION."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️ PostgreSQL is not installed or not in PATH."
    echo "Please install PostgreSQL and make sure it's running before starting the application."
else
    echo "✅ PostgreSQL detected"
    
    # Check if the database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw compatibility_matrix; then
        echo "✅ Database 'compatibility_matrix' already exists"
    else
        echo "Creating database 'compatibility_matrix'..."
        createdb compatibility_matrix
        echo "✅ Database created"
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.sample .env
    
    # Generate random secret keys
    JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    REFRESH_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update secret keys in .env
    sed -i'.bak' "s/JWT_SECRET_KEY=your_jwt_secret_key_here/JWT_SECRET_KEY=$JWT_SECRET/g" .env
    sed -i'.bak' "s/JWT_REFRESH_SECRET_KEY=your_refresh_token_secret_key_here/JWT_REFRESH_SECRET_KEY=$REFRESH_SECRET/g" .env
    
    # Remove backup file
    rm -f .env.bak
    
    echo "✅ .env file created with secure random keys"
else
    echo "✅ .env file already exists"
fi

echo "========================================================"
echo "Setup completed successfully! 🎉"
echo ""
echo "To start the application, run:"
echo "    source venv/bin/activate  # If not already activated"
echo "    uvicorn app.main:app --reload"
echo ""
echo "The API will be available at: http://localhost:8000"
echo "API documentation will be at: http://localhost:8000/docs"
echo "========================================================"