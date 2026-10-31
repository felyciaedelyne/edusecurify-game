"""Melatih model phishing gaya media sosial dan menyimpan model_medsos.joblib.

Evaluasi jujur dua lapis:
  1. GroupKFold per template: template yang sama tidak boleh muncul di train DAN validasi.
  2. Soal di game (data/game_items.csv) TIDAK ikut dilatih, dipakai sebagai uji akhir.

Jalankan: python train_medsos.py
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from fitur import normalisasi_batch

BASE = os.path.dirname(os.path.abspath(__file__))


def buat_pipeline(C=3.0):
    return Pipeline([
        ("norm", FunctionTransformer(normalisasi_batch, validate=False)),
        ("tfidf", FeatureUnion([
            ("kata", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)),
        ])),
        ("clf", LogisticRegression(C=C, class_weight="balanced", max_iter=3000)),
    ])


def cv_group(df, C, k=5):
    skor_acc, skor_f1 = [], []
    for tr, va in GroupKFold(n_splits=k).split(df["teks"], df["label"], df["grup"]):
        m = buat_pipeline(C).fit(df["teks"].iloc[tr], df["label"].iloc[tr])
        p = m.predict(df["teks"].iloc[va])
        skor_acc.append(accuracy_score(df["label"].iloc[va], p))
        skor_f1.append(f1_score(df["label"].iloc[va], p))
    return np.mean(skor_acc), np.mean(skor_f1)


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(BASE, "data", "dataset_medsos.csv"))
    game = pd.read_csv(os.path.join(BASE, "data", "game_items.csv"))
    print(f"Latih: {len(df)} contoh ({df['label'].sum()} phishing) | Uji game: {len(game)} soal")

    print("\nGroupKFold (5 lipatan, per template):")
    terbaik = None
    for C in (0.3, 1, 3, 10, 30):
        acc, f1 = cv_group(df, C)
        print(f"  C={C:<5} akurasi={acc:.3f}  F1 phishing={f1:.3f}")
        if terbaik is None or f1 > terbaik[1]:
            terbaik = (C, f1)
    C = terbaik[0]
    print(f"-> dipilih C={C}")

    model = buat_pipeline(C).fit(df["teks"], df["label"])
    pred = model.predict(game["teks"])
    prob = model.predict_proba(game["teks"])[:, 1]
    print(f"\nUji pada soal game (tidak ikut dilatih): akurasi={accuracy_score(game['label'], pred):.3f}")
    print(classification_report(game["label"], pred, target_names=["Normal", "Phishing"], zero_division=0))
    salah = game.assign(prediksi=pred, prob_phishing=prob.round(2))
    salah = salah[salah["label"] != salah["prediksi"]]
    if len(salah):
        print("Soal yang salah ditebak:")
        for _, r in salah.iterrows():
            print(f"  [{r['id']}] benar={r['label']} prob={r['prob_phishing']} :: {r['teks'][:90]}")

    out = os.path.join(BASE, "model_medsos.joblib")
    joblib.dump(model, out, compress=3)
    print(f"\nTersimpan: {out} ({os.path.getsize(out) / 1024:.0f} KB)")
