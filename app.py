import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

st.set_page_config(page_title="Altın Takip", page_icon="🪙", layout="wide")

DATA_FILE = "altin_kayitlari.json"

ALTIN_TURLERI = [
    "Gram Altın",
    "Çeyrek Altın",
    "Yarım Altın",
    "Tam Altın (Cumhuriyet)",
    "Ata Altın",
    "ONS (Ons)",
]

# Çeyrek = 1.75 gram, Yarım = 3.5 gram, Tam = 7 gram, Ata = 7 gram
GRAM_KATSAYI = {
    "Gram Altın": 1.0,
    "Çeyrek Altın": 1.75,
    "Yarım Altın": 3.5,
    "Tam Altın (Cumhuriyet)": 7.0,
    "Ata Altın": 7.0,
    "ONS (Ons)": 31.1035,
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@st.cache_data(ttl=60)
def get_gold_price():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://www.haremaltin.com/altin-fiyatlari", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # JSON data içinden fiyatı çek
        scripts = soup.find_all("script")
        for s in scripts:
            if s.string and "HAS" in s.string and "alis" in s.string.lower():
                txt = s.string
                idx = txt.find('"alis"')
                if idx != -1:
                    val = txt[idx+7:idx+20].split(",")[0].strip().replace('"','')
                    return float(val.replace(".","").replace(",","."))
    except:
        pass
    # Alternatif kaynak
    try:
        r = requests.get(
            "https://finance.altın.club/api/v1/price/gram",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8,
        )
        data = r.json()
        return float(data.get("buy") or data.get("price", 0))
    except:
        pass
    return None

@st.cache_data(ttl=60)
def get_gold_price_v2():
    """haremaltin.com'dan güncel gram altın alış fiyatı"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.haremaltin.com/",
        }
        r = requests.get(
            "https://www.haremaltin.com/api/altin-fiyatlari",
            headers=headers,
            timeout=10,
        )
        data = r.json()
        # HAS ALTIN alis fiyatı
        for item in data:
            if isinstance(item, dict):
                if item.get("kod") == "HAS" or item.get("name", "").upper() == "HAS ALTIN":
                    alis = item.get("alis") or item.get("buy")
                    return float(str(alis).replace(".", "").replace(",", "."))
    except:
        pass
    return None

def get_current_gram_price():
    price = get_gold_price_v2()
    if price and price > 1000:
        return price
    price = get_gold_price()
    if price and price > 1000:
        return price
    return None

def gram_degeri(tur, adet, gram_fiyat):
    return GRAM_KATSAYI.get(tur, 1.0) * adet * gram_fiyat

# ---------- UI ----------

st.title("🪙 Altın Takip Defteri")

col_price, col_refresh = st.columns([3, 1])
with col_price:
    gram_fiyat = get_current_gram_price()
    if gram_fiyat:
        st.metric("📡 Anlık Has Altın Alış (HaremalTın)", f"{gram_fiyat:,.2f} ₺ / gram")
    else:
        st.warning("⚠️ Anlık fiyat alınamadı. Lütfen manuel giriniz.")
        gram_fiyat = st.number_input("Gram Altın Alış Fiyatı (TL)", value=6600.0, step=10.0)

with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 Fiyatı Yenile"):
        st.cache_data.clear()
        st.rerun()

st.divider()

kayitlar = load_data()

# ---------- Yeni kayıt ekle ----------
with st.expander("➕ Yeni Altın Kaydı Ekle", expanded=len(kayitlar) == 0):
    c1, c2, c3 = st.columns(3)
    with c1:
        tarih = st.date_input("Tarih", value=datetime.today())
        kyk_kredi = st.number_input("KYK Kredi (TL)", value=8000, step=500)
        ekstra = st.number_input("Ekstra Eklenen Para (TL)", value=0, step=100)
    with c2:
        altin_turu = st.selectbox("Altın Türü", ALTIN_TURLERI)
        adet = st.number_input("Adet", min_value=0.5, step=0.5, value=1.0)
        alis_fiyati = st.number_input(
            "Alış Fiyatı (TL) — gram başına",
            value=float(int(gram_fiyat)) if gram_fiyat else 6600.0,
            step=10.0,
        )
    with c3:
        toplam_odenen = alis_fiyati * GRAM_KATSAYI.get(altin_turu, 1.0) * adet
        st.metric("Toplam Ödenen", f"{toplam_odenen:,.0f} ₺")
        kalan = kyk_kredi + ekstra - toplam_odenen
        st.metric("Kalan Para", f"{kalan:,.0f} ₺", delta_color="normal")
        not_alani = st.text_input("Not (opsiyonel)", "")

    if st.button("✅ Kaydet", type="primary"):
        yeni = {
            "id": len(kayitlar) + 1,
            "tarih": str(tarih),
            "altin_turu": altin_turu,
            "adet": adet,
            "alis_fiyati_gram": alis_fiyati,
            "toplam_odenen": round(toplam_odenen, 2),
            "kyk_kredi": kyk_kredi,
            "ekstra": ekstra,
            "kalan": round(kalan, 2),
            "not": not_alani,
        }
        kayitlar.append(yeni)
        save_data(kayitlar)
        st.success("Kayıt eklendi!")
        st.rerun()

st.divider()

# ---------- Portföy özeti ----------
if kayitlar and gram_fiyat:
    st.subheader("📊 Portföy Özeti")

    toplam_maliyet = sum(k["toplam_odenen"] for k in kayitlar)
    toplam_kyk = sum(k["kyk_kredi"] for k in kayitlar)
    toplam_ekstra = sum(k.get("ekstra", 0) for k in kayitlar)

    # Anlık değer hesapla
    toplam_anlik = 0.0
    tur_bazinda = {}
    for k in kayitlar:
        deger = gram_degeri(k["altin_turu"], k["adet"], gram_fiyat)
        toplam_anlik += deger
        tur = k["altin_turu"]
        if tur not in tur_bazinda:
            tur_bazinda[tur] = {"adet": 0, "maliyet": 0, "anlik": 0}
        tur_bazinda[tur]["adet"] += k["adet"]
        tur_bazinda[tur]["maliyet"] += k["toplam_odenen"]
        tur_bazinda[tur]["anlik"] += deger

    kar_zarar = toplam_anlik - toplam_maliyet
    kar_zarar_pct = (kar_zarar / toplam_maliyet * 100) if toplam_maliyet else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("💰 Toplam Maliyet", f"{toplam_maliyet:,.0f} ₺")
    m2.metric("📈 Anlık Değer", f"{toplam_anlik:,.0f} ₺")
    m3.metric(
        "📊 Kâr / Zarar",
        f"{kar_zarar:+,.0f} ₺",
        delta=f"%{kar_zarar_pct:+.1f}",
        delta_color="normal",
    )
    m4.metric("🏦 Toplam KYK", f"{toplam_kyk:,.0f} ₺")
    m5.metric("➕ Toplam Ekstra", f"{toplam_ekstra:,.0f} ₺")

    # Tür bazında tablo
    st.subheader("Altın Türü Bazında")
    rows = []
    for tur, v in tur_bazinda.items():
        kz = v["anlik"] - v["maliyet"]
        rows.append({
            "Altın Türü": tur,
            "Adet": v["adet"],
            "Gram Karşılığı": round(GRAM_KATSAYI.get(tur, 1.0) * v["adet"], 3),
            "Maliyet (₺)": f"{v['maliyet']:,.0f}",
            "Anlık Değer (₺)": f"{v['anlik']:,.0f}",
            "Kâr/Zarar (₺)": f"{kz:+,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.divider()

# ---------- Kayıtlar tablosu ----------
st.subheader("📋 Tüm Kayıtlar")

if not kayitlar:
    st.info("Henüz kayıt yok. Yukarıdan ekleyebilirsiniz.")
else:
    df_rows = []
    for k in kayitlar:
        anlik = gram_degeri(k["altin_turu"], k["adet"], gram_fiyat) if gram_fiyat else None
        kz = (anlik - k["toplam_odenen"]) if anlik else None
        df_rows.append({
            "#": k["id"],
            "Tarih": k["tarih"],
            "Altın Türü": k["altin_turu"],
            "Adet": k["adet"],
            "Gram Alış (₺)": f"{k['alis_fiyati_gram']:,.0f}",
            "Toplam Ödenen (₺)": f"{k['toplam_odenen']:,.0f}",
            "Anlık Değer (₺)": f"{anlik:,.0f}" if anlik else "—",
            "K/Z (₺)": f"{kz:+,.0f}" if kz is not None else "—",
            "KYK (₺)": f"{k['kyk_kredi']:,.0f}",
            "Ekstra (₺)": f"{k.get('ekstra',0):,.0f}",
            "Kalan (₺)": f"{k.get('kalan',0):,.0f}",
            "Not": k.get("not", ""),
        })

    df = pd.DataFrame(df_rows)
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Sil
    with st.expander("🗑️ Kayıt Sil"):
        sil_id = st.number_input("Silmek istediğin kayıt #", min_value=1, max_value=len(kayitlar), step=1)
        if st.button("Sil", type="secondary"):
            kayitlar = [k for k in kayitlar if k["id"] != sil_id]
            # ID'leri yeniden numaralandır
            for i, k in enumerate(kayitlar):
                k["id"] = i + 1
            save_data(kayitlar)
            st.success("Silindi.")
            st.rerun()

    # Export
    st.divider()
    df_export = pd.DataFrame([{
        "Tarih": k["tarih"],
        "Altın Türü": k["altin_turu"],
        "Adet": k["adet"],
        "Gram Alış Fiyatı (TL)": k["alis_fiyati_gram"],
        "Toplam Ödenen (TL)": k["toplam_odenen"],
        "KYK Kredi (TL)": k["kyk_kredi"],
        "Ekstra (TL)": k.get("ekstra", 0),
        "Kalan (TL)": k.get("kalan", 0),
        "Not": k.get("not", ""),
    } for k in kayitlar])

    st.download_button(
        "⬇️ Excel olarak indir",
        data=df_export.to_csv(index=False).encode("utf-8-sig"),
        file_name="altin_kayitlari.csv",
        mime="text/csv",
    )

st.caption("Fiyat kaynağı: haremaltin.com — Her 60 saniyede bir yenilenir.")
