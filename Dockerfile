FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (for building some py packages if needed)
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
# Filter out windows-specific dependencies for Docker (Linux)
# In a real scenario, we might have separate requirements. 
# Here we just sed them out or let pip ignore markers since we used markers.
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Initialize DB
RUN python -c "from core.logging_db import DatabaseManager; db = DatabaseManager(); db.init_db()"

EXPOSE 5000

CMD ["python", "api_app.py"]
