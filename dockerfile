# 1. Basis-Image wählen: Wir nehmen ein offizielles, schlankes Python 3.12 Image
FROM python:3.12-slim

# 2. Arbeitsverzeichnis im Container festlegen
WORKDIR /app

# 3. Die requirements.txt in den Container kopieren
COPY requirements.txt .

# 4. Die Python-Pakete im Container installieren
RUN pip install --no-cache-dir -r requirements.txt

# 5. Den kompletten Code aus unserem lokalen Projekt in den Container kopieren
COPY . .

# 6. Dem Container sagen, welchen Befehl er beim Starten ausführen soll
# Wichtig: Wir lauschen auf Port 8000 und erlauben Verbindungen von außen (0.0.0.0)
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]