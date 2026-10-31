# Isometric Trabzon — Açık Veriden Gerçek 3B Geometri (Pilot v0.1)

Trabzon Meydan çevresinin **gerçek OpenStreetMap bina izleri** ve yol verilerinden 3B, yakınlaştırılabilir izometrik haritası. Açık Mapzen Terrain Tiles verisinden **gerçek arazi yükseltileri** eklenir. Tamamen açık ve kaynak kodu düzenlenebilir.

**Durum:** Çalıştırılabilir ilk aşama. Model **fotoğraf gerçekliğinde değildir**: OSM'de yüksekliği bulunmayan binalar için 12 m varsayılır; renkler görsel amaçlıdır ve çatılar basitleştirilmiştir. Isometric Istanbul'un illüstratif karo/AI aşaması henüz yoktur.

## 1. Kurulum (Mac / Windows / Linux)

Python 3.10+ gerekli. Terminalde proje klasörüne girin:

```bash
cd isometric-trabzon
python3 -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/fetch_open_data.py
python -m http.server 8000
```

Tarayıcı: **http://localhost:8000**

İlk Python komutu OSM Overpass sunucularından canlı bina ve yol geometrisi indirir; ikincisi Mapzen AWS açık veri karolarından gerçek yükselti alır. İndirme internet bağlantısı ister. İlk denemede Overpass sunucuları yoğun olabilir; birkaç dakika sonra tekrar deneyin. Ek ücretli API anahtarı gerekmez.

Arazi servisine ulaşamıyorsanız `python scripts/fetch_open_data.py --no-terrain` ile düz zeminli sürümü oluşturabilirsiniz.

## 2. Görüntüleme

- Sol tuşla döndür, kaydırma tekeriyle yakınlaş, sağ tuşla taşı.
- **İzometrik açı** butonuyla kamerayı sıfırla.
- **PNG kaydet** ile mevcut görünümü kaydet.
- Binaya tıklayınca OSM kimliğini ve yükseklik verisinin gerçek/tahmini olduğunu gör.
- **GeoJSON dosyası aç** ile kullanıcı kaynaklı OSM/Overture GeoJSON içe aktar.

## 3. Coğrafi kapsam ve doğruluk

- BBOX `[39.725, 41.001, 39.737, 41.010]` sırası: **batı, güney, doğu, kuzey**.
- Koordinatların işlenmesi yerel metre ölçeğinde yapılıyor. Pilot alan için yeterli ama daha büyük Trabzon için **EPSG:32637 (UTM 37N)** dönüşümü kullanılmalı.
- OSM'de binaların bir kısmı bulunmayabilir; `building` *way* öğeleri indirilir, karmaşık multipolygon *relation* kayıtları bu pilotta yoktur.
- OSM yüksekliği varsa kullanılır (`height`); kat sayısı varsa 3,1m/kat + 1m kestirim yapılır, yoksa 12m görsel varsayım. Gerçek yüksekliğiymiş gibi değerlendirilmemelidir.
- Arazi Mapzen'ın birden fazla kaynağı birleştirdiği, kaynak doğruluğu bölgeye göre değişen yükseklik rasteridir. Sokak düzeyi hassas arazi ölçümü değildir.
- Çizilen yollar OSM merkez çizgilerinden yaklaşık genişlikte şeritlere dönüştürülür; ortofoto kadar hassas geometrileri yoktur.
- **Zemin dokusu:** lisanslı ve bu bbox'a tam hizalanmış görüntüyü `data/ortho.png` olarak yerleştirirseniz otomatik zemine kaplar. Bu sadece arazi/çatı üstten görüntüsünü temsil eder: bina cephelerine gerçek doku eklemek için eğik görüntü + kamera parametreleri veya dokulu 3B model gerekir.

## 4. Genişletme: Overture Maps

Bina izi yoğunluğunu artırmak için [Overture Maps CLI](https://docs.overturemaps.org/getting-data/overturemaps-py/):

```bash
pip install overturemaps
overturemaps download --bbox=39.725,41.001,39.737,41.010 -f geojson --type=building -o data/overture_buildings.geojson
```

Sonra arayüzde **GeoJSON dosyası aç** ile içe aktarabilirsiniz. Overture bina formatındaki `properties.height` ve `properties.num_floors` alanlarını bu sürümde okuyabiliriz; ancak Overture şemasının başka alanları ve bileşen ayrıntıları ayrıca kontrol edilmelidir. Yüklemeden önce veri kapsamı ayrıca doğrulanmalı. Aynı yerdeki OSM ve Overture yapılarını doğrudan üst üste koymayın: mükerrer binalar çıkar.

## 5. Sonraki teknik aşamalar

1. Bina poligon kalite kontrolü, OSM/Overture kapsama karşılaştırması; kaynak izlenebilirliği.
2. Hassas DEM (varsa), araziye oturan bina tabanı/çatı şekilleri.
3. Uygun lisanslı hava/eğik fotoğrafları ya da CityGML/tekstürlü mesh üzerinden **gerçek doku** üretimi.
4. Sabit ortografik kameradan örtüşmeli render karo sistemi.
5. Kaynak geometriyi bozmadan img2img/ControlNet tabanlı görsel stil oluşturma.
6. Yüksek çözünürlüklü karo piramidi, dağıtım (OpenSeadragon veya coğrafi imaj katmanı), mekan etiketi/arama.

Isometric Istanbul gibi stilize bir harita ile **fotogerçekçi şehir rekonstrüksiyonu** aynı şey değildir. Hazır açık Trabzon dokulu mesh verisi bulunmadan cepheleri birebir doğru yapmak mümkün değildir.

## 6. Veri lisansları / kaynaklar

- © OpenStreetMap katkıcıları — ODbL: https://www.openstreetmap.org/copyright
- Mapzen Terrain Tiles via AWS Open Data: https://registry.opendata.aws/terrain-tiles/
- Alttaki yükseklik veri kaynaklarının ayrı atıf koşulları: https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- Three.js (MIT): https://threejs.org/
- Overture Maps (alternatif veri): https://docs.overturemaps.org/getting-data/overturemaps-py/

Yüksek hacimli Overpass talepleri için servisin kullanım politikalarına uyun; tüm şehri tek sorguda indirmek yerine bölgelere ayırın.

## 7. Geliştirme testleri

```bash
python -m unittest discover -s tests -v
node --check src/app.js
```

## GitHub Pages

GitHub Actions iş akışı otomatik olarak açık OSM ve Mapzen verilerini indirip siteyi GitHub Pages'e dağıtır. Depo Settings → Pages → Source: GitHub Actions olarak ayarlanmalıdır. Private repo için uygun GitHub planı gereklidir.
