/* ==========================================================
   HOOK MODEL ML (versi terhubung ke server.py)
   - predict : memanggil POST /predict (model dari Data_Prep.ipynb)
               jika server tidak terjangkau, otomatis pakai heuristik.
   - onAnswer / onTweet : mengirim catatan ke POST /log.
   Semua data juga tersimpan di EduSecurity.records / getData().
   ========================================================== */
async function heuristicPredict(text){
  const s = text.toLowerCase();
  const links = s.split(/\s+/).filter(w=>w.startsWith("http")||w.startsWith("www.")||w.startsWith("bit.ly"));
  let z = -1.2;
  if(links.length) z += 0.8;
  links.forEach(l=>{
    if([".xyz",".top",".click",".tk",".site",".icu",".online"].some(x=>l.includes(x))) z += 1.6;
    if(["bit.ly","tinyurl","s.id"].some(x=>l.includes(x))) z += 1.0;
    if(["login","verif","secure","akun","klaim","claim","hadiah"].some(x=>l.includes(x))) z += 0.9;
    if([".ac.id",".go.id",".edu",".gov"].some(x=>l.includes(x))) z -= 2;
    if(l.startsWith("http://")) z += 0.4;
  });
  ["otp","pin","kata sandi","password","verifikasi","segera","blokir","dibekukan","hadiah","klaim","pemenang","undian","selamat","ktp","data kartu","login","transfer","gaji","24 jam","1 jam","menit"].forEach(w=>{ if(s.includes(w)) z += 0.55; });
  ["terima kasih","makasih","kuliah","tugas","seminar","gratis"," ya"].forEach(w=>{ if(s.includes(w)) z -= 0.35; });
  if(s.includes("!!")) z += 0.4;
  return 1/(1+Math.exp(-z));
}

window.EduSecurity = {
  records: [],
  onAnswer: null,
  onTweet: null,
  predict: heuristicPredict,
  getData(){ return JSON.parse(JSON.stringify(this.records)); }
};

/* ---------- koneksi ke server ---------- */
const API_BASE = "";   // kosong = server yang sama (game & API satu alamat)
const ON_SERVER = location.protocol.startsWith("http");  // false jika index.html dibuka dari file://

// ID anonim per perangkat (tanpa data pribadi) agar jawaban satu anak bisa dikelompokkan
let PLAYER_ID = "anon";
try{
  PLAYER_ID = localStorage.getItem("edu_pid") || ("p" + Math.random().toString(36).slice(2, 8));
  localStorage.setItem("edu_pid", PLAYER_ID);
}catch(e){}

function withTimeout(promise, ms){
  return Promise.race([promise, new Promise((_, rej)=>setTimeout(()=>rej(new Error("timeout")), ms))]);
}

if(ON_SERVER){
  EduSecurity.predict = async (text, meta) => {
    try{
      const res = await withTimeout(fetch(API_BASE + "/predict", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({text, ...meta})
      }), 8000);
      if(!res.ok) throw new Error("HTTP " + res.status);
      const out = await res.json();
      if(typeof out.phish_prob !== "number") throw new Error("respons tidak valid");
      return out.phish_prob;
    }catch(e){
      console.warn("API model tidak terjangkau, pakai heuristik:", e);
      return heuristicPredict(text);
    }
  };

  const kirim = (rec) => {
    try{
      fetch(API_BASE + "/log", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({...rec, playerId: PLAYER_ID}),
        keepalive: true
      }).catch(()=>{});
    }catch(e){}
  };
  EduSecurity.onAnswer = kirim;
  EduSecurity.onTweet  = kirim;
}
