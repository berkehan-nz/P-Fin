# Muratlı Böğürtlen — İş Planı ve Fizibilite (Son Hâl)

**Plan:** 10 dönüm dikensiz böğürtlen (Loch Ness + Chester + Prime-Ark), hibrit fidan (%70 doku kültürü + %30 2 yaşlı tüplü), satış ortağı + hafta sonu kendin-topla, kendi kurduğun dengeli teknoloji paketi
**Lokasyon:** Bursa / Karacabey / Muratlı · **Tarih:** 2 Ekim 2026
**Para birimi:** 2026 sabit fiyatlarıyla TL (1 USD = 49,1 TL, TCMB 1-2 Ekim 2026)
**Hesap modeli:** [`model_final.py`](model_final.py) (`--tables` ile bütün tablolar yeniden üretilir)

> Bu belge v1-v9'un vardığı son noktadır. Fiyatlar Ekim 2026 internet verileriyle güncellendi; doğrulanan kalemler tablolarda **D**, teklif alınması gerekenler **T** ile işaretli. Bölge, risk ve TEKNOSAB analizleri için v3-v4; seçenek karşılaştırmaları için v8'e bakılabilir.

---

## 0. Özet

| Gösterge | Değer |
|---|---:|
| **Başlangıç yatırımı (CAPEX)** | **1.566.179 TL** (≈ $31.900) |
| — dikimden önce (Kasım 2026 – Mart 2027) | 1.187.099 TL |
| — 2027 içinde (soğuk oda, gölge filesi, hasat) | 379.080 TL |
| Teknoloji payı | 119.232 TL (%8) |
| **Cepten çıkan en yüksek tutar** (2027 işletme açığı dahil) | **1.703.005 TL** |
| İlk hasat | 2027 sonbaharı (~1,5 t) |
| 2028 rekolte / net kâr | 10,1 t / 0,83 M TL |
| **2031 (tam verim) rekolte / net kâr** | **20 t / 2,43 M TL** (aylık ~202 bin TL) |
| 5 yıl toplam net kâr | 7,42 M TL |
| **Geri dönüş** | **2,3 yıl** (yatırım 2029 içinde çıkıyor) |
| Fiyatlar %30 düşük çıkarsa: 2031 net / geri dönüş | 1,17 M TL / 3,2 yıl |
| Maksimum üretim (çok iyi yönetim) | 25-28 t/yıl → 3,2-3,6 M TL net |

**İlk adım:** Toprak + sulama suyu analizi ve arazide profil çukuru. Toplam ~20-35 bin TL, 2-3 hafta (Bölüm 9). Bu sonuçlar sedde yüksekliğini, gübre/asit programını ve arazinin böğürtlene gerçekten uygun olup olmadığını belirler. Yatırım kararından önce alınması gereken tek teknik veri bu.

---

## 1. İş Modeli (tek paragraf)

10 dönümde üç çeşit dikensiz böğürtlen yetiştirip hasadı **haziran ortası – ekim sonuna** yayıyorsun. Ürünün ~%75-80'i tarlada kapaklı kaplara toplanıp kendi soğuk odanda soğutuluyor ve **satış ortağına** (taban fiyatlı sözleşmeyle) teslim ediliyor. Yola bakan sıralarda hafta sonu **kendin-topla** satışı yapılıyor (Bursa ~40-50 dk, TEKNOSAB komşu); fazla ürün hale, 2. sınıf ürün işlemeye gidiyor. Saha işini sen (Ankara'dan ~20-25 ziyaret/yıl), baban (Bursa) ve yevmiyeli ekip yürütüyor; sulama, gübre, hastalık riski ve soğuk zincir senin kurduğun sensör sistemiyle uzaktan izleniyor. Vergi: çiftçi statüsünde satışta %2 stopaj.

---

## 2. Başlangıç Yatırımı (CAPEX): Kalem Kalem

| Faz | Grup | Kalem | Miktar | TL | Fiyat |
|---|---|---|---|---:|:---:|
| 0 | Arazi | Dip kazan + diskaro + sedde (40 cm); lazer tesviye yok | 10 da | 64.800 | T |
| 0 | Arazi | Yanmış çiftlik gübresi ~3 t/da, temin + serme (~45 m³ × 1.771 TL) | 45 m³ | 86.400 | D |
| 0 | Arazi | Siyah PE malç 1,2 m (500 m rulo 1.450-2.220 TL) + serme | 7 rulo | 21.600 | D |
| 0 | Fidan | Doku kültürü fidan, viyolde (216'lık viyol ~5.300 TL) + 2-3 ay saksıda alıştırma | 3.171 ad × 46 TL | 157.535 | D |
| 0 | Fidan | 2 yaşlı tüplü fidan, hızlı blok (%30; tek tek 250 TL, toplu teklif) | 1.359 ad × 150 TL | 220.158 | T |
| 0 | Fidan | Dikim işçiliği (~18 yevmiye) |  | 27.000 | D |
| 0 | Telli sistem | Galvaniz direk 2,7 m, 8 m ara + baş direkleri | 483 ad × 350 TL | 182.574 | D |
| 0 | Telli sistem | Galvaniz tel 3 kat (75 TL/kg) + gergi/ankraj + montaj | ~10.000 m | 118.800 | D |
| 0 | Sulama | Damla sulama (9.000-12.000 TL/da) + hidrant bağlantısı, disk filtre, ana hat | 10 da | 172.800 | D |
| 0 | Teknoloji | Fertigasyon: 3 × Hunter PGV 1" selenoid (1.299 TL), venturi + bypass, ESP32 kontrolör + 24 VAC trafo | 3 zon | 12.960 | D/T |
| 0 | Teknoloji | Hat içi EC probu (gübre suyu uzaktan izleme) | 1 | 5.400 | T |
| 0 | Teknoloji | Hanna HI98129 pH/EC/TDS el ölçer | 1 | 14.472 | D |
| 0 | Teknoloji | Toprak düğümü: 2 × RS485 nem/sıcaklık/EC probu (4.232 TL) + Heltec ESP32-LoRa + solar/akü/kutu | 3 × 12.000 TL | 38.880 | D |
| 0 | Teknoloji | LoRaWAN gateway (Dragino, ~€160-245) + 4G modem | 1 | 14.040 | D |
| 0 | Teknoloji | Hava düğümü: sıcaklık/nem + yaprak ıslaklığı + yağmur ölçer + ESP32/solar | 1 | 8.640 | D/T |
| 0 | Teknoloji | Ana hat debimetresi (darbe çıkışlı) | 1 | 4.320 | T |
| 0 | Teknoloji | Raspberry Pi 5 + UPS + SSD (yerel sunucu, internet kesilse de çalışır) | 1 | 12.960 | D/T |
| 0 | Teknoloji | Solar 4G güvenlik kamerası (3.100-8.000 TL) | 1 | 7.560 | D |
| 0 | Diğer | ÇKS kaydı, tarımsal yapı bildirimi, küçük giderler |  | 16.200 | T |
| 1 | Soğuk zincir | Soğuk oda: 100 mm panel ~32 m² (890-1.050 TL/m²) + kapı/profil/montaj | ~12 m³ | 55.080 | D |
| 1 | Soğuk zincir | 24.000 BTU inverter klima (54-75 bin TL) + termostat kontrolü + ön soğutma fanı | 1 | 75.600 | D |
| 1 | Soğuk zincir | Elektrik bağlantısı (monofaze) + pano |  | 43.200 | T |
| 1 | Soğuk zincir | Wi-Fi sıcaklık sensörü + Telegram alarmı + 2 logger |  | 5.400 | T |
| 1 | Kalite | %35 gölge filesi (güney cephe + Chester sıraları, ~3.000 m² × ~35 TL) + montaj | ~3.000 m² | 135.000 | D/T |
| 1 | Hasat | 60 hasat kasası, 2 el arabası, terazi, etiket yazıcı |  | 32.400 | T |
| 1 | Hasat | Gıda işletme kaydı (İyi Tarım ortak isterse sonra) |  | 10.800 | T |
| 1 | Kendin-topla | Tabela, satış tezgâhı, gölgelik (WC kiralık) |  | 21.600 | T |
| | | **Faz 0 — dikimden önce (Kasım 2026 – Mart 2027)** | | **1.187.099** | |
| | | **Faz 1 — 2027 içinde, ilk büyük hasattan önce** | | **379.080** | |
| | | **TOPLAM BAŞLANGIÇ YATIRIMI** | | **1.566.179** | ≈ $31.898 |

*D: Ekim 2026 internet fiyatıyla doğrulandı · T: tahmin, teklif alınmalı · D/T: ana bileşen doğrulandı, kalan tahmin. Tutarlar %8 beklenmeyen gider payı dahil.*

### Grup özeti

| Grup | TL | Pay |
|---|---:|---:|
| Fidan | 404.693 | %26 |
| Telli sistem | 301.374 | %19 |
| Soğuk zincir | 179.280 | %11 |
| Arazi | 172.800 | %11 |
| Sulama | 172.800 | %11 |
| Kalite | 135.000 | %9 |
| Teknoloji | 119.232 | %8 |
| Hasat | 43.200 | %3 |
| Kendin-topla | 21.600 | %1 |
| Diğer | 16.200 | %1 |
| **Toplam** | **1.566.179** | |

**Neler bilinçli olarak yok:** lazer tesviye (arazi toplulaştırmada düzlenmiş; profil çukuru ve analiz sonucu gerekirse eklenir), agrotekstil (PE malç yeterli), pakethane, tünel, güneş paneli, şok dondurucu, traktör (hizmet alımı), çit, ofis konteyneri, İyi Tarım belgesi (ortak isterse).

---

## 3. Teknoloji Paketi (dengeli: kaliteden ve riskten ödün yok)

| Bileşen | Ne işe yarar | Kalite/risk etkisi |
|---|---|---|
| 3 zonlu otomatik sulama (selenoid + ESP32 kontrolör) | Her çeşit bloğu kendi ihtiyacına göre sulanır | Kök boğulması ve susuz kalma riskini önler |
| Venturi + hat içi EC probu + Hanna pH/EC el ölçer | Gübre suyunun yoğunluğu uzaktan, pH'ı haftada 2 el ölçümüyle | Demir eksikliği ve tuzlanma kontrolü |
| 3 toprak düğümü (her blokta 30 ve 60 cm nem/EC/sıcaklık) | Sulama kararı veriye dayanır | Ankara'dan yönetimin temeli |
| LoRaWAN gateway + 4G | 10 dönümü kablosuz kapsar | Kesintisiz veri |
| Hava düğümü (sıcaklık/nem, yaprak ıslaklığı, yağmur) | Hastalık riski ve don uyarısı | İlaçlama doğru zamanda |
| Ana hat debimetresi | Tıkanma/kaçak alarmı | Sessiz sulama arızasını yakalar |
| Raspberry Pi 5 yerel sunucu + UPS | İnternet kesilse de sulama ve alarm çalışır | Sistem güvenilirliği |
| Solar 4G kamera | Hırsızlık ve uzaktan gözlem | Güvenlik |
| Soğuk oda Wi-Fi sensörü + Telegram alarmı + logger | Oda arızasında telefona alarm | Bir günün hasadını (~60 bin TL) korur |

**Toplam: 119 bin TL** (v8'deki ~370 bin TL'lik pakete göre −%68). **Çıkarılanlar:** dozaj pompaları, fazladan 3 toprak düğümü, profesyonel meteoroloji istasyonu ve referans prob, yapay zekâlı PTZ/termal kamera, ayrı mini PC. Bunlar ileride 2028 gelirinden eklenebilir; ESP32 ve LoRa altyapısı genişlemeye hazır. **Yazılım** tamamen açık kaynak: ChirpStack, InfluxDB, Grafana, Node-RED, Telegram botu.

---

## 4. İşletme Giderleri (OPEX)

### Sabit giderler

| Sabit gider (TL/yıl) | 2027 | 2028 | 2029 | 2030 | 2031 |
|---|---:|---:|---:|---:|---:|
| Gübre + mücadele (böğürtlen) | 30.000 | 55.000 | 70.000 | 75.000 | 75.000 |
| Budama, bağlama, ot (yevmiyeli) | 50.000 | 90.000 | 110.000 | 120.000 | 120.000 |
| Traktör/ilaçlama hizmet alımı | 18.000 | 18.000 | 18.000 | 18.000 | 18.000 |
| DSİ sulama ücreti | 15.000 | 15.000 | 15.000 | 15.000 | 15.000 |
| Sezonluk soğuk oda/etiket yardımcısı | 0 | 45.000 | 60.000 | 60.000 | 60.000 |
| Elektrik (soğuk oda) | 3.000 | 10.000 | 15.000 | 16.000 | 16.000 |
| Bakım-onarım | 10.000 | 30.000 | 40.000 | 45.000 | 50.000 |
| TARSİM sigortası | 0 | 30.000 | 40.000 | 45.000 | 50.000 |
| Arı kovanı kiralama | 0 | 15.000 | 15.000 | 15.000 | 15.000 |
| SIM/4G + bulut, muhasebe, analiz | 50.000 | 50.000 | 50.000 | 50.000 | 50.000 |
| Kurucu ulaşımı (Ankara, ~20-25 ziyaret) | 125.000 | 125.000 | 125.000 | 125.000 | 125.000 |
| Baba: yakıt/harcırah | 40.000 | 40.000 | 40.000 | 40.000 | 40.000 |
| Kendin-topla: ilan, sosyal medya | 0 | 25.000 | 25.000 | 25.000 | 25.000 |
| **Toplam** | **341.000** | **548.000** | **623.000** | **649.000** | **659.000** |

### Değişken giderler (kg başı)

| Kalem | TL/kg | Dayanak |
|---|---:|---|
| Hasat, paket kalitesi (kişi/gün 55 kg) | 28 | Yevmiye 1.400 TL + %10 dayıbaşı (Bursa 2026: 1.100-1.500 TL) |
| Hasat, dökme (kişi/gün 70 kg) | 22 | Aynı |
| Kapaklı kap + etiket + koli | 25 | 250 cc kap ~2,9 TL/ad |
| Ortağa yükleme (ortak tarladan alır) | 5 | Sözleşme maddesi |
| Hal komisyonu + kasa | %10 + 8 | |
| Kendin-topla görevli, kap, ilan | 40 | |

---

## 5. Beş Yıllık Projeksiyon (2027-2031)

| TL | 2027 | 2028 | 2029 | 2030 | 2031 | 5 yıl |
|---|---:|---:|---:|---:|---:|---:|
| Rekolte (t) | 1,5 | 10,1 | 17,9 | 20,0 | 20,0 | 69,5 |
| — Ortak üzerinden paketli | 144.648 | 1.398.510 | 2.582.016 | 2.853.600 | 2.794.560 | 9.773.334 |
| — Kendin-topla | 0 | 200.000 | 480.000 | 600.000 | 720.000 | 2.000.000 |
| — Hal | 105.483 | 339.949 | 470.726 | 520.238 | 509.475 | 1.945.870 |
| — 2. sınıf → işleme | 19.110 | 131.300 | 232.700 | 260.000 | 260.000 | 903.110 |
| **Gelir** | **269.241** | **2.069.759** | **3.765.442** | **4.233.838** | **4.284.035** | **14.622.314** |
| Değişken gider (hasat, kap, kanal) | −59.682 | −461.120 | −832.148 | −927.800 | −924.080 | −3.204.830 |
| Sabit gider (OPEX) | −341.000 | −548.000 | −623.000 | −649.000 | −659.000 | −2.820.000 |
| **FAVÖK** | **−131.441** | **1.060.639** | **2.310.294** | **2.657.038** | **2.700.955** | **8.597.484** |
| Amortisman | −137.941 | −190.455 | −190.455 | −183.255 | −186.682 | −888.787 |
| Stopaj (%2) | −5.385 | −41.395 | −75.309 | −84.677 | −85.681 | −292.446 |
| **Net kâr** | **−274.767** | **828.789** | **2.044.530** | **2.389.107** | **2.428.592** | **7.416.251** |
| Aylık net kâr | −22.897 | 69.066 | 170.378 | 199.092 | 202.383 |  |
| Yatırım (CAPEX) / yenileme | −379.080 | 0 | 0 | −20.000 | 0 | −399.080 |
| **Kümülatif nakit (yatırım dahil)** | **−1.703.005** | **−683.762** | **1.551.223** | **4.103.585** | **6.718.859** | |

**Satış fiyatı varsayımları:**

- **Hal:** mevsime göre ağırlıklı 199 TL/kg. Haziran 450, temmuz 250, ağustos 180, eylül 220, ekim 300; %15 hacim/kalite iskontosuyla.
- **Satış ortağı:** paketli 300 TL/kg; %18 komisyon düşülüyor.
- **Kendin-topla:** 400 TL/kg perakende.
- **2. sınıf ürün:** 65 TL/kg (işleme).

Kaynaklar Ek A'da.

---

## 6. Ne Kadar Üretebilirim? (Maksimum Kapasite)

| Üretim düzeyi (tam verim) | t/da | Rekolte | Net kâr / yıl | Aylık | Fiyat −%30 ile net |
|---|---:|---:|---:|---:|---:|
| Temkinli | 1,5 | 15 t | 1,69 M TL | 140.783 TL | 0,72 M TL |
| Baz (iyi yönetim) | 2,0 | 20 t | 2,43 M TL | 202.383 TL | 1,17 M TL |
| Çok iyi yönetim | 2,5 | 25 t | 3,17 M TL | 263.983 TL | 1,62 M TL |
| Üst sınır (açık tarla Chester/Loch Ness) | 2,8 | 28 t | 3,61 M TL | 300.943 TL | 1,88 M TL |

- **2 t/da (baz)**, sertifikalı fidan, damla + fertigasyon, sık dikim ve iyi budamayla Türkiye'de açık tarlada ulaşılabilir bir hedef.
- **2,5 t/da**, ilk iki sezonun sensör ve hasat verisiyle sulama/gübre programı oturduğunda mümkün.
- **2,8 t/da** açık tarla için üst sınır. Bunu aşmak tünel, saksı veya topraksız sistem ister (v8'de ekonomik bulunmadı).
- **Altyapı kapasitesi:** 12 m³ soğuk oda 28 t'luk yılda tepe gün yükünü (~450 kg) taşır. 25 t üstünde 4-5 yerine 6-7 toplayıcı gerekir.
- **Dikkat:** Rekolte arttıkça yerel fiyat düşebilir. Ortakla yıllık hacim taahhüdü bunu dengeler.

---

## 7. Hızlı Sonuç İçin Ne Yapıldı?

| Hızlandırıcı | Etkisi |
|---|---|
| %30 2 yaşlı tüplü fidan | 2028 rekoltesi 8 t yerine 10 t; ~290 bin TL ek net kâr |
| Prime-Ark (sonbahar ürünlü) çeşit | Dikim yılında, 2027 eylül-ekimde ilk satış |
| Kendin-topla kanalı | 2028'den itibaren en yüksek kg kârı (perakende 400 TL) |
| Dikim Nisan 2027 | Fidan siparişi **Ekim-Kasım 2026'da** verilmeli (viyolden alıştırma 2-3 ay) |
| Satış ortağı | 2028'den itibaren ürünün %75-80'i doğrudan alıcılı |

**Para akışı:** 2027 eksi (yatırım + ilk yıl), 2028'den itibaren artı (aylık ~69 bin TL), 2029'da yatırımın tamamı geri dönmüş oluyor.

---

## 8. Stres Testi

| Senaryo | 2031 net | Geri dönüş | 10 yıl IRR |
|---|---:|---:|---:|
| Baz | 2,43 M TL | 2,3 yıl | %71,4 |
| Tüm fiyatlar −%30 | 1,17 M TL | 3,2 yıl | %41,6 |
| Verim −%25 | 1,69 M TL | 2,7 yıl | %54,7 |
| İşçilik +%40 | 2,19 M TL | 2,4 yıl | %65,8 |
| Ortak fiyatı 200 TL (hal düzeyi) | 1,52 M TL | 2,9 yıl | %50,5 |
| Fiyat −%30 + verim −%15 + işçilik +%20 | 0,80 M TL | 3,9 yıl | %30,1 |

Proje en kötü kombinasyonda bile (fiyat −%30, verim −%15, işçilik +%20) 4 yıl içinde geri dönüyor. **En kritik değişkenler:** satış ortağının fiyatı ve genel fiyat seviyesi. Bursa halinde 16 Eylül 2026'da 60-70 TL/kg işlem görmüş olması (muhtemelen yabani/sezon sonu) yerel fiyatın düşük olabileceğini gösteriyor. **Ortak sözleşmesinde taban fiyat şart.**

---

## 9. ADIM 1 — Fizibiliteyi Derinleştirmek: Önce Ne Lazım?

### 9.1 Toprak ve sulama suyu analizi (en önemli ilk adım)

**Neden:** Böğürtlenin başarısı üç toprak özelliğine bağlı:

- **Drenaj ve kil oranı:** Kök boğulmasına hassas; sedde yüksekliğini belirler.
- **pH ve kireç:** pH 7,5 üstünde ve kireç yüksekse demir eksikliği görülür; asit programı gerekir.
- **Tuz ve bor:** Böğürtlen bora hassastır.

Ayrıca sulama suyunun bikarbonatı yüksekse gübre suyuna asit gerekir.

**Kime gideceksin (Bursa):**

| Laboratuvar | Not |
|---|---|
| **Bursa İl Tarım ve Orman Müdürlüğü, Toprak-Bitki Analiz Laboratuvarı** | Resmî laboratuvar; numune kabulünü telefonla sor |
| **Trakya Birlik Karacabey Toprak Tahlil Laboratuvarı** | Bakanlığın yetkili laboratuvar listesinde; Karacabey'de, araziye en yakın |
| **Nilüfer Belediyesi Tarımsal Analiz Laboratuvarı** (Ulutek Teknopark) | Üreticiye yönelik |
| TÜBİTAK BUTAL (Bursa) | Tek tek parametre fiyatlı (ör. kireç 1.000 TL + KDV) |

Ayrıca **Karacabey İlçe Tarım ve Orman Müdürlüğü:** ÇKS kaydı, ücretsiz yayım/danışmanlık, numune alma tavsiyesi.

**Ne isteyeceksin (laboratuvara aynen söyle):**

1. **Toprak:** "Meyve bahçesi tesisi için verimlilik analizi: bünye (kum-silt-kil), pH, EC/tuz, kireç, organik madde, yarayışlı fosfor ve potasyum, **mikro elementler (Fe, Zn, Mn, Cu) ve bor**, mümkünse değişebilir sodyum." Referans fiyat: standart paket ~975 TL/numune (Bilecik Üni. 2026 tarifesi). Mikro elementler ve bor ek; Bursa laboratuvarlarından teyit edilmeli.
2. **Su:** "Sulama suyu sınıflandırma analizi: EC, pH, Na, Ca, Mg, SAR, **bikarbonat**, klor, **bor**." Referans: tek tek parametre ~227-348 TL; paket ~2.500-3.500 TL.

**Numune nasıl alınır (sen ya da baban, 1 gün):**

- **Bölme:** 10 dönümü iki yarıya böl (kuzey/güney ya da göze çarpan farka göre).
- **Noktalar:** Her yarıda zikzak çizerek **15-20 noktadan** burgu ya da kürekle toprak al.
- **Derinlik:** **0-30 cm** ve **30-60 cm** ayrı torbalara. Toplam **4 karışık numune**, her biri ~1 kg.
- **Kaçınılacak yerler:** Gübre yığını yerleri, tarla kenarları ve yol dibi.
- **Etiket:** Torbaya ada/parsel, derinlik ve tarih yaz.
- **Su:** DSİ hidrantından temiz şişeye 1-1,5 litre al; kuyu varsa ondan da ayrı numune.
- **Teslim:** Numuneleri 2-3 gün içinde laboratuvara ver. Sonuçlar genellikle 1-2 haftada çıkar.

### 9.2 Arazide profil çukuru (aynı gün)

Bir kepçeyle (1-2 saat) **1-1,2 m derinliğinde** çukur açtır ve fotoğrafla. Bakılacaklar:

- **Taban taşı / sert katman (pulluk tabanı):** Varsa dip kazan derinliğini belirler.
- **Kök bölgesinde gri-mavi lekeler (taban suyu izi):** Varsa sedde 50 cm'ye çıkar.
- **Su gelip gelmediği:** Çukura su geliyorsa drenaj önlemi gerekir.

Bu tek gözlem lazer tesviye ve sedde kararını netleştirir.

### 9.3 Aynı ay yapılacak diğer kontroller (masrafsız ya da düşük maliyetli)

| Konu | Kime | Ne soracaksın |
|---|---|---|
| Elektrik | **UEDAŞ** (Bursa elektrik dağıtım) | Parsele en yakın hat (monofaze/trifaze), bağlantı bedeli ve süresi |
| Sulama | **DSİ / sulama birliği** | Hidrant yeri ve debisi, 2026 meyve bahçesi su ücreti, sulama takvimi |
| Satış | **Satış ortağı** | Ön protokol: yıllık tonaj, ay bazında fiyat, **taban fiyat**, teslim şekli, ödeme vadesi |
| Fidan | **Fidanlıklar** (doku kültürü viyol + tüplü) | 3 çeşit için 3.200 viyol + 1.360 tüplü fidan: fiyat, sertifika, **teslim tarihi** |
| Finansman | **Ziraat Bankası** | Hazine faiz destekli kredi şartları; başvuru **31.12.2026'dan önce** |
| İzin | **Karacabey İlçe Tarım** | ÇKS kaydı; soğuk oda için tarımsal yapı izni gerekip gerekmediği |

### 9.4 Adım 1'in maliyeti

| Kalem | Tahmini TL |
|---|---:|
| 4 toprak numunesi (paket + mikro element + bor) | 6.000-10.000 |
| 1-2 sulama suyu analizi | 2.500-6.000 |
| Profil çukuru (kepçe 1-2 saat) | 3.000-5.000 |
| Ziraat mühendisi arazi ziyareti ve analiz yorumu (İlçe Tarım'da ücretsiz; serbest danışman ücretli) | 0-15.000 |
| Ankara–Karacabey 1-2 ziyaret (yakıt + otoyol) | 5.000-10.000 |
| **Toplam** | **~20.000-35.000 TL** |

### 9.5 Sonuçlara göre karar kuralları

| Sonuç | Ne anlama gelir | Karar |
|---|---|---|
| pH ≤ 7,5, kireç < %10, EC < 1 dS/m, bor < 0,5 mg/L (su) | Uygun | Plan aynen devam |
| pH 7,5-8,0 veya kireç %10-20 | Demir eksikliği riski | Gübre suyuna asit (sülfürik/fosforik), demir şelat; maliyet +~20-30 bin TL/yıl |
| Kil > %45 veya profil çukurunda su/gri leke | Kök boğulması riski | Sedde 50 cm, gerekirse lazer tesviye (+~55 bin TL) |
| Suda bikarbonat yüksek | Damlatıcı tıkanması, pH yükselmesi | Sürekli asit enjeksiyonu (hat içi EC/pH bunun için kritik) |
| Toprakta veya suda bor yüksek (> 0,7-1 mg/L) | Böğürtlen için toksik | **Dur:** danışmanla yeniden değerlendir; gerekirse başka parsel |
| EC > 2 dS/m (tuzlu) | Verim kaybı | **Dur:** yıkama/drenaj olmadan dikim yapılmaz |

---

## 10. ADIM 2 ve Sonrası: Takvim

| Dönem | İş | Karar kapısı |
|---|---|---|
| **Ekim 2026, 1-2. hafta** | Toprak/su numunesi, profil çukuru, UEDAŞ + DSİ + İlçe Tarım görüşmeleri, satış ortağıyla ön protokol | |
| **Ekim 2026, 3-4. hafta** | Analiz sonuçları → danışmanla son tasarım (sedde, gübre/asit programı); fidanlık teklifleri | **Kapı 1:** Toprak ve su uygun mu? Ortak taban fiyatı kabul etti mi? |
| **Kasım 2026** | Fidan siparişi (viyol teslimi Aralık-Ocak); dip kazan, gübre, sedde (kış yağmurlarından önce); Ziraat kredi başvurusu | **Kapı 2:** Sermaye/kredi hazır mı? |
| **Aralık 2026 – Şubat 2027** | Telli sistem, ana sulama hattı; viyol fidanları saksıda alıştırma (Bursa'da korunaklı bir alanda, babanla); sensör prototipleri evde | |
| **Mart 2027** | Damla lateraller, PE malç, sensörler, gateway, kamera | |
| **Nisan 2027** | **Dikim** (don riskinden sonra) | |
| **Mayıs-Ağustos 2027** | Kol yönetimi, sulama kalibrasyonu; soğuk oda ve gölge filesi (Faz 1); kendin-topla hazırlığı | |
| **Eylül-Ekim 2027** | **İlk hasat** (Prime-Ark + tüplü fidan, ~1,5 t), ortakla ilk teslimat | **Kapı 3:** Fiyat ve kalite hedefte mi? |
| **Haziran-Ekim 2028** | İlk büyük hasat (~10 t), kendin-topla açılışı | 2028 sonu: 20 da'ya büyüme kararı (v8 seçenek D) |

---

## 11. Hâlâ Doğrulanması Gereken Varsayımlar

1. **Satış ortağının fiyatı (300 TL/kg) ve taban fiyatı.** Sonucu en çok etkileyen tek kalem.
2. **Hal fiyatı:** mevsimsel ağırlıklı 199 TL/kg. Bursa ve İstanbul hal kayıtlarından son 2 sezon kontrol edilmeli.
3. **Tüplü fidanın toplu fiyatı** (150 TL, tek tek 250 TL) ve viyol fidanın teslim tarihi.
4. **Elektrik bağlantı bedeli** (40 bin TL tahmini; hat uzaksa çok daha yüksek olabilir).
5. **Dip kazan/sedde hizmet bedeli** ve **hasat kasası** fiyatı (tahmin).
6. **Kendin-topla talebi:** 2028'de 0,5 t ile başlayıp yılda 2 t'ya çıkması varsayımı.

---

### Ek A — Kaynaklar (Ekim 2026)

- **Kur:** [Halk TV, 2 Ekim 2026](https://halktv.com.tr/ekonomi/2-ekim-2026-doviz-kurlari-euro-kac-tl-dolar-kac-tl-sterlin-kac-tl-1058876h)
- **Böğürtlen fiyatı:** [haldefiyat](https://haldefiyat.com/urun/bogurtlen), [Tarım Ziraat](https://www.tarimziraat.com/fiyat/bogurtlen_fiyatlari-a97.html), [Bursa hal](https://www.bursa.bel.tr/hal_fiyatlari), [Migros 125 g](https://www.migros.com.tr/hemen/bogurtlen-125-g-p-19cc015)
- **Fidan:** [Bursa Tarım Market, doku kültürü çoklu satış](https://www.bursatarimmarket.com/doku-kulturu-ile-coklu-satis), [Elma Tarım, Chester](https://elmatarim.com.tr/urun/doku-kulturuyle-uretilmis-chester-bogurtlen-fidani/)
- **Yevmiye:** [Bursadabugün](https://www.bursadabugun.com/haber/bursa-da-tarim-iscilerine-gunluk-ne-kadar-odenecek-yeni-tarife-belli-oldu-1923814.html), [Sanayi Gazetesi](https://sanayigazetesi.com.tr/2026-sezonluk-isciucretleri/)
- **Damla sulama:** [Tarım Memleketi](https://tarimmemleketi.com/1-donum-damla-sulama-maliyeti)
- **Direk ve tel:** [Panel Çit Ankara](https://www.panelcitankara.com/urundetay/boru-direk)
- **Gübre (çiftlik gübresi temin ve serme birim fiyatı):** [birimfiyat.com](https://birimfiyat.com/pdf/52370)
- **Malç:** [Hepsiburada, Sef Tarım malç](https://www.hepsiburada.com/sef-tarim-malc-naylonu-1-2m-en-500m-uzunluk-20-micron22-5-kg-pm-HBC00003NBFNK), [Cimri](https://www.cimri.com/malc-naylonu)
- **Gölge filesi:** [Akakçe](https://www.akakce.com/golgelik-file.html)
- **Soğuk oda paneli:** [Yapıpan](https://yapipanmetal.com/urun/sandvic-panel/sandvic-soguk-oda-paneli-100mm-ral-9002/)
- **Klima:** [Cimri, 24.000 BTU](https://www.cimri.com/klimalar/en-ucuz-siemens-as24ivw32n-24000-btu-inverter-duvar-tipi-klima-fiyatlari,2497594586)
- **Teknoloji bileşenleri:** [Cimri, selenoid vana](https://www.cimri.com/selenoid-vana), [E-Tartes, RS485 toprak sensörü](https://www.e-tartes.com/toprak-nemi-sicakligi-ve-tuzluluguec-sensoru-rs485-4735), [Dragino gateway](https://invibitshop.com/collections/dragino), [Heltec ESP32-LoRa](https://heltec.org/lora-enable%EF%BC%9Aesp32-series), [Cimri, Hanna HI98129](https://www.cimri.com/diger-test-ve-olcum-cihazlari/en-ucuz-hanna-hi-98129-dijital-ph-ec-tds-olcum-cihazi-fiyatlari,2423775134), [idefix, solar 4G kamera](https://www.idefix.com/venas-sim-kartli-solar-panelli-hareket-sensorlu-guvenlik-kamerasi-p-19837777)
- **Toprak analizi:** [Bilecik Üniversitesi Ziraat Fakültesi laboratuvar ücretleri](https://bilecik.edu.tr/ziraat/Icerik/Toprak_Su_Bitki_Analiz_Laboratuvar%C4%B1_3f7ea), [TÜBİTAK BUTAL katalog](https://butal.tubitak.gov.tr/wp-content/uploads/sites/115/BUTAL_KATALOG_2025.pdf), [Bakanlık yetkili laboratuvar listesi](https://www.tarimorman.gov.tr/TRGM/Belgeler/Duyurular/lab_liste.pdf), [Bursa İl Tarım laboratuvar hizmetleri](https://bursa.tarimorman.gov.tr/Menu/22/Laboratuvar-Hizmetlerimiz), [Nilüfer Tarımsal Analiz Laboratuvarı](https://www.nilufer.bel.tr/haber/nilufer-tarimsal-analiz-laboratuvari-ile-ureticiye-destek)
- **Sulama suyu analizi:** [Toprak Gübre Araştırma Enstitüsü analiz fiyatları](https://arastirma.tarimorman.gov.tr/toprakgubre/Belgeler/Analiz%20Fiyatları/Analiz%20Fiyatları%202023/Analiz_Fiyat_2023_Rev.pdf)
