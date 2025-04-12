# tests/conftest.py
import sys
import os
from api.services.content_distributor.dispatcher import dispatch_content


# Ajoute la racine du projet au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
