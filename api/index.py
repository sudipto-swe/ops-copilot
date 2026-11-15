import os
import sys

# Ensure repository root is in python path for serverless imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.app.main import app
