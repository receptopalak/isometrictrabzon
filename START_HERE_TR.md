# İlk Çalıştırma — Trabzon Meydan

## Mac'te en kısa yol

1. ZIP dosyasını aç.
2. Terminal'i açıp `cd` komutundan sonra ZIP'ten çıkan `isometric-trabzon` klasörünü Terminal'e sürükle ve Enter'a bas.
3. `./run_mac.command` çalıştır.
4. Tarayıcıda `http://localhost:8000` adresini aç.

İlk çalışmada internet üzerinden OSM bina yolları ve Mapzen arazi yüksekliği indirilir. İndirme gecikirse veya başarısız olursa Terminal'deki hata mesajını paylaş; birlikte kaynağı/dosyayı kontrol edebiliriz. Kaynak dosyaları **gerçek veri inmeden dolmaz**, sahte bina yok.

## Adım adım

```bash
cd isometric-trabzon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_open_data.py
python -m http.server 8000
```

Sonraki aşamada: OSM/Overture doğruluk analizi, gerçek çatı ve cephe fotoğraflarına uygun açık veri arama, fotogerçekçi 3B/dokulu model, izometrik PNG karo üretimi.