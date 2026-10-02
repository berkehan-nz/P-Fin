# Muratlı Böğürtlen — Fizibilite v6: Ek Gelir İçin Yalın Hibrit Plan

**Amaç:** Tesis veya uzun vadeli vizyon değil, kurucuya **ek gelir** üreten bir bahçe. En az yatırım (CAPEX) ve işletme gideriyle (OPEX) en çok kaliteli üretim. Kalite için gereken teknoloji korunuyor ve kurucu tarafından kendisi kuruluyor.
**Kurgu:** Satışı bir iş ortağı yapıyor (%18 komisyon). Saha işi kurucu (Ankara'dan ziyaret), baba (Bursa) ve yevmiyeli ekiple yürüyor. Traktör hizmeti satın alınıyor. Pakethane yok; ürün tarlada kapaklı kaba toplanıyor.
**Lokasyon:** Bursa / Karacabey / Muratlı · **Tarih:** 2 Ekim 2026 · **Para birimi:** 2026 sabit USD; 1 USD = 47 TL
**Hesap modeli:** [`model_v6.py`](model_v6.py) (`--tables` ile bütün tablolar yeniden üretilir)

> Bu rapor v1-v5'teki tarım, risk ve bölge analizlerine dayanıyor; kapsamı bilinçli olarak daraltıyor. Çıkarılanlar: test sahası (living lab), danışmanlık, liyofilize makinesi, pakethane, kalıcı teknisyen, şirket yapısı. Mevsim riski simülasyonu ve TEKNOSAB/imar analizi için v3 ve v4'e bakılabilir.

---

## 0. Özet

| Gösterge | 10 da | 20 da |
|---|---:|---:|
| Başlangıç yatırımı (Faz 0 + 1) | $67.367 (3,2 M TL) | $109.305 (5,1 M TL) |
| Cepten çıkan en yüksek tutar (işletme açıkları dahil) | $72.165 (3,4 M TL) | $117.333 (5,5 M TL) |
| — Ziraat faiz destekli kredi (%50) ile | $41.967 (2,0 M TL) | $69.098 (3,2 M TL) |
| 2028 rekolte / net kâr | 10,1 t / −$251 | 20,2 t / $4.051 |
| 2031 rekolte / net kâr | 20,0 t / $19.150 | 40,0 t / $48.066 |
| 2031 aylık ortalama ek gelir (net) | 75.006 TL | 188.260 TL |
| 5 yıl toplam net kâr | $43.042 | $113.747 |
| 10 yıl toplam net kâr | $135.766 | $339.310 |
| Geri dönüş (Y0'dan) | 4,5 yıl | 4,3 yıl |
| 10 yıllık IRR / NPV (%12) | %21,6 / $35.638 | %27,4 / $110.045 |

**Önerim: 20 dönüm, hibrit dikim, 2027 ilkbaharı.**

- **Neden 20 da:** Soğuk depo, sensör ağı, ulaşım ve sabit giderler iki büyüklükte de neredeyse aynı. 20 dönümde ~1,6 kat yatırımla 2031 net kârı ~2,5 kat oluyor.
- **Hibrit dikim (her 10 dönümün %70'i doku kültürü, %30'u 2 yaşlı saksılı fidan):** Saksılı blok 2027'de ilk ürünü, 2028'de tam verime yakın ürünü veriyor. Böylece 2028'de toplam verim tam verimin yarısına ulaşıyor (20 da'da 20 t). Fidan bütçesi ise tamamen saksılı yapılan plana göre ~$22k daha düşük.
- **2031'de aylık ortalama ~188 bin TL net ek gelir** (20 da). 4,3 yılda başlangıç sermayesini geri ödüyor.

**Bu sonuçlar iki şarta bağlı:**

1. **Satış ortağıyla yazılı ve taahhütlü sözleşme:** minimum yıllık alım tonajı, taban fiyat, komisyon, ürünü soğuk depodan teslim alma, ödeme vadesi.
2. **Babanın düzenli saha desteği.** Olmazsa yerine ücretli bir saha şefi gerekir (~$9k/yıl): 20 dönümde 2031 net kârı ~%19 düşer.

---

## 1. Tasarım İlkeleri

| İlke | Uygulama |
|---|---|
| **Kaliteyi belirleyen şeye para harca** | Sertifikalı fidan, damla + fertigasyon, ön soğutma + soğuk depo, gölge filesi, toprak/iklim ölçümü |
| **Kaliteyi belirlemeyen şeyi erte veya kirala** | Pakethane, traktör, ofis konteyneri, çit, GES, termal kamera, meyve sayım kameraları, liyofilize: hepsi yok ya da kârdan sonra |
| **Teknolojiyi kendin kur, açık kaynakla çalıştır** | Endüstriyel sensör + ESP32/LoRa; sunucuda açık kaynak yazılım; lisans ve abonelik yok |
| **Her teknoloji bir kararı beslemeli** | Sulama ne zaman, ilaç ne zaman, hasat ne zaman, soğuk zincir kırıldı mı. Bu dört soruya cevap vermeyen hiçbir şey kurulmuyor |
| **Giderler değişken olsun** | Hasat, budama, traktör: iş varken ödeniyor. Sabit personel yok (20 da'da yalnızca sezonluk 1 kişi) |

---

## 2. Hibrit Dikim Planı

| Blok (her 10 da için) | Alan | Fidan | Çeşit | Rolü |
|---|---:|---|---|---|
| **Çekirdek** | 7 da | Sertifikalı doku kültürü, sık dikim (3 m × 0,75 m), ~3.170 ad | Loch Ness + Chester (yazlık) | Ucuz, virüssüz, uzun ömürlü kalite motoru |
| **Hızlı** | 3 da | 2 yaşlı saksılı sertifikalı fidan, sık dikim, ~1.360 ad | Prime-Ark Traveler/Freedom (sonbaharlık) + bir kısım Loch Ness | 2027'de ilk ürün, 2028'de tama yakın verim |

**Beklenen rekolte:**

| Yıl | Doku kültürü bloğu (7 da) | Saksılı blok (3 da) | Toplam / 10 da | Toplam / 20 da |
|---|---:|---:|---:|---:|
| 2027 | 0,4 t | 1,1 t | 1,5 t | 2,9 t |
| 2028 | 5,6 t | 4,5 t | 10,1 t | 20,2 t |
| 2029 | 11,9 t | 6,0 t | 17,9 t | 35,8 t |
| 2030 | 14,0 t | 6,0 t | 20,0 t | 40,0 t |
| 2031 | 14,0 t | 6,0 t | 20,0 t | 40,0 t |
| 2032 | 14,0 t | 6,0 t | 20,0 t | 40,0 t |
| 2033 | 14,0 t | 6,0 t | 20,0 t | 40,0 t |
| 2034 | 14,0 t | 6,0 t | 20,0 t | 40,0 t |
| 2035 | 12,6 t | 5,4 t | 18,0 t | 36,0 t |
| 2036 | 11,2 t | 4,8 t | 16,0 t | 32,0 t |

Üç çeşitle hasat haziran ortasından ekim sonuna yayılıyor (v3 Bölüm 1-3). Bu, tepe işçi ihtiyacını ve soğuk depo yükünü düşürüyor; küçük bir altyapıyla büyük hacmi taşımanın anahtarı bu.

---

## 3. Teknoloji: Kendi Kuracağın Sistem

### 3.1 Ne kuruluyor?

| Katman | Bileşen | Neden şart (hangi kararı besliyor) |
|---|---|---|
| **Toprak** | 6 (10 da) / 10 (20 da) düğüm. Her düğümde ESP32-LoRa kart, 30 ve 60 cm'de 2 endüstriyel RS485 nem/EC/sıcaklık probu, küçük güneş paneli + akü | **Ne zaman ve ne kadar sulama.** Böğürtlen ağır toprakta kök boğulmasına hassas; hem kuraklık hem fazla su kaliteyi düşürür |
| **Kalibrasyon** | 1 profesyonel referans prob | Kendi sensörlerinin doğru ölçtüğünden emin olmak (sezonda bir kez karşılaştırma) |
| **İklim** | Hobi-profesyonel meteoroloji istasyonu + yaprak ıslaklığı sensörü | **Ne zaman ilaçlama:** hastalık riski (ıslaklık süresi), don, sıcak dalgası uyarısı |
| **Fertigasyon** | ESP32/röle kontrolör + selenoid vanalar + venturi gübre emiş + asit pompası + hat içi EC/pH | Gübrenin doğru dozda ve pH'ta verilmesi (nötr-hafif bazik toprakta demir eksikliğini önler) |
| **Sulama hattı** | 2 debimetre + basınç sensörü | Tıkanma ve kaçak tespiti; m³/kg ölçümü |
| **Hasat** | NFC kartlı toplayıcı tartısı (kendi yapımın), terazi, QR etiket yazıcı | Toplayıcı ve sıra bazında kg; parça başı ödeme; lot izlenebilirliği |
| **Soğuk zincir** | 6 sıcaklık kayıt cihazı (logger) + soğuk oda sensörü | **Soğuk zincir kırıldı mı.** Raf ömrü ve ortağın kalite şikâyetlerine kanıt |
| **Güvenlik** | 1 solar 4G PTZ kamera | Hırsızlık ve uzaktan gözlem |
| **Sunucu** | Mini PC + UPS (sahada) | İnternet kesilse de sulama ve alarm çalışır |

**Yazılım (tamamı açık kaynak, lisans yok):**

- ChirpStack: LoRaWAN ağ sunucusu
- Mosquitto: MQTT mesajlaşma
- InfluxDB: zaman serisi veri tabanı
- Grafana: panel
- Node-RED: kurallar ve sulama mantığı
- Telegram botu: alarmlar sana ve babana
- Basit bir web sayfası: QR lot sayfası
- İsteğe bağlı: LLM ile otomatik günlük saha özeti (Claude API ile birkaç dolar/ay)

### 3.2 Bilinçli olarak kurulmayanlar

| Kurulmayan | Neden | Ne zaman tekrar düşünülür |
|---|---|---|
| Pakethane + top-seal makinesi | Tarlada kapaklı kaba toplama aynı kaliteyi verir | Ortak kendi markanla raf isterse |
| GES (güneş paneli) | Soğuk oda yalnızca 4-5 ay çalışıyor; tasarruf ~$1.000-1.200/yıl, geri dönüş ~7 yıl | Elektrik fiyatı ikiye katlanırsa |
| Termal kamera, meyve sayım ve sinek tuzağı kameraları | Kaliteye doğrudan etkisi yok; elle tuzak sayımı yeterli | 2029+ kârından, merak ve verimlilik için |
| Traktör | Hizmet alımı yılda ~$1.200 (20 da); traktör ~$25k | Hiçbir zaman (bu ölçekte) |
| Ofis konteyneri, çit | Konfor ve güvenlik; kaliteyi etkilemiyor | Hırsızlık yaşanırsa çit |
| Kalıcı teknisyen | Babanın desteği + yevmiyeli ekip | Baba destekleyemezse |
| Liyofilize, tünel, living lab | Ek gelir hedefi dışında | İsteğe bağlı, kârdan |

---

## 4. Yatırım (CAPEX): Kalem Kalem

### 4.1 20 dönüm (önerilen)

| Faz | Ne zaman | Grup | Kalem | Miktar | USD | TL |
|---|---|---|---|---|---:|---:|
| 0 | Q4-2026 / Q1-2027 | Arazi | Toprak analizi, dip kazan, lazer tesviye, 40 t/10 da gübre, sedde | 20 da | 8.316 | 390.852 |
| 0 | Q4-2026 / Q1-2027 | Arazi | Agrotekstil malç örtü (ot işçiliğini düşürür) | 6800 m² | 2.376 | 111.672 |
| 0 | Q4-2026 / Q1-2027 | Fidan | Sertifikalı doku kültürü fidan, sık dikim (%70 alan) | 6342 ad × $3,0 | 20.548 | 965.760 |
| 0 | Q4-2026 / Q1-2027 | Fidan | 2 yaşlı saksılı sertifikalı fidan, sık dikim (%30 alan) | 2718 ad × $6,5 | 19.081 | 896.828 |
| 0 | Q4-2026 / Q1-2027 | Fidan | Dikim işçiliği + kök uyarıcı |  | 1.296 | 60.912 |
| 0 | Q4-2026 / Q1-2027 | Telli sistem | Galvaniz direk 8 m aralık, 3 kat tel, ankraj, montaj |  | 15.444 | 725.868 |
| 0 | Q4-2026 / Q1-2027 | Sulama | Hidrant bağlantısı, disk filtre, ana hat, basınç ayarlı çift damla hattı | 13200 m | 5.292 | 248.724 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Fertigasyon: ESP32/röle kontrolör + selenoid vanalar + venturi + asit pompası + hat içi EC/pH |  | 2.160 | 101.520 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | LoRaWAN gateway + 4G router | 1 | 486 | 22.842 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Toprak düğümü: ESP32-LoRa + 2 endüstriyel RS485 nem/EC/sıcaklık probu + solar | 10 × $280 | 3.024 | 142.128 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Referans prob (kendi sensörlerinin kalibrasyonu) | 1 | 972 | 45.684 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Hobi-profesyonel meteoroloji istasyonu + yaprak ıslaklığı sensörü | 1 | 648 | 30.456 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Debimetre + basınç sensörü | 2 | 432 | 20.304 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Mini PC sunucu + UPS (ChirpStack, InfluxDB, Grafana, Node-RED) | 1 | 432 | 20.304 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Solar 4G PTZ güvenlik kamerası | 1 | 702 | 32.994 |
| 0 | Q4-2026 / Q1-2027 | Diğer | ÇKS, 5403 tarımsal yapı izni, proje |  | 648 | 30.456 |
| 1 | 2027 sonu | Soğuk zincir | 40' reefer konteyner, yenilenmiş (0/+2 °C) | 1 | 9.180 | 431.460 |
| 1 | 2027 sonu | Soğuk zincir | Ön soğutma tüneli (fan + branda + termostat, kendi yapımın) | 1 | 1.080 | 50.760 |
| 1 | 2027 sonu | Soğuk zincir | Trifaze elektrik bağlantısı + pano |  | 3.780 | 177.660 |
| 1 | 2027 sonu | Soğuk zincir | Stabilize zemin + basit gölgelik |  | 1.620 | 76.140 |
| 1 | 2027 sonu | Soğuk zincir | NFC kartlı toplayıcı tartısı (kendi yapımın) + terazi + QR etiket yazıcı + 6 logger |  | 972 | 45.684 |
| 1 | 2027 sonu | Soğuk zincir | Hasat kasaları + el arabaları |  | 1.527 | 71.785 |
| 1 | 2027 sonu | Soğuk zincir | Gıda işletme kaydı + İyi Tarım belgesi |  | 1.080 | 50.760 |
| 1 | 2027 sonu | Kalite | %35 gölge filesi (güneş yanığına karşı) + montaj |  | 8.208 | 385.776 |
| 2 | 2030 sonu (kârdan) | Kârdan | Şok dondurucu + 2. reefer (-20 °C): 2. sınıf ürün IQF |  | 24.300 | 1.142.100 |
| | | | **Faz 0 — kurulum toplamı** | | **81.858** | **3.847.303** |
| | | | **Faz 1 — ilk büyük hasattan önce toplamı** | | **27.447** | **1.290.025** |
| | | | **Faz 2 — kârdan toplamı** | | **24.300** | **1.142.100** |
| | | | **Başlangıç yatırımı (Faz 0 + 1)** | | **109.305** | **5.137.329** |

*Tutarlar %8 beklenmeyen gider payı dahildir.*

### 4.2 10 dönüm

| Faz | Ne zaman | Grup | Kalem | Miktar | USD | TL |
|---|---|---|---|---|---:|---:|
| 0 | Q4-2026 / Q1-2027 | Arazi | Toprak analizi, dip kazan, lazer tesviye, 40 t/10 da gübre, sedde | 10 da | 4.158 | 195.426 |
| 0 | Q4-2026 / Q1-2027 | Arazi | Agrotekstil malç örtü (ot işçiliğini düşürür) | 3400 m² | 1.188 | 55.836 |
| 0 | Q4-2026 / Q1-2027 | Fidan | Sertifikalı doku kültürü fidan, sık dikim (%70 alan) | 3171 ad × $3,0 | 10.274 | 482.880 |
| 0 | Q4-2026 / Q1-2027 | Fidan | 2 yaşlı saksılı sertifikalı fidan, sık dikim (%30 alan) | 1359 ad × $6,5 | 9.541 | 448.414 |
| 0 | Q4-2026 / Q1-2027 | Fidan | Dikim işçiliği + kök uyarıcı |  | 648 | 30.456 |
| 0 | Q4-2026 / Q1-2027 | Telli sistem | Galvaniz direk 8 m aralık, 3 kat tel, ankraj, montaj |  | 7.722 | 362.934 |
| 0 | Q4-2026 / Q1-2027 | Sulama | Hidrant bağlantısı, disk filtre, ana hat, basınç ayarlı çift damla hattı | 6600 m | 2.646 | 124.362 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Fertigasyon: ESP32/röle kontrolör + selenoid vanalar + venturi + asit pompası + hat içi EC/pH |  | 2.160 | 101.520 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | LoRaWAN gateway + 4G router | 1 | 486 | 22.842 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Toprak düğümü: ESP32-LoRa + 2 endüstriyel RS485 nem/EC/sıcaklık probu + solar | 6 × $280 | 1.814 | 85.277 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Referans prob (kendi sensörlerinin kalibrasyonu) | 1 | 972 | 45.684 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Hobi-profesyonel meteoroloji istasyonu + yaprak ıslaklığı sensörü | 1 | 648 | 30.456 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Debimetre + basınç sensörü | 2 | 432 | 20.304 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Mini PC sunucu + UPS (ChirpStack, InfluxDB, Grafana, Node-RED) | 1 | 432 | 20.304 |
| 0 | Q4-2026 / Q1-2027 | Teknoloji (kendi yapımın) | Solar 4G PTZ güvenlik kamerası | 1 | 702 | 32.994 |
| 0 | Q4-2026 / Q1-2027 | Diğer | ÇKS, 5403 tarımsal yapı izni, proje |  | 648 | 30.456 |
| 1 | 2027 sonu | Soğuk zincir | 40' reefer konteyner, yenilenmiş (0/+2 °C) | 1 | 9.180 | 431.460 |
| 1 | 2027 sonu | Soğuk zincir | Ön soğutma tüneli (fan + branda + termostat, kendi yapımın) | 1 | 1.080 | 50.760 |
| 1 | 2027 sonu | Soğuk zincir | Trifaze elektrik bağlantısı + pano |  | 3.780 | 177.660 |
| 1 | 2027 sonu | Soğuk zincir | Stabilize zemin + basit gölgelik |  | 1.620 | 76.140 |
| 1 | 2027 sonu | Soğuk zincir | NFC kartlı toplayıcı tartısı (kendi yapımın) + terazi + QR etiket yazıcı + 6 logger |  | 972 | 45.684 |
| 1 | 2027 sonu | Soğuk zincir | Hasat kasaları + el arabaları |  | 1.080 | 50.760 |
| 1 | 2027 sonu | Soğuk zincir | Gıda işletme kaydı + İyi Tarım belgesi |  | 1.080 | 50.760 |
| 1 | 2027 sonu | Kalite | %35 gölge filesi (güneş yanığına karşı) + montaj |  | 4.104 | 192.888 |
| | | | **Faz 0 — kurulum toplamı** | | **44.471** | **2.090.145** |
| | | | **Faz 1 — ilk büyük hasattan önce toplamı** | | **22.896** | **1.076.112** |
| | | | **Başlangıç yatırımı (Faz 0 + 1)** | | **67.367** | **3.166.257** |

*Tutarlar %8 beklenmeyen gider payı dahildir.*

**20 dönümün başlangıç yatırımı nereye gidiyor:** fidan %37 · soğuk zincir %18 · telli sistem %14 · arazi hazırlığı %10 · teknoloji %8 · gölge filesi %8 · sulama %5.

**Şok dondurucu (yalnız 20 da, 2030 kârından):** 20 dönümde yılda ~8 t 2. sınıf ürün çıkıyor. Bu ürün işleme tesisine $1,30/kg yerine IQF olarak $2,80/kg'a satılıyor; yatırım ~3,5 yılda geri dönüyor. 10 dönümde gerek yok.

---

## 5. İşletme Giderleri (OPEX)

### 5.1 Sabit giderler — 20 dönüm

| Sabit gider (USD/yıl) | 2027 | 2028 | 2029 | 2030 | 2031+ |
|---|---:|---:|---:|---:|---:|
| Gübre + mücadele (biyolojik öncelikli) | 2.200 | 4.000 | 5.600 | 6.000 | 6.000 |
| Budama, bağlama, ot (yevmiyeli) | 2.600 | 4.600 | 5.800 | 6.000 | 6.000 |
| Traktör/ilaçlama hizmet alımı | 800 | 1.200 | 1.200 | 1.200 | 1.200 |
| DSİ su ücreti | 500 | 800 | 1.000 | 1.000 | 1.000 |
| Sezonluk saha işçisi (Mart-Ekim, yalnız 20 da) | 3.000 | 6.000 | 6.000 | 6.000 | 6.000 |
| Sezonluk soğuk oda/etiket yardımcısı | 0 | 1.697 | 2.121 | 2.121 | 2.121 |
| Elektrik (soğuk oda, pompa) | 100 | 1.000 | 1.200 | 1.200 | 2.100 |
| Bakım-onarım | 283 | 849 | 1.131 | 1.273 | 1.414 |
| TARSİM sigortası | 0 | 975 | 1.300 | 1.462 | 1.625 |
| SIM/4G + bulut yedeği | 150 | 150 | 150 | 150 | 150 |
| Gıda güvenliği/kalıntı analizi | 0 | 400 | 400 | 400 | 400 |
| Arı kovanı kiralama | 0 | 600 | 600 | 600 | 600 |
| Muhasebe (çiftçi) | 400 | 400 | 400 | 400 | 400 |
| Kurucu ulaşımı (Ankara) | 3.000 | 3.000 | 3.000 | 3.000 | 3.000 |
| Baba: yakıt/harcırah | 800 | 800 | 800 | 800 | 800 |
| **Toplam** | **13.833** | **26.470** | **30.702** | **31.606** | **32.810** |

### 5.2 Sabit giderler — 10 dönüm

| Sabit gider (USD/yıl) | 2027 | 2028 | 2029 | 2030 | 2031+ |
|---|---:|---:|---:|---:|---:|
| Gübre + mücadele (biyolojik öncelikli) | 1.100 | 2.000 | 2.800 | 3.000 | 3.000 |
| Budama, bağlama, ot (yevmiyeli) | 1.300 | 2.300 | 2.900 | 3.000 | 3.000 |
| Traktör/ilaçlama hizmet alımı | 400 | 600 | 600 | 600 | 600 |
| DSİ su ücreti | 250 | 400 | 500 | 500 | 500 |
| Sezonluk soğuk oda/etiket yardımcısı | 0 | 1.200 | 1.500 | 1.500 | 1.500 |
| Elektrik (soğuk oda, pompa) | 100 | 1.000 | 1.200 | 1.200 | 1.200 |
| Bakım-onarım | 200 | 600 | 800 | 900 | 1.000 |
| TARSİM sigortası | 0 | 600 | 800 | 900 | 1.000 |
| SIM/4G + bulut yedeği | 150 | 150 | 150 | 150 | 150 |
| Gıda güvenliği/kalıntı analizi | 0 | 400 | 400 | 400 | 400 |
| Arı kovanı kiralama | 0 | 300 | 300 | 300 | 300 |
| Muhasebe (çiftçi) | 400 | 400 | 400 | 400 | 400 |
| Kurucu ulaşımı (Ankara) | 3.000 | 3.000 | 3.000 | 3.000 | 3.000 |
| Baba: yakıt/harcırah | 800 | 800 | 800 | 800 | 800 |
| **Toplam** | **7.700** | **13.750** | **16.150** | **16.650** | **16.850** |

### 5.3 Değişken giderler (kg başı)

| Kalem | Değer |
|---|---|
| Hasat işçiliği: tarlada kaba toplama / dökme | $0,70 / $0,55 |
| Kapaklı PET kap + etiket + koli | $0,65 |
| Soğuk odada etiket/koli işçiliği | $0,06 |
| Bursa'ya soğuk teslimat (ortak teslim alırsa düşer) | $0,25 |
| Satış ortağı komisyonu | Satış fiyatının %18'i |
| Hal / dökme satış gideri | $0,45 |

---

## 6. 10 Yıllık Gelir, Kâr ve Nakit

### 6.1 20 dönüm

| USD | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rekolte (t) | 2,9 | 20,2 | 35,8 | 40,0 | 40,0 | 40,0 | 40,0 | 40,0 | 36,0 | 32,0 |
| **Gelir (ortak komisyonu düşülmüş)** | **9.657** | **71.529** | **129.826** | **145.057** | **157.057** | **157.057** | **157.057** | **157.057** | **141.352** | **125.646** |
| Değişken gider (hasat, kap, teslimat, kanal) | −3.660 | −26.745 | −48.344 | −54.016 | −57.616 | −57.616 | −57.616 | −57.616 | −51.854 | −46.093 |
| Sabit gider | −13.833 | −26.470 | −30.702 | −31.606 | −32.810 | −32.810 | −32.810 | −32.810 | −32.810 | −32.810 |
| **FAVÖK** | **−7.835** | **18.314** | **50.780** | **59.435** | **66.631** | **66.631** | **66.631** | **66.631** | **56.687** | **46.743** |
| Amortisman | −9.395 | −12.832 | −12.832 | −12.832 | −15.424 | −13.134 | −12.702 | −12.702 | −12.230 | −12.230 |
| **Vergi öncesi kâr** | **−17.231** | **5.482** | **37.948** | **46.603** | **51.207** | **53.497** | **53.929** | **53.929** | **44.457** | **34.513** |
| Stopaj (%2) | −193 | −1.431 | −2.597 | −2.901 | −3.141 | −3.141 | −3.141 | −3.141 | −2.827 | −2.513 |
| **Net kâr** | **−17.424** | **4.051** | **35.351** | **43.702** | **48.066** | **50.356** | **50.788** | **50.788** | **41.630** | **32.000** |
| Aylık ortalama net kâr (TL) | −68.243 | 15.868 | 138.459 | 171.167 | 188.260 | 197.227 | 198.919 | 198.919 | 163.052 | 125.335 |
| Yatırım / yenileme | −27.447 | 0 | 0 | −24.300 | 0 | −2.500 | 0 | −4.900 | 0 | 0 |
| **Kümülatif nakit (Y0 dahil)** | **−117.333** | **−100.450** | **−52.267** | **−20.033** | **43.457** | **104.447** | **167.937** | **226.527** | **280.388** | **331.964** |

### 6.2 10 dönüm

| USD | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rekolte (t) | 1,5 | 10,1 | 17,9 | 20,0 | 20,0 | 20,0 | 20,0 | 20,0 | 18,0 | 16,0 |
| **Gelir (ortak komisyonu düşülmüş)** | **4.829** | **35.764** | **64.913** | **72.529** | **72.529** | **72.529** | **72.529** | **72.529** | **65.276** | **58.023** |
| Değişken gider (hasat, kap, teslimat, kanal) | −1.830 | −13.372 | −24.172 | −27.008 | −27.008 | −27.008 | −27.008 | −27.008 | −24.307 | −21.606 |
| Sabit gider | −7.700 | −13.750 | −16.150 | −16.650 | −16.850 | −16.850 | −16.850 | −16.850 | −16.850 | −16.850 |
| **FAVÖK** | **−4.701** | **8.642** | **24.591** | **28.871** | **28.671** | **28.671** | **28.671** | **28.671** | **24.119** | **19.567** |
| Amortisman | −5.417 | −8.178 | −8.178 | −8.178 | −8.070 | −6.260 | −5.917 | −5.917 | −6.031 | −6.031 |
| **Vergi öncesi kâr** | **−10.118** | **464** | **16.413** | **20.693** | **20.601** | **22.411** | **22.753** | **22.753** | **18.088** | **13.536** |
| Stopaj (%2) | −97 | −715 | −1.298 | −1.451 | −1.451 | −1.451 | −1.451 | −1.451 | −1.306 | −1.160 |
| **Net kâr** | **−10.215** | **−251** | **15.115** | **19.242** | **19.150** | **20.961** | **21.303** | **21.303** | **16.782** | **12.375** |
| Aylık ortalama net kâr (TL) | −40.008 | −983 | 59.201 | 75.366 | 75.006 | 82.095 | 83.436 | 83.436 | 65.730 | 48.469 |
| Yatırım / yenileme | −22.896 | 0 | 0 | 0 | 0 | −2.500 | 0 | −4.900 | 0 | 0 |
| **Kümülatif nakit (Y0 dahil)** | **−72.165** | **−64.238** | **−40.945** | **−13.525** | **13.695** | **38.415** | **65.635** | **87.955** | **110.768** | **132.470** |

**Notlar:**

- Vergi: gerçek kişi çiftçi statüsünde ürün satışında %2 stopaj (nihai vergi). Mali müşavirle teyit edilmeli.
- 2036 sonunda tesisin net defter değerinin yarısı kalıntı değer olarak eklendi.
- Ziraat Hazine faiz destekli kredi kullanılırsa (Faz 0-1'in %50'si, 2+3 yıl), cepten çıkan en yüksek tutar 20 dönümde $117k'dan $69k'ya iner (Özet tablosu).

### 6.3 Neden v3'ten (%9,5-15) çok daha iyi görünüyor?

| Fark | v3 | v6 | Etki (20 da, yıllık) |
|---|---|---|---:|
| Kalıcı teknisyen + daimi işçi | Var | Yok (baba + sezonluk 1 kişi) | ~+$12.000 |
| Pakethane, marka, pazarlama, şirket gideri | Var | Yok (ortak satıyor, çiftçi statüsü) | ~+$8.000 |
| Kurumlar vergisi %25 | Var | %2 stopaj | Kâr arttıkça büyür |
| Satış hızı | Kanal yıllar içinde oluşuyor | Ortak 2028'den olgun karmayla alıyor | Erken gelir |
| Living lab, danışmanlık, GES, liyofilize, kameralar | Var | Yok | 10 yıllık yatırım ~−%27 |

**Dürüst uyarı:** Bu farkın büyük kısmı iki varsayımdan geliyor: **satış ortağının ürünü gerçekten alması** ve **babanın emeğinin ücretsiz olması**. İkisi gerçekleşmezse sonuçlar v3'e yaklaşır.

---

## 7. Stres Testi (20 dönüm)

| Senaryo | 2031 net kâr | Geri dönüş | 10 yıl IRR |
|---|---:|---:|---:|
| Baz | $48.066 | 4,3 yıl | %27,4 |
| Fiyat −%20 | $17.283 | 6,8 yıl | %9,2 |
| Verim −%25 | $23.991 | 5,9 yıl | %13,9 |
| Hasat işçiliği +%35 (TEKNOSAB etkisi) | $39.022 | 4,8 yıl | %22,5 |
| Ortak komisyonu %25 | $38.140 | 4,8 yıl | %22,1 |
| Fiyat −%20 + verim −%15 + işçilik +%20 | $3.063 | dönmez | −%3,5 |

- **En kritik değişken fiyat.** %20 fiyat düşüşü getiriyi %27'den %9'a indiriyor. Bu yüzden ortak sözleşmesinde **taban fiyat** (örneğin 250 g kap için üretici çıkışında TL taban, yıllık enflasyon endeksli) olmazsa olmaz.
- **İşçilik ve komisyon artışı yönetilebilir.** TEKNOSAB'ın işgücü baskısı (+%35) getiriyi %22'ye indiriyor, ama proje kârlı kalıyor.
- **Üçlü şok** (fiyat −%20, verim −%15, işçilik +%20) birlikte gelirse yatırım 10 yılda geri dönmüyor. v3'teki önlemler (gölge filesi, sigorta, 3 çeşit, sık hasat) ve bu plandaki soğuk zincir bu ihtimali düşürüyor.

---

## 8. Kimin Ne Zaman Ne Yaptığı (zaman bütçesi)

| Kişi | Görev | Yıllık zaman (tahmin) |
|---|---|---|
| **Sen** | Sistem kurulumu (2027 kışı yoğun), haftalık veri kontrolü, ortakla planlama, sezon kararları, muhasebe | Uzaktan haftada 3-4 saat + ~25 ziyaret (sezonda 3-4 günlük kalışlar). Kurulum yılı ~300 saat, sonraki yıllar ~200-250 saat |
| **Baban** | Sahada göz: ekip denetimi, sulama/alarm kontrolü, hasat günlerinde soğuk oda ve teslim | Sezon dışı haftada 1 gün, haziran-ekim haftada 3-4 gün |
| **Dayıbaşı + yevmiyeli ekip** | Budama (ocak-şubat), bağlama, ot, hasat | 20 da tepe hasatta 8-10 kişi, 10 da'da 4-5 kişi |
| **Sezonluk saha işçisi (20 da)** | Günlük saha işi, sulama kontrolü | Mart-ekim |
| **Sezonluk yardımcı** | Soğuk oda, etiket, koli | Haziran-ekim |
| **Ziraat danışmanı** | Budama, gübre, hastalık kararlarına ikinci göz | Sezonda ayda 1 (ücreti bakım/gübre bütçesinden) |

Ay ay iş takvimi v3 Bölüm 3'te; bu planda yalnız pakethane ve ofis işleri yok.

---

## 9. Kârdan Eklenecekler: Karar Kuralları

| Ne | Ne zaman | Karar kuralı |
|---|---|---|
| Şok dondurucu + -20 °C depo (20 da) | 2030 sonu | 2. sınıf ürün ≥ 6 t/yıl ve IQF alıcısı bulunduysa |
| Sinek tuzağı (SWD) + sıra kameraları | 2029+ | Sinek kaybı %5'i geçtiyse veya rekolte tahmini ortak için kritikse |
| Tünel (1-2 da pilot) | 2029+ | Ortak eylül-ekim ürününe ≥ %20 prim veriyorsa |
| Pakethane / kendi marka | 2030+ | Ortak kendi markanla raf istiyorsa ve hacim ≥ 30 t ise |
| GES | – | Elektrik gideri yılda $2.500'ü geçerse |

**Genel kural:** Bir yılın serbest nakdinin en fazla yarısı yeni yatırıma gider; kalanı sana ek gelir olarak döner.

---

## 10. İlk 90 Gün

| Hafta | İş |
|---|---|
| 1-2 | Satış ortağıyla sözleşme taslağı (tonaj, taban fiyat, komisyon, teslim, vade). Arazide toprak analizi |
| 2-4 | Fidanlıklardan teklif: doku kültürü (3 çeşit) ve 2 yaşlı saksılı fidan (adet, saksı hacmi, kol sayısı, virüs sertifikası). ÇKS kaydı, Ziraat kredi ön görüşmesi (faiz desteği 31.12.2026 bitiyor) |
| 4-6 | Dip kazan, tesviye, gübre, sedde (kış yağmurlarından önce). TEDAŞ trifaze keşfi |
| 6-10 | Telli sistem ve ana sulama hattı. Sensör ve kontrolör siparişleri; evde ilk prototip (2 düğüm + gateway + Grafana) |
| 10-13 | Yazılım ve alarm kuralları, babanla Telegram alarm denemesi. Dayıbaşıyla 2027 iş takvimi. Dikim Mart sonu – Nisan |

---

## 11. Sonuç

1. **Ek gelir hedefi için doğru büyüklük 20 dönüm, doğru dikim hibrit.** Başlangıç yatırımı **$109.305 (≈5,1 M TL)**, cepten çıkan en yüksek tutar $117.333; Ziraat kredisiyle ~$69k.
2. **2028'de 20 t hasat ve kâra geçiş; 2031'den itibaren yılda ~$48k (≈2,3 M TL) net**, aylık ~188 bin TL. Yatırım 4,3 yılda geri dönüyor.
3. **Teknoloji kaliteyi belirleyen dört karar için kuruluyor:** sulama, ilaçlama, hasat zamanlaması, soğuk zincir. Toplam teknoloji bütçesi ~$9-10k ve yazılımın tamamı açık kaynak, kendi yapımın.
4. **Planın ayakta durması için:** ortakla taban fiyatlı yazılı sözleşme ve babanın düzenli desteği.

---

### Ek — Varsayımlar ve kaynaklar

| Varsayım | Değer |
|---|---|
| Fidan fiyatı | Doku kültürü $3,0/ad, 2 yaşlı saksılı $6,5/ad (**tahmin, teklif alınmalı**) |
| Verim | Doku kültürü 0,6 / 8 / 17 / 20 t; saksılı 3,5 / 15 / 20 / 20 t (10 da başına, sık dikim) |
| Satış | 1. sınıfın %60 → %80'i ortak üzerinden paketli ($5,65/kg, %18 komisyon), kalanı hal; 2. sınıf işleme ($1,30) veya IQF ($2,80) |
| Ekipman fiyatları | 2026 Türkiye piyasası tahminleri; her kalem için en az 3 teklif |
| Kur | 1 USD = 47 TL (Ekim 2026 çalışma kuru) |
| Hariç | Arazi kirası (arazi senin), kurucu ve baba emeğinin ücreti, olası Ziraat kredisi faizi (Özet'te ayrıca gösterildi) |

Tarımsal veriler, risk analizi ve bölge bilgileri için v1-v4 raporları; kredi kaynakları v1 Ek B.
