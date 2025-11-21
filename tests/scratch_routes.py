# scratch_routes.py
from api.main import app

for route in app.routes:
    print(route.path, route.methods)
