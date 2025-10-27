#!/bin/bash

echo "═══════════════════════════════════════════════════════"
echo "  🌿 DERIC CONSISTENCY PLAN - AUTOMATED INSTALLER"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install requests streamlit plotly pandas

# Create requirements.txt
echo "requests>=2.28.0
streamlit>=1.28.0
plotly>=5.14.0
pandas>=2.0.0" > requirements.txt

echo "✅ Dependencies installed"
echo ""

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p images/teaching_leads
mkdir -p images/analytics_leads

echo "✅ Directories created"
echo ""

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "
from core import Database
db = Database()
print('✅ Database initialized')
db.close()
"

# Create config files if they don't exist
echo "⚙️  Setting up configuration..."
if [ ! -f "config.json" ]; then
    echo '{
  "name": "Deric Marangu",
  "phone": "+254791360805",
  "email": "dericmarangu@gmail.com",
  "links": {
    "DericBI": "https://dericBi.netlify.app",
    "Tujengane": "https://tujengane.netlify.app"
  },
  "branding": {
    "tone": "empowering",
    "style": "minimal",
    "primary_color": "#2e7d32",
    "language": "English"
  },
  "si_time": "13:00",
  "ai_api": {
    "provider": "openai",
    "api_key": "",
    "model": "gpt-4"
  }
}' > config.json
fi

if [ ! -f "tasks.json" ]; then
    echo '[
  "Post outreach message",
  "DM 10 leads",
  "Offer audit to SMEs",
  "Update WhatsApp group",
  "Post recap with proof"
]' > tasks.json
fi

echo "✅ Configuration complete"
echo ""

echo "═══════════════════════════════════════════════════════"
echo "  ✅ INSTALLATION COMPLETE!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Upload your images:"
echo "   • images/teaching_leads/day1.png to day7.png"
echo "   • images/analytics_leads/day1.png to day7.png"
echo ""
echo "2. Add your AI API key to config.json (optional)"
echo ""
echo "3. Run the system:"
echo "   • Manual: python3 core.py"
echo "   • Dashboard: streamlit run dashboard.py"
echo ""
echo "4. Set up auto-execution:"
echo "   • python3 auto_scheduler.py"
echo ""
echo "🌿 Your legacy engine is ready. Stay consistent!"