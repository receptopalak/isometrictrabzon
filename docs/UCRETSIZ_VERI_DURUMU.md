# Isometric Trabzon — ücretsiz veri doğrulaması (31 Ekim 2026)

## Kabul kriteri

Hedef: Isometric Istanbul benzeri, **gerçek bina çatı/cephe dokularına** sahip, koordinatları doğru izometrik şehir. Varsayımlar ve prosedürel dokular "gerçek fotoğraf dokusu" sayılmaz.

Kısıt: ücretli görüntü satın alma, ücretli API kotası, devlet kurumundan özel veri temini veya ücretli drone çekimi yok.

## Doğrulanan açık kaynaklar

1. **OSM + Mapzen Terrain:** Trabzon Meydan pilot sınırı (39.725, 41.001, 39.737, 41.010) için GitHub Actions'da 1.466 OSM bina, 422 yol, 23 yeşil/su alanı ve açık arazi verisi indirildi. Bazı bina yükseklikleri tahmini, çatı/cephe fotoğraf dokusu yok.
2. **OpenAerialMap / STAC:** `https://api.imagery.hotosm.org/stac/search` üzerinde `collections=openaerialmap` ve gerçek coğrafi bbox filtreleriyle pilot Meydan ve geniş Ortahisar tarandı. **Her iki sorgu da 0 görsel döndürdü.** Bu, yalnızca incelenen katalog ve alanları kapsar; başka kaynaklarda görüntü olmadığı anlamına gelmez. Kontrol: `scripts/audit_open_imagery.py`, GitHub Actions `Audit Free Trabzon Aerial Imagery`.
3. **Wikimedia Commons:** 9 adet lisanslı Trabzon fotoğrafı galeride. Bunlar fotoğraflı mesh veya otomatik cephe texture atlası olarak kullanılamaz.
4. **KartaView:** Görüntüler CC BY-SA 4.0 altında; pilot koordinatlar için API sorgusu denendi ama `api.openstreetcam.org` TLS sunucu sertifikası yanlış hostname nedeniyle başarısız oldu. *Kapsam var/yok iddiası yapılamaz.* Kontrol: `scripts/audit_street_photos.py`.
5. **Mapillary:** Sokak fotoğrafları CC BY-SA; hizmet ücretsiz. Kapsam/açık API erişimi ayrıca kontrol edilmeli. Sokak fotoğrafları gerçek çatı görünümü yerine geçmez.

## Uygulanabilir bedava yol

- Gerçek bina konumu/geometrisini OSM'den koru.
- Ücretsiz, uygun lisanslı yüksek çözünürlüklü ortofoto ortaya çıkarsa *jeoreferanslı veri* olarak arazi ve çatı üst yüzeyine projekte et. Bu işlem tek başına cepheyi oluşturmaz.
- Mapillary, KartaView ve Wikimedia'dan konumu ve lisansı doğrulanmış çekimlerle **bireysel, görünür yüzeyler** için doku kaplaması geliştir; az sayıdaki landmark için elle kamera/UV eşleştirme gerekebilir.
- Görüntüsü eksik bina için yüzeyi gerçekte varmış gibi uydurma. `verified`, `estimated`, `missing-photo` kalite etiketlerini sakla.
- Verinin kapsadığı bölgede sabit ortografik kamera ve karo çıktı üret, sonrasında isteğe bağlı illüstrasyon stili uygula.
- Yeni açık arşiv bulunduğunda lisans ve mekânsal kapsama doğrulanmadan resimleri büyük ölçekte indirip dağıtma.

## Teknik referanslar

- [OAM STAC ve raster servisleri](https://docs.imagery.hotosm.org/usage/using-imagery/)
- [Mapillary CC BY-SA lisans](https://help.mapillary.com/hc/en-us/articles/115001770409-CC-BY-SA-license-for-open-data)
- [KartaView CC BY-SA](https://kartaview.org/terms)
- [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

**Not:** Ücretsiz olmak lisansın kopyalama, dönüştürme ve yeniden yayımlamaya izin verdiği anlamına gelmez. Google Earth / Bing gibi görüntülerin ekran görüntülerini, içeriklerini veya tile paketlerini kendi yayımladığımız ürünün kalıcı texture verisi olarak izinsiz çıkarmıyoruz.
