"""EduSecurity server: melayani game (folder public/) + API model phishing.

Jalankan lokal : python server.py
Produksi       : gunicorn server:app --workers 2 --threads 4 --timeout 60
"""
import json
import os
import threading
from datetime import datetime, timezone

import joblib
from flask import Flask, jsonify, request, send_from_directory

import fitur  # noqa: F401  (dibutuhkan saat memuat model: normalisasi_batch ada di fitur.py)

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(BASE, "public")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE, "data"))
LOG_FILE = os.path.join(DATA_DIR, "records.jsonl")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")  # isi di hosting agar /export aman
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, static_folder=PUBLIC, static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # batasi ukuran request

# ---- model gaya media sosial (dilatih lewat train_medsos.py / Train_Medsos.ipynb) ----
# Pipeline sudah memuat normalisasi teks + TF-IDF + Logistic Regression.
model = joblib.load(os.path.join(BASE, "model_medsos.joblib"))


# ---- routes ----
@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/predict")
def predict():
    data = request.get_json(silent=True) or {}
    teks = str(data.get("text", ""))[:1000]
    if not teks.strip():
        return jsonify(error="text kosong"), 400
    prob = float(model.predict_proba([teks])[0][1])
    return jsonify(phish_prob=prob)


_lock = threading.Lock()


@app.post("/log")
def log():
    """Simpan jawaban/tweet pemain untuk analisis PkM."""
    rec = request.get_json(silent=True)
    if not isinstance(rec, dict):
        return jsonify(error="bad request"), 400
    rec["server_time"] = datetime.now(timezone.utc).isoformat()
    with _lock, open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return jsonify(ok=True)


@app.get("/export")
def export():
    """Unduh semua catatan: /export?token=ADMIN_TOKEN"""
    if not ADMIN_TOKEN or request.args.get("token") != ADMIN_TOKEN:
        return jsonify(error="forbidden"), 403
    if not os.path.exists(LOG_FILE):
        return "", 204
    with open(LOG_FILE, encoding="utf-8") as f:
        return app.response_class(f.read(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
