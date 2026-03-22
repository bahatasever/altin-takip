# 🪙 Altın Takip Uygulaması

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

```bash
streamlit run app.py
```

Tarayıcın otomatik açılır: http://localhost:8501

## Google Colab'da kullanmak için

1. Google Colab'da yeni notebook aç
2. Aşağıdaki hücreyi çalıştır:

```python
!pip install streamlit requests beautifulsoup4 pyngrok -q

# app.py dosyasını yükle (Files > Upload)

from pyngrok import ngrok
import subprocess, threading, time

def run_streamlit():
    subprocess.run(["streamlit", "run", "app.py", "--server.port=8501"])

t = threading.Thread(target=run_streamlit)
t.daemon = True
t.start()
time.sleep(4)

tunnel = ngrok.connect(8501)
print("🌐 URL:", tunnel.public_url)
```

## Özellikler

- **Kayıt Ekleme**: Her ay aldığın altını tarih, tür, adet ve alış fiyatıyla gir
- **Desteklenen Türler**: Gram, Çeyrek, Yarım, Tam, Ata, ONS
- **Anlık Fiyat**: haremaltin.com'dan 60 saniyede bir güncellenir (ALIŞ fiyatı)
- **Kâr/Zarar**: Her kayıt ve toplam portföy için anlık hesaplama
- **Veri Saklama**: `altin_kayitlari.json` dosyasında saklanır
- **Excel Export**: CSV olarak indir butonu

## Notlar

- Veriler `altin_kayitlari.json` dosyasında saklanır
- Gram katsayıları: Çeyrek=1.75g, Yarım=3.5g, Tam=7g, ONS=31.1g
- Fiyat otomatik gelmezse manuel giriş yapabilirsin
