# Akıllı Dikensiz Böğürtlen Bahçesi — Fizibilite ve Yatırım Analiz Raporu

**Proje:** 10 dekar pilot, teknoloji odaklı dikensiz kültür böğürtleni (Chester / Loch Ness)
**Lokasyon:** Bursa / Karacabey / Muratlı Mah. — DSİ Uluabat 2. Kısım AT-TİGH sahası
**Rapor tarihi:** 2 Ekim 2026 · **Para birimi:** USD (TL karşılığı **1 USD = 47 TL** çalışma kuru ile)
**Hesap modeli:** [`model.py`](model.py). Tablolardaki her rakam bu dosyadan üretildi. Varsayımı değiştirip `python reports/bogurtlen-fizibilite/model.py` ile yeniden hesaplayabilirsiniz.

> Not: Repo herkese açık olduğu için ada/parsel numarası ve tam koordinatlar rapora yazılmadı. Analizde mahalle düzeyindeki konum bilgisi yeterli.

---

## 0. Yönetici Özeti

| Gösterge | S1 Talep (toptan $2,50) | S2 Talep (perakende $4,00) | **S3 Uzman gerçekçi (karma)** | S4 Pesimistik stres |
|---|---:|---:|---:|---:|
| CAPEX (soğuk oda dahil) | $53.650 | $53.650 | **$53.650** | $61.697 |
| Tam verim rekoltesi | 28 t | 28 t | **20 t** | 15 t |
| Tam verim yılı net nakit | $30.550 | $47.350 | **$18.594** | −$8.578 |
| Geri dönüş süresi (dikimden) | 3,8 yıl | 3,0 yıl | **5,5 yıl** | geri dönmez |
| NPV (10 yıl, %12 USD) | $63.352 | $131.698 | **$8.335** | −$103.204 |
| Proje IRR (USD) | %29,2 | %42,3 | **%14,6** | negatif |

**Beş ana bulgu:**

1. **Hedef CAPEX bandı ($35-40k) kalemler eksiksiz sayıldığında tutmuyor.** İstenen kalemlerin tam spesifikasyonu **$45.150** ediyor (%7 beklenmeyen gider dahil). Buna listede olmayan ama zorunlu gördüğüm **ön soğutma ve soğuk oda ($8.500)** eklenince toplam **$53.650** oluyor. Bölüm 1.3'teki yalın versiyonla bu tutar **$35.150'ye (soğuk odasız) veya $43.650'ye (soğuk odalı)** inebilir.
2. **28 t/10 da verim (bitki başına 9,3 kg) üst sınır kabul edilmeli.** Türkiye açık tarla Chester ortalaması 1,2-2,0 t/da. İyi yönetilen, fertigasyonlu, yüksek seddeli bahçelerde 2,0-2,5 t/da görülüyor. Banka ve yatırımcı sunumunda baz senaryo olarak **20 t (2,0 t/da)** kullanılmalı.
3. **Projenin asıl riski satış.** Karacabey'de temmuz-ağustos arasındaki 6-7 haftada 20-28 ton taze böğürtlen satmak gerekiyor. Ürünün raf ömrü soğuk zincirsiz 2-3 gün. Soğuk oda ve en az üç satış kanalı (hal, perakende/HoReCa, işleme/dondurma) olmadan $2,50/kg ortalama fiyat garanti değil.
4. **Stres testi:** Fiyat %30 düşer, işçilik %40 artar ve verim %25 kaybederse proje nakit üretmez. Tam verim yılında başabaş için 15 t rekoltede **ağırlıklı satış fiyatının en az $2,45/kg** olması gerekiyor (baz karma fiyat $2,635). Yani fiyatın baz değerin %93'ünün altına düşmemesi lazım. Tek başına en yıkıcı şok **%30 fiyat düşüşü**. Fiyatın sözleşmeyle korunması, sensör paketinden daha önemli.
5. **Önerilen yapı:** Yalın CAPEX ($43.650, soğuk odalı) + CAPEX'in %50'si için Ziraat Bankası Hazine faiz destekli TL kredisi + aşamalı kâr paylaşımı (waterfall). Bu yapıda gerçekçi senaryoda proje IRR'si %18,6'ya, kredili özsermaye IRR'si %18,8 (tam CAPEX) ile %23,8 (yalın CAPEX) arasına çıkıyor.

**Karar: ŞARTLI OLUMLU.** Şartlar: (i) dikimden önce en az bir işleme/dondurma tesisiyle alım sözleşmesi (taban fiyat ≥ $1,30/kg) ve bir perakende/HoReCa kanalı; (ii) soğuk oda; (iii) yalın CAPEX; (iv) ilk 2 yıl verim ölçümü bitmeden ikinci faza (alan genişletme) geçilmemesi.

---

## 1. CAPEX — İlk Kurulum Maliyeti

### 1.1 Tasarım parametreleri (hesap tabanı)

| Parametre | Değer | Hesap |
|---|---|---|
| Alan | 10.000 m² | ~100 m × 100 m varsayımı |
| Sıra arası × sıra üzeri | 3,0 m × 1,0 m | 10.000 / 3 = **33 sıra** × ~100 m = **~3.300 m sıra** |
| Fidan | 3.000 + %5 yedek | 3.300 m / 1 m − baş dönüm boşlukları ≈ 3.000 |
| Direk | 6 m aralık | 33 × (100/6 + 2) ≈ **630 direk** |
| Tel | 3 kat | 3.300 × 3 = 9.900 m ≈ **10.000 m** |
| Damla lateral | çift hat | 3.300 × 2 = **6.600 m** |

### 1.2 Kalem kalem CAPEX (tam spesifikasyon)

| Grup | Kalem | Miktar | USD | TL (47) |
|---|---|---|---:|---:|
| Arazi hazırlığı | Toprak analizi (2 derinlik, 4 nokta) + drenaj kontrolü | 1 set | 250 | 11.750 |
| Arazi hazırlığı | Dip kazan (subsoiler) + diskaro + rototiller | 10 da | 600 | 28.200 |
| Arazi hazırlığı | Lazerli tesviye (%0,2-0,3 drenaj eğimi bırakılarak) | 10 da | 550 | 25.850 |
| Arazi hazırlığı | Yanmış çiftlik gübresi / kompost (4 t/da) | 40 t | 2.000 | 94.000 |
| Arazi hazırlığı | Yüksek sedde (30-40 cm) yapımı | ~3.300 m | 450 | 21.150 |
| Arazi hazırlığı | Sedde üstü agrotekstil malç örtü | 3.400 m² | 1.100 | 51.700 |
| Fidan | Doku kültürü M1 mavi sertifikalı fidan | 3.000 × $3,00 | 9.000 | 423.000 |
| Fidan | Yedek fidan (%5) + dikim işçiliği | 150 ad + 15 yevmiye | 1.050 | 49.350 |
| Telli terbiye | Galvaniz direk 2,7 m | ~630 × $8,5 | 5.350 | 251.450 |
| Telli terbiye | Gergi teli 2,5 mm (3 kat) + ankraj | ~10.000 m + 66 ankraj | 1.650 | 77.550 |
| Telli terbiye | T-kol (cross-arm) + montaj | set | 1.500 | 70.500 |
| Sulama & fertigasyon | Ana hat PE + vanalar + DSİ hidrant bağlantısı | set | 900 | 42.300 |
| Sulama & fertigasyon | Disk + kum filtre grubu | 1 set | 700 | 32.900 |
| Sulama & fertigasyon | Damla lateral (16 mm, 33 cm, basınç ayarlı), çift hat | ~6.600 m | 850 | 39.950 |
| Sulama & fertigasyon | Fertigasyon kontrolörü (4G/Wi-Fi), 4 selenoid vana | 4 zon | 1.800 | 84.600 |
| Sulama & fertigasyon | EC/pH dozaj ünitesi (2 gübre + 1 asit kanalı) | 1 ad | 2.400 | 112.800 |
| AgTech sensör | Toprak istasyonu (30/60 cm nem + EC + sıcaklık), LoRa/4G | 3 × $650 | 1.950 | 91.650 |
| AgTech sensör | Mikro meteoroloji istasyonu (yaprak ıslaklığı, don alarmı) | 1 ad | 1.900 | 89.300 |
| AgTech sensör | Gateway, kurulum, kalibrasyon, 1. yıl platform | set | 600 | 28.200 |
| Güvenlik | Solar 4G PTZ AI kamera (360°) | 2 × $650 | 1.300 | 61.100 |
| Güvenlik | Solar termal kamera | 1 ad | 1.600 | 75.200 |
| Gölgeleme | %35 beyaz gölge filesi, sıra üstü şerit | ~4.500 m² | 2.700 | 126.900 |
| Gölgeleme | Direk uzatma + file teli + montaj | set | 1.100 | 51.700 |
| Diğer | Proje/danışmanlık, izinler, ilk TARSİM poliçesi | – | 900 | 42.300 |
| | **Alt toplam** | | **42.200** | **1.983.400** |
| | Beklenmeyen giderler (%7) | | 2.950 | 138.650 |
| | **CAPEX, istenen kapsam** | | **45.150** | **2.122.050** |
| | **+ Ön soğutma + 20 m³ soğuk oda (+2/+4 °C)** *(eklediğim kritik kalem)* | | 8.500 | 399.500 |
| | **CAPEX, önerilen tam kapsam** | | **53.650** | **2.521.550** |

**Grup dağılımı (tam kapsam $53.650 içinde):** Fidan %18,7 · Telli terbiye %15,8 · Soğuk oda %15,8 · Sulama ve fertigasyon %12,4 · Arazi hazırlığı %9,2 · AgTech sensör %8,3 · Gölgeleme %7,1 · Güvenlik %5,4 · Beklenmeyen + diğer %7,2.

**Teknik notlar:**
- **Toprak pH sensörü:** Toprağa gömülü pH probları 3-6 ayda kalibrasyondan kayar. pH kontrolü fertigasyon çözeltisinde ve drenaj suyunda yapılmalı. Toprakta nem, EC ve sıcaklık izlenmeli, pH için 3 ayda bir laboratuvar analizi yeterli. Bütçede toprak pH probu bu yüzden yer almıyor.
- **Killi-tınlı toprak:** Sedde yüksekliği 40 cm'den az olmamalı. Böğürtlende kök boğazı çürüklüğü (*Phytophthora*) ağır topraklarda en büyük fidan kaybı nedeni. DSİ drenajı yüzey suyunu alır ama kök bölgesi havalanmasını ancak sedde sağlar.
- **Gölge filesi:** Chester'da 33-35 °C üstünde güneş yanığı (beyaz dane, "sunscald") ciddi kayıp yaratır. Karacabey'de temmuz ortalama maksimumu 31-32 °C ve 38 °C'nin üstündeki ekstremler artık neredeyse her yıl görülüyor. File, verimi değil **pazarlanabilir verimi** korur.

### 1.3 Yalın CAPEX (hedef banda çekme)

| Kesinti / erteleme | Tasarruf (USD) |
|---|---:|
| Fidan pazarlığı: 3.000 adet toplu alımda $3,00 → $2,50 | 1.500 |
| Direk aralığı 6 m → 8 m (ara gergiyle) | 1.350 |
| Termal kamerayı 2. yıla ertele (PTZ AI kameralar 1. yıl yeterli) | 1.600 |
| Gölge filesini 2. yıla ertele (dikim yılında rekolte yok) | 3.800 |
| EC/pH dozaj: 3 kanal yerine venturi + tek asit pompası | 1.100 |
| **Toplam** | **9.350** |

| Versiyon | USD | TL |
|---|---:|---:|
| Yalın, soğuk odasız (%7 beklenmeyen dahil) | **35.150** | 1.652.050 |
| **Yalın + soğuk oda (önerilen)** | **43.650** | 2.051.550 |

Ertelenen $5.400'lük kalem (file + termal kamera) 2. yılın ilk hasat gelirinden karşılanır.

---

## 2. OPEX — Yıllık İşletme Giderleri

### 2.1 Sabit OPEX (USD/yıl, 10 da)

| Kalem | Yıl 1 | Yıl 2 | Yıl 3 | Yıl 4+ |
|---|---:|---:|---:|---:|
| Gübre (fertigasyon + organik) | 700 | 1.100 | 1.500 | 1.600 |
| Biyolojik/kimyasal mücadele (SWD tuzağı, Bt, avcı akar, bakır) | 400 | 900 | 1.300 | 1.400 |
| Budama + sürgün bağlama işçiliği | 600 | 1.300 | 1.800 | 1.900 |
| Ot / sıra arası biçim, malç bakımı | 500 | 550 | 600 | 600 |
| DSİ su ücreti + pompa elektriği | 250 | 400 | 500 | 500 |
| IoT veri / 4G SIM + platform aboneliği | 500 | 950 | 950 | 950 |
| Bakım-onarım (ekipmanın ~%4'ü) | 0 | 700 | 900 | 1.000 |
| TARSİM sigortası | 0 | 500 | 700 | 750 |
| Soğuk oda elektriği | 0 | 400 | 700 | 750 |
| Muhasebe, borsa tescili, sabit nakliye | 300 | 500 | 600 | 600 |
| **Toplam sabit OPEX** | **3.250** | **7.300** | **9.550** | **10.050** |
| TL karşılığı | 152.750 | 343.100 | 448.850 | 472.350 |

### 2.2 Değişken OPEX (kg başı)

| Kalem | Toptan (hal) | Perakende/gurme | İşleme/dondurma |
|---|---:|---:|---:|
| Elle hasat işçiliği | $0,60 | $0,60 | $0,60 |
| Ambalaj + soğuk lojistik | $0,20 (kasa/viyol) | $0,75 (250 g klapa, etiket, soğuk zincir) | $0,05 (kasa) |
| Komisyon / fire / stopaj | %10 (hal komisyonu %8 + rüsum/stopaj ~%2) | %15 (kanal payı + iade/fire) | %3 |

**Hasat işçiliği kontrolü:** 2026 tarım yevmiyesi yaklaşık 1.500-1.800 TL ($32-38). Taze pazar kalitesinde toplama hızı 7-9 kg/saat, günde 55-70 kg eder. Buradan kg başı maliyet **$0,50-0,65** çıkıyor, yani verdiğiniz $0,50-0,70 bandı doğru. Modelde $0,60 kullanıldı. Tam verimde (20-28 t) bu, 6 hafta boyunca **günde 7-10 toplayıcı** demek. İşçi bulma riski bu nedenle ciddi (Bölüm 4).

### 2.3 Yıllara göre toplam OPEX

| Yıl | Rekolte (S3) | Sabit OPEX | Hasat ($0,60) | Ambalaj + komisyon | **Toplam OPEX** | kg başı |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0 t | 3.250 | 0 | 0 | **3.250** | – |
| 2 | 5 t | 7.300 | 3.000 | 3.014 | **13.314** | $2,66 |
| 3 | 14 t | 9.550 | 8.400 | 8.439 | **26.389** | $1,88 |
| 4+ | 20 t | 10.050 | 12.000 | 12.056 | **34.106** | **$1,71** |

Talep senaryosunda (28 t, %100 toptan) 4. yıl toplam OPEX: 10.050 + 16.800 + 12.600 = **$39.450** (kg başı $1,41).

---

## 3. Rekolte, Gelir ve ROI Modeli

### 3.1 Verim varsayımları — eleştirel değerlendirme

| Yıl | Talep (t) | t/da | kg/bitki | Uzman gerçekçi (t) | Gerekçe |
|---|---:|---:|---:|---:|---|
| 1 (dikim) | 0 | 0 | 0 | 0 | Primokan büyüme yılı |
| 2 | 10 | 1,0 | 3,3 | **5** | İlk floricane yılında 1-2 kg/bitki normal. 3,3 kg ancak çok güçlü fidanla mümkün |
| 3 | 25 | 2,5 | 8,3 | **14** | Kanopi henüz tam dolmuyor |
| 4-8 | 28 | 2,8 | 9,3 | **20** | 2,0 t/da: iyi yönetilen açık tarla Chester'ın üst-orta seviyesi |
| 9-10 | 25,2 / 22,4 | | | 18 / 16 | Yaşlanma, %10-20 düşüş |

### 3.2 Senaryo S1 — Talep verimi, %100 toptan $2,50/kg

| Yıl | Rekolte (t) | Brüt gelir | Ambalaj+komisyon | Hasat işçiliği | Sabit OPEX | Net nakit | Kümülatif |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | – | – | – | – | – | −53.650 | −53.650 |
| 1 | 0,0 | 0 | 0 | 0 | 3.250 | −3.250 | −56.900 |
| 2 | 10,0 | 25.000 | 4.500 | 6.000 | 7.300 | 7.200 | −49.700 |
| 3 | 25,0 | 62.500 | 11.250 | 15.000 | 9.550 | 26.700 | −23.000 |
| 4 | 28,0 | 70.000 | 12.600 | 16.800 | 10.050 | 30.550 | 7.550 |
| 5-8 | 28,0 | 70.000 | 12.600 | 16.800 | 10.050 | 30.550 | 129.750 (Y8) |
| 9 | 25,2 | 63.000 | 11.340 | 15.120 | 10.050 | 26.490 | 156.240 |
| 10 | 22,4 | 56.000 | 10.080 | 13.440 | 10.050 | 22.430 | 178.670 |

**Geri dönüş 3,8 yıl · NPV@12 $63.352 · IRR %29,2.** Tam verim yılı net nakit $30.550 ≈ **1,44 milyon TL**.

### 3.3 Senaryo S2 — Talep verimi, %100 perakende/gurme $4,00/kg

| Yıl | Rekolte (t) | Brüt gelir | Ambalaj+komisyon | Hasat işçiliği | Sabit OPEX | Net nakit | Kümülatif |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | – | – | – | – | – | −53.650 | −53.650 |
| 1 | 0,0 | 0 | 0 | 0 | 3.250 | −3.250 | −56.900 |
| 2 | 10,0 | 40.000 | 13.500 | 6.000 | 7.300 | 13.200 | −43.700 |
| 3 | 25,0 | 100.000 | 33.750 | 15.000 | 9.550 | 41.700 | −2.000 |
| 4 | 28,0 | 112.000 | 37.800 | 16.800 | 10.050 | 47.350 | 45.350 |
| 5-8 | 28,0 | 112.000 | 37.800 | 16.800 | 10.050 | 47.350 | 234.750 (Y8) |
| 9 | 25,2 | 100.800 | 34.020 | 15.120 | 10.050 | 41.610 | 276.360 |
| 10 | 22,4 | 89.600 | 30.240 | 13.440 | 10.050 | 35.870 | 312.230 |

**Geri dönüş 3,0 yıl · NPV@12 $131.698 · IRR %42,3.**
⚠️ **Gerçeklik kontrolü:** 28 t'nin tamamını 250 g klapada perakende satmak, 6 haftada **112.000 klapa** (günde ~2.700) demek. Bu hacim marka, zincir market listelemesi ve günlük soğuk dağıtım gerektirir ve 10 da'lık bir işletmenin ilk 3 yılında gerçekçi değil. Bu senaryoyu bir tavan olarak okuyun. Perakende payı ilk yıllarda %20-30'u geçmez.

### 3.4 Senaryo S3 — Uzman gerçekçi: 20 t, karma kanal (önerilen baz senaryo)

Kanal dağılımı: **%55 toptan ($2,50) + %25 perakende ($4,00) + %20 işleme/dondurma ($1,30)**, ağırlıklı ortalama **$2,635/kg**.

| Yıl | Rekolte (t) | Brüt gelir | Ambalaj+komisyon | Hasat işçiliği | Sabit OPEX | Net nakit | Kümülatif |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | – | – | – | – | – | −53.650 | −53.650 |
| 1 | 0,0 | 0 | 0 | 0 | 3.250 | −3.250 | −56.900 |
| 2 | 5,0 | 13.175 | 3.014 | 3.000 | 7.300 | −139 | −57.039 |
| 3 | 14,0 | 36.890 | 8.439 | 8.400 | 9.550 | 10.501 | −46.538 |
| 4 | 20,0 | 52.700 | 12.056 | 12.000 | 10.050 | 18.594 | −27.944 |
| 5 | 20,0 | 52.700 | 12.056 | 12.000 | 10.050 | 18.594 | −9.350 |
| 6 | 20,0 | 52.700 | 12.056 | 12.000 | 10.050 | 18.594 | 9.244 |
| 7 | 20,0 | 52.700 | 12.056 | 12.000 | 10.050 | 18.594 | 27.838 |
| 8 | 20,0 | 52.700 | 12.056 | 12.000 | 10.050 | 18.594 | 46.432 |
| 9 | 18,0 | 47.430 | 10.850 | 10.800 | 10.050 | 15.730 | 62.161 |
| 10 | 16,0 | 42.160 | 9.645 | 9.600 | 10.050 | 12.865 | 75.027 |

**Geri dönüş 5,5 yıl · NPV@12 $8.335 · IRR %14,6.**
**Yalın CAPEX ($43.650) ile:** geri dönüş **5,0 yıl**, NPV@12 **$18.335**, IRR **%18,6**.
NPV'nin sıfırlandığı tam verim rekoltesi **18,5 t** (1,85 t/da). Baz senaryonun güvenlik payı sadece **%7,6**.

### 3.5 ROI ve amortisman özeti

| Metrik | S1 | S2 | S3 | S3 yalın |
|---|---:|---:|---:|---:|
| Basit geri dönüş (yıl, dikimden) | 3,8 | 3,0 | 5,5 | 5,0 |
| 10 yıllık kümülatif net nakit | $178.670 | $312.230 | $75.027 | $85.027 |
| 10 yıllık ROI (kümülatif / CAPEX) | %333 | %582 | %140 | %195 |
| IRR | %29,2 | %42,3 | %14,6 | %18,6 |
| Muhasebe amortismanı (VUK, telli terbiye + sulama ~10 yıl, elektronik ~5 yıl) | Yıllık ~$4.000-4.500 | | | |

---

## 4. Türkiye Şartları — Risk ve Stres Testi

### 4.1 Tek faktörlü duyarlılık (S3 bazında)

| Şok | Tam verim yılı net | Geri dönüş | NPV@12 | IRR |
|---|---:|---:|---:|---:|
| **Baz S3** | $18.594 | 5,5 yıl | $8.335 | %14,6 |
| Tüccar baskısı: fiyat −%30 | $4.556 | **geri dönmez** | −$45.649 | −%11,1 |
| İklim/sıcak stresi: verim −%25 | $11.433 | 7,7 yıl | −$19.203 | %4,8 |
| İşçi krizi: hasat $0,84/kg (+%40) | $13.794 | 6,7 yıl | −$10.123 | %8,4 |
| Enflasyon/kur: USD bazlı maliyet +%8/yıl (3 yıl) | $12.867 | 6,9 yıl | −$12.737 | %7,4 |
| CAPEX +%15 (kur şoku kurulum anında) | $18.594 | 5,9 yıl | $287 | %12,1 |
| **Hepsi birlikte (S4)** | **−$8.578** | **geri dönmez** | **−$103.204** | negatif |

**"Enflasyon stresi" ile "kur baskısı" nasıl modellendi:** Türkiye'de son yıllarda görülen örüntü, TL enflasyonunun kur artışından hızlı seyretmesi (reel TL değerlenmesi). Bu durumda işçilik, gübre ve elektrik **USD bazında pahalanıyor**. Satış fiyatları ise ithal/ihraç paritesi nedeniyle USD'de yatay kalma eğiliminde. Modelde maliyetler ilk 3 yıl USD bazında %8/yıl artıyor ve sonra yatay seyrediyor. Toplam etki +%26.

### 4.2 Pesimistik senaryo S4 (tüm şoklar aynı anda)

Varsayımlar: fiyat −%30 (karma $1,84/kg), verim −%25 (tam verim 15 t), hasat $0,84/kg (yıllık %8 artışla 4. yılda $1,06), maliyet +%8/yıl (3 yıl), CAPEX +%15 ($61.697).

| Yıl | Rekolte (t) | Brüt gelir | Ambalaj+komisyon | Hasat | Sabit OPEX | Net nakit | Kümülatif |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | – | – | – | – | – | −61.697 | −61.697 |
| 1 | 0,0 | 0 | 0 | 0 | 3.250 | −3.250 | −64.947 |
| 2 | 3,8 | 6.917 | 1.928 | 3.402 | 7.884 | −6.297 | −71.245 |
| 3 | 10,5 | 19.367 | 5.399 | 10.288 | 11.139 | −7.459 | −78.704 |
| 4-8 | 15,0 | 27.668 | 7.713 | 15.872 | 12.660 | −8.578 | −121.594 (Y8) |
| 10 | 12,0 | 22.134 | 6.171 | 12.698 | 12.660 | −9.395 | −139.975 |

### 4.3 Başabaş noktaları (break-even)

**(a) Başabaş fiyatı.** Tam verim yılında nakit sıfır için gereken ağırlıklı fiyat:

> P* = (Sabit OPEX / kg + hasat + ambalaj) / (1 − komisyon oranı)

| Durum | Hesap | **Başabaş fiyat** | Baz fiyata oranı |
|---|---|---:|---:|
| Talep (28 t, toptan) | (10.050/28.000 + 0,60 + 0,20) / 0,90 | **$1,29/kg** | %52 |
| S3 gerçekçi (20 t, karma) | (10.050/20.000 + 0,60 + 0,3075) / 0,9015 | **$1,56/kg** | %59 |
| S4 stres (15 t, hasat $1,06, OPEX +%26) | (12.660/15.000 + 1,06 + 0,3075) / 0,9015 | **$2,45/kg** | **%93** |

**(b) Başabaş rekolte.** Kg başı katkı payı = fiyat × (1 − komisyon) − ambalaj − hasat:

| Durum | Katkı payı / kg | **Başabaş rekolte** |
|---|---:|---:|
| Baz maliyet, baz fiyat ($2,635) | $1,47 | **6,8 t** (0,68 t/da) |
| Stres maliyet, baz fiyat | $1,01 | **12,5 t** (1,25 t/da) |
| Stres maliyet, fiyat −%30 | $0,30 | **42,6 t → 10 da'da imkânsız** |

**(c) Sermaye başabaşı.** S4 koşullarında 10 yılda yatırımın sadece geri dönmesi (NPV@0) için fiyatların stres seviyesinin **1,22 katı** olması gerekiyor (≈ $2,25/kg, baz fiyatın %85'i). %12 getiri için **1,47 katı** (≈ $2,71/kg).

**Yorum:** Proje maliyet ve verim şoklarını tek tek kaldırabiliyor. **Fiyat şokunu, özellikle işçilik şokuyla birlikte gelirse, kaldıramıyor.** Kg başı katkı payı $1,47'den $0,30'a düşüyor. Bu yüzden risk yönetimi önceliği şu sırada olmalı: **(1) fiyat ve kanal, (2) hasat işgücü, (3) iklim, (4) maliyet.**

### 4.4 Risk matrisi ve önlemler

| Risk | Olasılık | Etki | Önlem | Maliyet |
|---|---|---|---|---|
| **Tüccar/hal fiyat baskısı** (hasat zirvesinde fiyat %30-50 düşer) | Yüksek | Çok yüksek | Dikimden önce işleme/dondurma tesisiyle taban fiyatlı alım sözleşmesi ($1,30/kg, ürünün %20-30'u). Soğuk oda ile satışı 5-7 gün kaydırma. Perakende/HoReCa (Bursa-İstanbul) payını 3. yılda %25'e çıkarma | Soğuk oda $8.500 (CAPEX'te) |
| **Drosophila suzukii (SWD)** | Yüksek (Marmara'da yaygın) | Yüksek (%20-50 kayıp) | Elma sirkesi tuzak ağı, 2 günde bir hasat, düşük meyve sanitasyonu, gerekirse sıra kenarına böcek tülü | OPEX'te (mücadele kalemi) |
| **Hasat işçisi bulamama** | Orta-yüksek | Yüksek | Muratlı ve çevre köylerden 8-10 kişilik sabit ekip, sezon başı avans + kg başı prim, Loch Ness karışımıyla hasadı 2 haftaya yayma | +$0,05-0,10/kg prim |
| **Yaz sıcağı / güneş yanığı** | Orta-yüksek | Orta | Gölge filesi, sabah erken hasat, sıcak dalgası öncesi IoT tetikli serinletme sulaması | CAPEX'te |
| **Phytophthora / kök boğulması** | Orta (killi toprak) | Yüksek | 40 cm sedde, drip ile kontrollü nem, sensör eşiği (30 cm'de tarla kapasitesinin %85'i üstü alarm) | CAPEX'te |
| **Geç bahar donu** | Düşük (orman kalkanı + Chester'ın geç çiçeklenmesi) | Orta | Meteoroloji istasyonu don alarmı | CAPEX'te |
| **Hırsızlık / vandalizm** | Orta | Düşük-orta | Solar AI kamera + termal kamera | CAPEX'te |
| **Kur şoku (kurulum anında)** | Orta | Orta | İthal ekipmanı (sensör, kontrolör) peşin USD fiyatla sabitleme, fidan için ön sipariş | – |
| **Politika / destek değişikliği** | Orta | Düşük-orta | Kredi faiz desteğinde kilit tarih: 31.12.2026 (aşağıya bakın) | – |

### 4.5 AgTech paketinin ekonomik gerekçesi

$7.350'lik sensör ve güvenlik paketi (E + F grupları), 10 yılda kendini **yılda ~%1,5 pazarlanabilir verim kurtararak** öder ($52.700 × %1,5 × 10 yıl ≈ $7.900). Gerçekçi faydalar: %15-25 su ve gübre tasarrufu (yıllık ~$400-600), don ve hastalık uyarısıyla kayıp önleme, hırsızlıkta caydırıcılık. Asıl katkısı ise **yatırımcıya uzaktan şeffaflık**: kameralar ve sensör verisi waterfall ortaklığında güven mekanizması işlevi görür (Bölüm 5). Bu paket verimi kendi başına 20 t'dan 28 t'ya çıkarmaz.

---

## 5. İş Ortaklığı ve Finansman Yapısı

### 5.1 Katkıların değerlemesi

| Taraf | Katkı | Değer (10 yıl) |
|---|---|---|
| **Yatırımcı** | CAPEX ($43.650 yalın / $53.650 tam) + ilk 2 yıl işletme açığı (~$3.400) + pazar/kanal erişimi | **~$47.000-57.000** nakit |
| **Arazi sahibi** | 10 da sulu arazi kirası (~7.000 TL/da/yıl ≈ $150/da → $1.500/yıl), DSİ su hakkı, 7/24 saha yönetimi (yarı zamanlı yönetici ≈ $4.000/yıl) | **~$55.000** ayni katkı |

Katkılar yaklaşık eşit. Fakat yatırımcının sermayesi **ilk günden riskte**, arazi sahibinin katkısı ise zamana yayılıyor. Bu asimetri, düz 50/50 yerine **waterfall** yapısını gerekçelendiriyor.

### 5.2 Önerilen aşamalı kâr paylaşımı (waterfall)

| Kademe | Kural | Yatırımcı | Arazi sahibi |
|---|---|---:|---:|
| **0 — Saha ücreti** | Brüt satış gelirinin %5'i, her yıl, diğer dağıtımlardan önce (arazi sahibinin emeğini ve performansını ödüllendirir) | – | %100 |
| **1 — Sermaye iadesi** | Yatırımcının koyduğu tüm nakit geri dönene kadar | **%85** | %15 |
| **2 — Tercihli getiri** | Yatırımcının USD IRR'si %12'ye ulaşana kadar | **%70** | %30 |
| **3 — Kalıcı ortaklık** | Sonrası | %50 | %50 |

**Model sonuçları (tam CAPEX, 10 yıl, USD):**

| Senaryo | Yatırımcı IRR | Yatırımcı 10 yıl net kazanç | Arazi sahibine 10 yıl nakit |
|---|---:|---:|---:|
| S1 Talep, toptan | %18,0 | $80.680 | $97.990 |
| S2 Talep, perakende | %27,0 | $136.584 | $175.646 |
| **S3 Gerçekçi** | **%7,3** | **$31.281** | **$43.746** |
| S3 Gerçekçi + yalın CAPEX | **%10,5** | $39.516 | $45.510 |

S3'te yatırımcı getirisi %7-10 USD seviyesinde kalıyor. Bu, risk primi için düşük. Yatırımcı tarafının getirisini yükseltmenin iki yolu var: **kredi kaldıracı** (5.3) ve aşağıdaki **müzakere kolları**.

**Sözleşme maddeleri (müzakere listesi):**
1. **Süre:** 10 yıl + 5 yıl uzatma opsiyonu. Tapuya şerh edilmiş **intifa veya kira sözleşmesi** (yatırımcının sabit yatırım güvencesi için zorunlu).
2. **Varlıkların akıbeti:** Süre sonunda telli terbiye, sulama ve sedde araziye kalır. Elektronik ekipman (sensör, kamera, kontrolör, soğuk oda ünitesi) yatırımcıya döner veya defter değerinden arazi sahibine satılır.
3. **Performans eşiği:** 4. yıldan itibaren rekolte 2 yıl üst üste 12 t'nin altında kalırsa ve sebep iklim dışıysa, Kademe 0 saha ücreti %5'ten %2'ye iner.
4. **Şeffaflık:** Sensör ve kamera platformunda yatırımcıya salt-okuma erişimi, hasat günlüğü (kg/gün, kanal, fiyat) aylık paylaşımı, ortak banka hesabı.
5. **Satış yetkisi:** Kanal sözleşmeleri yatırımcıda, hal satışı ve günlük operasyon arazi sahibinde. Fiyat tabanı ($2,00/kg altı satış) çift imza gerektirir.
6. **Çıkış:** Taraflardan biri çıkarsa diğerinin önalım hakkı. Değerleme = son 2 yıl ortalama net nakit × 3.
7. **Kademe 2 tavanı için alternatif:** Yatırımcı IRR'si %12 yerine %10'da kesilirse arazi sahibinin payı erken artar. Gerçekçi senaryoda bu fark arazi sahibi lehine ~$4-6k.

### 5.3 Ziraat Bankası (Hazine faiz destekli) kredi stratejisi

**Mevcut çerçeve (doğrulanmalı):** Hazine destekli tarımsal kredilerde faiz indirimi oranı 31.12.2026'ya kadar geçerli olmak üzere %50 olarak açıklandı. Bitkisel üretim, bahçe tesisi ve basınçlı sulama konuları destek kapsamında. Kesin oranlar, limitler ve geri ödemesiz süreler başvuru anında şubeden teyit edilmeli. **Başvurunun 2026 sonundan önce yapılması**, yeni dönem koşullarının belirsizliği nedeniyle önemli.

**Modellenen kredi:** CAPEX'in %50'si ($26.825 ≈ **1.260.775 TL**), %18,5 nominal TL faiz (indirimli), 2 yıl anapara ödemesiz (faiz ödenir), 5 yıl vade, 3-5. yıllarda eşit anapara. TL'nin yıllık %18 değer kaybettiği varsayıldı.

| Yıl | Kur (TL/USD) | Faiz (TL) | Anapara (TL) | Taksit (TL) | **Taksit (USD)** | Kalan (TL) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 55,5 | 233.243 | 0 | 233.243 | **4.206** | 1.260.775 |
| 2 | 65,4 | 233.243 | 0 | 233.243 | **3.564** | 1.260.775 |
| 3 | 77,2 | 233.243 | 420.258 | 653.502 | **8.463** | 840.517 |
| 4 | 91,1 | 155.496 | 420.258 | 575.754 | **6.318** | 420.258 |
| 5 | 107,5 | 77.748 | 420.258 | 498.006 | **4.632** | 0 |
| | | | | **Toplam** | **$27.182** | |

**Efektif USD maliyeti: toplamda %1,3 (yıllık ~%0,4).** Faiz TL bazında, gelir ise USD paritesine bağlı. TL değer kaybı faizi büyük ölçüde eritiyor. Bu, projenin en ucuz fonlama kaynağı.

- **S3 özsermaye IRR'si:** kredisiz %14,6 → **kredili %18,8** (tam CAPEX). Yalın CAPEX ($43.650) + %50 kredi ile **%23,8**.
- **Kümülatif özsermaye nakdi (S3, kredili):** Y0 −26.825 → Y2 −37.984 (en derin nokta) → **Y6'da pozitife geçer** → Y10 +74.669.
- ⚠️ **Kredi riski:** TL değer kaybı %18'in altında kalırsa (reel TL değerlenmesi) kredinin USD maliyeti artar. Ama bu durumda bile nominal %18,5 TL faiz, TL enflasyonunun altında kalarak negatif reel faiz sağlar. Asıl risk 3. yıl taksiti ($8.463): S3'te 3. yıl net nakdi $10.501, yani **karşılama oranı 1,24x, ince**. Geri ödemesiz sürenin 3 yıl olarak pazarlık edilmesi önerilir.

**Hibe ve destekler (başvuru öncesi uygunluk kontrolü gerekli):**

| Program | Kapsam | Potansiyel etki |
|---|---|---|
| KKYDP — Bireysel sulama sistemleri | Damla/fertigasyon ekipmanında %50 hibe | ~$3.000-3.500 CAPEX düşüşü (D grubu) |
| Sertifikalı fidan kullanım desteği | Sertifikalı fidanla bahçe tesisine dekar başı destek | Küçük ama nakit |
| TARSİM devlet prim desteği | Primin ~%50'si | OPEX'te varsayıldı |
| Genç Çiftçi / kırsal kalkınma programları | Arazi sahibi yaş ve şartlara uyuyorsa | Hibe |
| İyi Tarım / organik sertifikası | Zincir market ve ihracat kanalına giriş | Perakende payını artırır |

**Önerilen finansman karması (yalın CAPEX $43.650 için):**

| Kaynak | Pay | USD | Not |
|---|---:|---:|---|
| Ziraat Hazine destekli TL kredi | %50 | 21.825 | 2+3 yıl, TL |
| KKYDP sulama hibesi | ~%7 | ~3.200 | Ön finansman yatırımcıdan, hibe sonra gelir |
| Yatırımcı özsermayesi | ~%43 | ~18.600 | + ilk 2 yıl işletme açığı ~$3.400 |

Kredi borçlusu arazi sahibi (çiftçi kaydı ÇKS ve tapu onda), kefili veya teminat sağlayan yatırımcı olur. Kredi taksitleri, waterfall'dan önce ödenen bir operasyon kalemi olarak sözleşmeye yazılmalı.

---

## 6. Uygulama Takvimi ve Karar Kapıları

| Dönem | İş | Karar kapısı |
|---|---|---|
| Ekim-Kasım 2026 | Toprak analizi, satış/işleme ön sözleşmeleri, Ziraat kredi başvurusu (31.12.2026 öncesi), fidan ön siparişi | **Kapı 1:** Alım sözleşmesi yoksa dikim yapılmaz |
| Aralık 2026 - Şubat 2027 | Dip kazan, tesviye, gübreleme, sedde, sulama ana hattı, telli terbiye | |
| Mart-Nisan 2027 | Dikim (doku kültürü fidan, don riski sonrası), malç, sensör ve kamera kurulumu | |
| 2027 yazı | Primokan yönetimi, IoT kalibrasyonu, SWD izleme | |
| Haziran-Ağustos 2028 | İlk hasat (hedef 5 t) | **Kapı 2:** ≥ 4 t ve ≥ $2,30/kg ortalama: soğuk oda + gölge filesi tamamlanır |
| 2029 | 14 t hedefi | **Kapı 3:** ≥ 12 t ise 2. faz (ek 10-20 da) değerlendirilir |

---

## 7. Sonuç

1. Talep edilen senaryolar (S1/S2) bahçenin teknik olarak mümkün olan **üst sınırını** temsil ediyor. Gerçekçi beklenti S3: **IRR %14,6-18,6, geri dönüş 5-5,5 yıl.**
2. Proje **maliyet ve verim şoklarına dayanıklı, fiyat şokuna kırılgan.** Başarının belirleyicisi sensör paketi değil, **dikimden önce kurulan satış kanalı ve soğuk zincir.**
3. Ziraat faiz destekli TL kredisi, TL değer kaybı varsayımıyla neredeyse sıfır USD maliyetli ve özsermaye getirisini ~4-8 puan artırıyor. Başvuru **2026 sonundan önce** yapılmalı.
4. Ortaklıkta waterfall yapısı (Kademe 0 %5 saha ücreti → 85/15 → 70/30 → 50/50), her iki tarafın katkı ve risk profiline uygun. Tapuya şerhli intifa ve şeffaf veri erişimi sözleşmenin olmazsa olmazları.

---

### Ek A — Ana varsayımlar

| Varsayım | Değer | Hassasiyet |
|---|---|---|
| USD/TRY | 47,0 (Ekim 2026 çalışma kuru) | Tüm TL tabloları doğrusal ölçeklenir. Güncel TCMB kuruyla `FX` değişkenini güncelleyin |
| İskonto oranı | %12 USD | Tarım projesi risk primi dahil |
| Ekonomik ömür | 10 yıl | Böğürtlende 10-12 yıl |
| Arazi kirası / sahibin emeği | Proje nakit akışına dahil değil (ayni katkı) | Bölüm 5.1'de değerlendi |
| Vergi | Dahil değil (gerçek kişi çiftçide %2 stopaj komisyon kalemine dahil) | Şirketleşilirse kurumlar vergisi ayrıca hesaplanmalı |
| Fiyatlar | Talep edilen $2,50 / $4,00, işleme $1,30 | 2026 hal ve işleme fiyatları sezon başında teyit edilmeli |

### Ek B — Kaynaklar ve doğrulama notları
- Hazine destekli tarımsal kredilerde faiz indirimi (31.12.2026'ya kadar %50): [Bloomberg HT](https://www.bloomberght.com/tarimsal-uretimde-kullandirilacak-kredilere-iliskin-esaslar-belirlendi-2351935), [Dünya](https://www.dunya.com/kose-yazisi/tarimin-stklari-ses-verdi-hazine-destekli-subvansiyonlu-kredi-faizlerinde-geri-adim-atiliyor/800602), [Bloomberg HT — faiz desteği geri geldi](https://www.bloomberght.com/subvansiyonlu-tarim-kredilerinde-eski-faiz-destegi-geri-geldi-3760308)
- Böğürtlen yetiştiriciliği ve verim aralıkları: [TAGEM Yalova Atatürk Bahçe Kültürleri MAE — Organik Böğürtlen](https://arastirma.tarimorman.gov.tr/yalovabahce/Belgeler/brosurler/OrganikBogurtlen.pdf)
- Perakende fidan fiyat referansı: [Trendyol — böğürtlen fidanı](https://www.trendyol.com/bogurtlen-fidani-y-s280710) (toplu sertifikalı fidan fiyatı fidanlıktan teklifle alınmalı)
- Ekipman fiyatları (direk, damla, sensör, kamera, soğuk oda) 2026 Türkiye piyasa bantlarına dayalı tahminler. Kurulumdan önce en az 3 teklif alınmalı.
