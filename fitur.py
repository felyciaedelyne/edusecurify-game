"""Normalisasi teks + ciri tautan untuk model phishing media sosial.

Dipakai SAMA PERSIS oleh training (train_medsos.py / Train_Medsos.ipynb) dan server.py.
Tidak memakai stemmer: bahasa medsos penuh singkatan/gaul, dan tanpa stemmer server lebih ringan.

Ide utama: setiap tautan diganti token "zurl", lalu ciri-cirinya (domain murah, shortener,
http, tanda hubung, kata "login/verif" di domain, file .apk, domain resmi .ac.id/.go.id)
ditambahkan sebagai token "z..." di akhir teks, sehingga TF-IDF otomatis ikut mempelajarinya.
"""
import re
from urllib.parse import urlparse

URL_RE = re.compile(
    r"(?:https?://|www\.|bit\.ly/|tinyurl\.com/|s\.id/|t\.co/|cutt\.ly/|rb\.gy/|wa\.me/)\S+",
    re.IGNORECASE,
)
SHORTENERS = ("bit.ly", "tinyurl.com", "s.id", "t.co", "cutt.ly", "is.gd", "rb.gy", "shorturl.at")
RISKY_TLD = (".xyz", ".top", ".click", ".tk", ".site", ".icu", ".online", ".buzz", ".cc",
             ".live", ".shop", ".link", ".monster", ".cfd", ".sbs", ".info", ".vip")
OFFICIAL_TLD = (".ac.id", ".go.id", ".sch.id", ".edu", ".gov", ".mil.id")
KW_DOMAIN = ("login", "verif", "secure", "akun", "klaim", "claim", "hadiah", "bantuan", "update",
             "cek", "bayar", "promo", "gift", "reward", "konfirmasi", "resmi", "aman", "official")


def ciri_url(u):
    """Daftar token ciri untuk satu tautan."""
    u = u.strip().rstrip(".,!?)\"'")
    ada_skema = bool(re.match(r"https?://", u, re.IGNORECASE))
    parsed = urlparse(u if ada_skema else "http://" + u)
    host = (parsed.netloc or "").lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    path = (parsed.path or "").lower() + ("?" + parsed.query.lower() if parsed.query else "")

    tok = []
    if ada_skema:
        tok.append("zhttps" if u.lower().startswith("https") else "zhttp")
    if host in SHORTENERS:
        tok.append("zshort")
    if host.endswith(OFFICIAL_TLD):
        tok.append("ztldresmi")
    elif host.endswith(RISKY_TLD):
        tok.append("ztldmurah")
    else:
        tok.append("ztldbiasa")
    if host.count("-") >= 1:
        tok.append("zhyphen")
    if host.count("-") >= 2:
        tok.append("zhyphen2")
    if any(k in host for k in KW_DOMAIN):
        tok.append("zkwhost")
    if any(k in path for k in KW_DOMAIN):
        tok.append("zkwpath")
    if path.endswith(".apk"):
        tok.append("zapk")
    if re.search(r"\d", host.split(".")[0]):
        tok.append("zdigithost")
    return tok


def normalisasi(teks):
    teks = str(teks)
    tokens = []

    def ganti(m):
        tokens.extend(ciri_url(m.group(0)))
        return " zurl "

    t = URL_RE.sub(ganti, teks)
    t = t.lower()
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)                         # selamaaat -> selamaat
    t = re.sub(r"\b(kode|otp|pin|token|verifikasi)\W{0,3}\d{4,6}\b", " zkode ", t)
    t = re.sub(r"\b\d{10,}\b", " znomor ", t)                    # nomor rekening / HP panjang
    t = re.sub(r"\brp\.?\s?\d[\d.,]*", " zrupiah ", t)
    t = re.sub(r"!{2,}", " zseru ", t)
    t = re.sub(r"[^\w\s]", " ", t)                               # buang tanda baca & emoji
    t = re.sub(r"\s+", " ", t).strip()

    ciri = list(tokens)
    if not tokens:
        ciri.append("ztanpalink")
    elif len([c for c in tokens if c.startswith("ztld")]) >= 2:
        ciri.append("zbanyaklink")
    return (t + " " + " ".join(ciri)).strip()


def normalisasi_batch(teks_list):
    return [normalisasi(x) for x in teks_list]
