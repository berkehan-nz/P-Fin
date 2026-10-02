# Muratlı Böğürtlen — Fizibilite v7: 10 Dönüm Ek Gelir Planı (Yalın Hibrit)

**Amaç:** Tesis veya uzun vadeli vizyon değil, kurucuya **ek gelir** üreten **10 dönümlük** bir bahçe. En az yatırım (CAPEX) ve işletme gideriyle (OPEX) en çok kaliteli üretim. Kalite için gereken teknoloji korunuyor ve kurucu tarafından kendisi kuruluyor.
**Kurgu:** Satışı bir iş ortağı yapıyor (%18 komisyon). Saha işi kurucu (Ankara'dan ziyaret), baba (Bursa) ve yevmiyeli ekiple yürüyor; sabit veya sezonluk saha personeli yok. Traktör hizmeti satın alınıyor. Pakethane yok; ürün tarlada kapaklı kaba toplanıyor.
**Lokasyon:** Bursa / Karacabey / Muratlı · **Tarih:** 2 Ekim 2026 · **Para birimi:** 2026 sabit USD; 1 USD = 47 TL
**Hesap modeli:** [`model_v6.py`](model_v6.py) (`--tables` ile bütün tablolar yeniden üretilir)

> v6'nın 10 dönüme uyarlanmış hâli. 10 dönümün tepe hasat yükü (~300 kg/gün) için soğuk depo 40' yerine **20' reefer** olarak küçültüldü. Rapor v1-v5'teki tarım, risk ve bölge analizlerine dayanıyor; kapsamı bilinçli olarak daraltıyor. Çıkarılanlar: test sahası (living lab), danışmanlık, liyofilize makinesi, pakethane, kalıcı teknisyen, şirket yapısı. Mevsim riski simülasyonu ve TEKNOSAB/imar analizi için v3 ve v4'e bakılabilir.

---

## 0. Özet

| Gösterge | 10 da | 20 da |
|---|---:|---:|
| Başlangıç yatırımı (Faz 0 + 1) | $64.127 (3,0 M TL) | $109.305 (5,1 M TL) |
| Cepten çıkan en yüksek tutar (işletme açıkları dahil) | $68.925 (3,2 M TL) | $117.333 (5,5 M TL) |
| — Ziraat faiz destekli kredi (%50) ile | $40.347 (1,9 M TL) | $69.098 (3,2 M TL) |
| 2028 rekolte / net kâr | 10,1 t / $73 | 20,2 t / $4.051 |
| 2031 rekolte / net kâr | 20,0 t / $19.474 | 40,0 t / $48.066 |
| 2031 aylık ortalama ek gelir (net) | 76.275 TL | 188.260 TL |
| 5 yıl toplam net kâr | $44.338 | $113.747 |
| 10 yıl toplam net kâr | $138.682 | $339.310 |
| Geri dönüş (Y0'dan) | 4,4 yıl | 4,3 yıl |
| 10 yıllık IRR / NPV (%12) | %22,6 / $38.478 | %27,4 / $110.045 |

**Plan: 10 dönüm, hibrit dikim, 2027 ilkbaharı.** 20 dönüm sütunu yalnızca karşılaştırma için.

- **Başlangıç yatırımı $64.127 (≈3,0 M TL).** Ziraat faiz destekli krediyle cepten çıkan en yüksek tutar $40.347 (≈1,9 M TL).
- **2028'de 10 t hasat ve başabaş; 2029'dan itibaren yılda ~$15-21k net.** 2031'de aylık ortalama **~76 bin TL** net ek gelir.
- **4,4 yılda geri dönüş**, 10 yıllık getiri (IRR) %22,6, 10 yılda toplam net kâr $138.682.
- **Hibrit dikim (%70 doku kültürü, %30 2 yaşlı saksılı fidan):** 2028'de tam verimin yarısı (10 t). Tamamı saksılı fidana göre fidan bütçesi ~$12k düşük.
- **20 dönüme büyüme seçeneği açık:** 2028 sezonu hedefi tutarsa ikinci 10 dönüm 2029 ilkbaharında ~$45k ek yatırımla dikilebilir (Bölüm 9).

**10 dönümün zayıf yanı: daha kırılgan.** Sabit giderler (ulaşım, soğuk depo, sensörler) küçük alana bölündüğü için fiyat ve emek şoklarına 20 dönümden daha duyarlı (Bölüm 7).

**Bu sonuçlar iki şarta bağlı:**

1. **Satış ortağıyla yazılı ve taahhütlü sözleşme:** minimum yıllık alım tonajı, taban fiyat, komisyon, ürünü soğuk depodan teslim alma, ödeme vadesi.
2. **Babanın düzenli saha desteği.** Olmazsa yerine ücretli bir saha şefi gerekir (~$9k/yıl). 10 dönümde bu, 2031 net kârının **~%46'sı** demek; ek gelir neredeyse yarıya iner.

---

## 1. Tasarım İlkeleri

| İlke | Uygulama |
|---|---|
| **Kaliteyi belirleyen şeye para harca** | Sertifikalı fidan, damla + fertigasyon, ön soğutma + soğuk depo, gölge filesi, toprak/iklim ölçümü |
| **Kaliteyi belirlemeyen şeyi erte veya kirala** | Pakethane, traktör, ofis konteyneri, çit, GES, termal kamera, meyve sayım kameraları, liyofilize: hepsi yok ya da kârdan sonra |
| **Teknolojiyi kendin kur, açık kaynakla çalıştır** | Endüstriyel sensör + ESP32/LoRa; sunucuda açık kaynak yazılım; lisans ve abonelik yok |
| **Her teknoloji bir kararı beslemeli** | Sulama ne zaman, ilaç ne zaman, hasat ne zaman, soğuk zincir kırıldı mı. Bu dört soruya cevap vermeyen hiçbir şey kurulmuyor |
| **Giderler değişken olsun** | Hasat, budama, traktör: iş varken ödeniyor. Sabit ya da sezonluk personel yok |

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

Üç çeşitle hasat haziran ortasından ekim sonuna yayılıyor (v3 Bölüm 1-3). Bu, tepe işçi ihtiyacını (4-5 toplayıcı) ve soğuk depo yükünü (~300 kg/gün) düşürüyor; 20' reefer'ın yetmesinin nedeni bu.

---

## 3. Teknoloji: Kendi Kuracağın Sistem

### 3.1 Ne kuruluyor?

| Katman | Bileşen | Neden şart (hangi kararı besliyor) |
|---|---|---|
| **Toprak** | 6 düğüm. Her düğümde ESP32-LoRa kart, 30 ve 60 cm'de 2 endüstriyel RS485 nem/EC/sıcaklık probu, küçük güneş paneli + akü | **Ne zaman ve ne kadar sulama.** Böğürtlen ağır toprakta kök boğulmasına hassas; hem kuraklık hem fazla su kaliteyi düşürür |
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
| Traktör | Hizmet alımı yılda ~$600; traktör ~$25k | Hiçbir zaman (bu ölçekte) |
| Ofis konteyneri, çit | Konfor ve güvenlik; kaliteyi etkilemiyor | Hırsızlık yaşanırsa çit |
| Kalıcı teknisyen | Babanın desteği + yevmiyeli ekip | Baba destekleyemezse |
| Şok dondurucu (IQF) | 10 da'da yılda ~4 t 2. sınıf ürün; ek kazanç ~$3.300/yıl, $24k yatırımın geri dönüşü ~7 yıl | 20 dönüme büyürse |
| Liyofilize, tünel, living lab | Ek gelir hedefi dışında | İsteğe bağlı, kârdan |

---

## 4. Yatırım (CAPEX): Kalem Kalem

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
| 1 | 2027 sonu | Soğuk zincir | 20' reefer konteyner, yenilenmiş (0/+2 °C; 10 da tepe yükü ~300 kg/gün) | 1 | 5.940 | 279.180 |
| 1 | 2027 sonu | Soğuk zincir | Ön soğutma tüneli (fan + branda + termostat, kendi yapımın) | 1 | 1.080 | 50.760 |
| 1 | 2027 sonu | Soğuk zincir | Trifaze elektrik bağlantısı + pano |  | 3.780 | 177.660 |
| 1 | 2027 sonu | Soğuk zincir | Stabilize zemin + basit gölgelik |  | 1.620 | 76.140 |
| 1 | 2027 sonu | Soğuk zincir | NFC kartlı toplayıcı tartısı (kendi yapımın) + terazi + QR etiket yazıcı + 6 logger |  | 972 | 45.684 |
| 1 | 2027 sonu | Soğuk zincir | Hasat kasaları + el arabaları |  | 1.080 | 50.760 |
| 1 | 2027 sonu | Soğuk zincir | Gıda işletme kaydı + İyi Tarım belgesi |  | 1.080 | 50.760 |
| 1 | 2027 sonu | Kalite | %35 gölge filesi (güneş yanığına karşı) + montaj |  | 4.104 | 192.888 |
| | | | **Faz 0 — kurulum toplamı** | | **44.471** | **2.090.145** |
| | | | **Faz 1 — ilk büyük hasattan önce toplamı** | | **19.656** | **923.832** |
| | | | **Başlangıç yatırımı (Faz 0 + 1)** | | **64.127** | **3.013.977** |

*Tutarlar %8 beklenmeyen gider payı dahildir.*

**Başlangıç yatırımı nereye gidiyor:** fidan %32 · soğuk zincir %24 · telli sistem %12 · teknoloji %12 · arazi hazırlığı %8 · gölge filesi %6 · sulama %4.

**Soğuk zincir, 10 dönümde payı en yüksek ikinci kalem.** Reefer + ön soğutma + trifaze bağlantı ~$15,6k ediyor. Arazide trifaze hat varsa ya da ürünü ortak her gün tarladan teslim alıyorsa bu kalem küçülebilir. Ama ön soğutmasız böğürtlenin raf ömrü 2-3 gün; kaliteyi koruyan en önemli yatırım bu.

---

## 5. İşletme Giderleri (OPEX)

### 5.1 Sabit giderler

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

### 5.2 Değişken giderler (kg başı)

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

| USD | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rekolte (t) | 1,5 | 10,1 | 17,9 | 20,0 | 20,0 | 20,0 | 20,0 | 20,0 | 18,0 | 16,0 |
| **Gelir (ortak komisyonu düşülmüş)** | **4.829** | **35.764** | **64.913** | **72.529** | **72.529** | **72.529** | **72.529** | **72.529** | **65.276** | **58.023** |
| Değişken gider (hasat, kap, teslimat, kanal) | −1.830 | −13.372 | −24.172 | −27.008 | −27.008 | −27.008 | −27.008 | −27.008 | −24.307 | −21.606 |
| Sabit gider | −7.700 | −13.750 | −16.150 | −16.650 | −16.850 | −16.850 | −16.850 | −16.850 | −16.850 | −16.850 |
| **FAVÖK** | **−4.701** | **8.642** | **24.591** | **28.871** | **28.671** | **28.671** | **28.671** | **28.671** | **24.119** | **19.567** |
| Amortisman | −5.417 | −7.854 | −7.854 | −7.854 | −7.746 | −5.936 | −5.593 | −5.593 | −5.707 | −5.707 |
| **Vergi öncesi kâr** | **−10.118** | **788** | **16.737** | **21.017** | **20.925** | **22.735** | **23.077** | **23.077** | **18.412** | **13.860** |
| Stopaj (%2) | −97 | −715 | −1.298 | −1.451 | −1.451 | −1.451 | −1.451 | −1.451 | −1.306 | −1.160 |
| **Net kâr** | **−10.215** | **73** | **15.439** | **19.566** | **19.474** | **21.285** | **21.627** | **21.627** | **17.106** | **12.699** |
| Aylık ortalama net kâr (TL) | −40.008 | 286 | 60.470 | 76.635 | 76.275 | 83.364 | 84.705 | 84.705 | 66.999 | 49.738 |
| Yatırım / yenileme | −19.656 | 0 | 0 | 0 | 0 | −2.500 | 0 | −4.900 | 0 | 0 |
| **Kümülatif nakit (Y0 dahil)** | **−68.925** | **−60.998** | **−37.705** | **−10.285** | **16.935** | **41.655** | **68.875** | **91.195** | **114.008** | **135.548** |

**Notlar:**

- Vergi: gerçek kişi çiftçi statüsünde ürün satışında %2 stopaj (nihai vergi). Mali müşavirle teyit edilmeli.
- 2036 sonunda tesisin net defter değerinin yarısı kalıntı değer olarak eklendi.
- Ziraat Hazine faiz destekli kredi kullanılırsa (Faz 0-1'in %50'si, 2+3 yıl), cepten çıkan en yüksek tutar $68.925'ten $40.347'ye iner.

### Neden v3'ten (10 da IRR %9,5) çok daha iyi görünüyor?

| Fark | v3 | v7 | Etki (10 da, yıllık) |
|---|---|---|---:|
| Kalıcı teknisyen | Var | Yok (baba + yevmiyeli) | ~+$9.000 |
| Pakethane, marka, pazarlama, şirket gideri | Var | Yok (ortak satıyor, çiftçi statüsü) | ~+$6.000 |
| Kurumlar vergisi %25 | Var | %2 stopaj | Kâr arttıkça büyür |
| Satış hızı | Kanal yıllar içinde oluşuyor | Ortak 2028'den olgun karmayla alıyor | Erken gelir |
| Living lab, danışmanlık, GES, dondurucu, kameralar, 40' reefer | Var | Yok | 10 yıllık yatırım ~−%47 |

**Dürüst uyarı:** Bu farkın büyük kısmı iki varsayımdan geliyor: **satış ortağının ürünü gerçekten alması** ve **babanın emeğinin ücretsiz olması**. İkisi gerçekleşmezse sonuçlar v3'e yaklaşır.

---

## 7. Stres Testi

| Senaryo | 2031 net kâr | Geri dönüş | 10 yıl IRR |
|---|---:|---:|---:|
| Baz | $19.474 | 4,4 yıl | %22,6 |
| Fiyat −%20 | $5.259 | 8,1 yıl | %4,4 |
| Verim −%25 | $8.457 | 6,5 yıl | %9,3 |
| Hasat işçiliği +%35 (TEKNOSAB etkisi) | $14.952 | 4,9 yıl | %17,7 |
| Ortak komisyonu %25 | $14.511 | 5,0 yıl | %17,2 |
| Fiyat −%20 + verim −%15 + işçilik +%20 | −$1.416 | dönmez | −%10,2 |

- **En kritik değişken fiyat.** %20 fiyat düşüşü getiriyi %22,6'dan %4,4'e indiriyor; geri dönüş 8 yılı buluyor. 10 dönümde ortak sözleşmesindeki **taban fiyat** (örneğin 250 g kap için üretici çıkışında TL taban, yıllık enflasyon endeksli) projenin sigortası.
- **Verim kaybı da sert:** −%25 verimde IRR %9,3. Gölge filesi, sık hasat, sinek tuzağı ve sigorta (v3 Bölüm 5) bu yüzden bütçeden çıkarılmadı.
- **İşçilik ve komisyon artışı yönetilebilir:** TEKNOSAB etkisiyle +%35 işçilikte ya da %25 komisyonda IRR %17 civarında kalıyor.
- **Üçlü şok** (fiyat −%20, verim −%15, işçilik +%20) birlikte gelirse yatırım geri dönmüyor.

---

## 8. Kimin Ne Zaman Ne Yaptığı (zaman bütçesi)

| Kişi | Görev | Yıllık zaman (tahmin) |
|---|---|---|
| **Sen** | Sistem kurulumu (2027 kışı yoğun), haftalık veri kontrolü, ortakla planlama, sezon kararları, muhasebe | Uzaktan haftada 2-3 saat + ~20 ziyaret (sezonda 2-3 günlük kalışlar). Kurulum yılı ~250 saat, sonraki yıllar ~150-200 saat |
| **Baban** | Sahada göz: ekip denetimi, sulama/alarm kontrolü, hasat günlerinde soğuk oda ve teslim | Sezon dışı haftada 1 gün, haziran-ekim haftada 2-3 gün |
| **Dayıbaşı + yevmiyeli ekip** | Budama (ocak-şubat), bağlama, ot, hasat | Tepe hasatta 4-5 kişi; budamada 2-3 kişi × ~2 hafta |
| **Sezonluk yardımcı** | Soğuk oda, etiket, koli | Haziran-ekim |
| **Ziraat danışmanı** | Budama, gübre, hastalık kararlarına ikinci göz | Sezonda ayda 1 (ücreti bakım/gübre bütçesinden) |

Ay ay iş takvimi v3 Bölüm 3'te; bu planda yalnız pakethane ve ofis işleri yok.

---

## 9. Kârdan Eklenecekler: Karar Kuralları

| Ne | Ne zaman | Karar kuralı |
|---|---|---|
| **İkinci 10 da (20 dönüme büyüme)** | Fidan siparişi Eylül 2028, dikim Nisan 2029 | 2028'de ≥ 9 t satıldı, ortalama fiyat taban fiyatın üstünde, ortak daha fazla hacim istiyor, baban ve saha düzeni yükü kaldırıyor. Ek yatırım ~$45k; 20 dönümde getiri %27'ye çıkar (v6) |
| Şok dondurucu + -20 °C depo | Yalnız 20 dönüme büyürse | 2. sınıf ürün ≥ 6 t/yıl ve IQF alıcısı bulunduysa |
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

1. **10 dönüm, hibrit dikim:** başlangıç yatırımı **$64.127 (≈3,0 M TL)**; cepten çıkan en yüksek tutar $68.925, Ziraat kredisiyle ~$40k.
2. **2028'de başabaş, 2029'dan itibaren yılda ~$15-21k net**, 2031'de aylık ~76 bin TL ek gelir. Yatırım 4,4 yılda geri dönüyor; 10 yılda toplam net kâr ~$139k.
3. **Teknoloji kaliteyi belirleyen dört karar için kuruluyor:** sulama, ilaçlama, hasat zamanlaması, soğuk zincir. Bütçe ~$8k ve yazılımın tamamı açık kaynak, kendi yapımın.
4. **10 dönüm 20 dönümden kırılgan.** Ortakla taban fiyatlı yazılı sözleşme ve babanın düzenli desteği burada daha da kritik.
5. **Büyüme kapısı açık:** 2028 sezonu hedefi tutarsa 2029'da ikinci 10 dönümle 20 dönüm planına (v6) geçilir.

---

### Ek — Varsayımlar ve kaynaklar

| Varsayım | Değer |
|---|---|
| Soğuk depo | 20' yenilenmiş reefer (~28 m³), 10 da tepe yükü ~300 kg/gün için yeterli |
| Fidan fiyatı | Doku kültürü $3,0/ad, 2 yaşlı saksılı $6,5/ad (**tahmin, teklif alınmalı**) |
| Verim | Doku kültürü 0,6 / 8 / 17 / 20 t; saksılı 3,5 / 15 / 20 / 20 t (10 da başına, sık dikim) |
| Satış | 1. sınıfın %60 → %80'i ortak üzerinden paketli ($5,65/kg, %18 komisyon), kalanı hal; 2. sınıf işleme ($1,30) veya IQF ($2,80) |
| Ekipman fiyatları | 2026 Türkiye piyasası tahminleri; her kalem için en az 3 teklif |
| Kur | 1 USD = 47 TL (Ekim 2026 çalışma kuru) |
| Hariç | Arazi kirası (arazi senin), kurucu ve baba emeğinin ücreti, olası Ziraat kredisi faizi (Özet'te ayrıca gösterildi) |

Tarımsal veriler, risk analizi ve bölge bilgileri için v1-v4 raporları; kredi kaynakları v1 Ek B.
