"""
Run the Flask API server

Usage:
    python backend/run_api.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api import app

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" DATA SEANCE - Ethics Compliance API")
    print("="*60)
    print(f" Server: http://localhost:5000")
    print(f" Health: http://localhost:5000/api/health")
    print(f" Analyze: POST http://localhost:5000/api/analyze")
    print("="*60 + "\n")
    print(" Ready to analyze files from frontend!")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')