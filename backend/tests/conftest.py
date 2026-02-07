# 1. Fixture dla testowej bazy danych (SQLite in-memory)
# 2. Fixture dla TestClient (FastAPI client)
# 3. Fixtures dla użytkowników (admin, user, viewer, inactive)
# 4. Fixtures dla JWT tokenów
# 5. Fixtures dla HTTP headers z tokenami

import sys
from pathlib import Path

# Dodaj backend do ścieżki Pythona
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))