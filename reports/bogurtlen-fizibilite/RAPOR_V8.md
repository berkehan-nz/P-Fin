# Muratlı Böğürtlen — Fizibilite v8: Güncel 2026 Fiyatlarıyla 10 Dönüm Optimizasyonu

**Tarih:** 2 Ekim 2026 · **Para birimi:** 2026 sabit fiyatlarıyla TL (USD karşılığı 1 USD = 49,1 TL, TCMB 1-2 Ekim 2026)
**Hesap modeli:** [`model_v8.py`](model_v8.py) (`--tables` ile bütün tablolar yeniden üretilir)
**Kurgu (v7'den devam):** Satış ortağı (%18 komisyon), saha işi kurucu + baba + yevmiyeli ekip, kendi kurulan açık kaynak teknoloji, çiftçi statüsü (%2 stopaj).

> **Bu sürümde değişen:** Bütün satış fiyatları, fidan, işçilik ve yatırım kalemleri Ekim 2026 internet verileriyle güncellendi (Bölüm 1, kaynaklar Ek A). Önceki raporlardaki dolar bazlı tahminler, güncel verilere göre **satış fiyatını düşük, fidan ve işçiliği yüksek** göstermiş. Sonuçlar bu yüzden belirgin şekilde iyileşti. Ama fiyat verisinin yayılımı çok geniş; temkinli senaryoyu da mutlaka oku.

---

## 0. Kısa Cevaplar

1. **Ceviz ağaçlarının arasına böğürtlen?** Hayır. Ceviz kökleri toprağa **juglon** salgılar ve böğürtlen (Rubus) juglona hassas bitkiler listesinde. Ayrıca gölge, kök rekabeti ve telli sistemin kurulamaması verim ve kaliteyi düşürür. Böğürtlen, ceviz taç izdüşümünden en az 15-20 m uzakta olmalı (Bölüm 2).
2. **10 dönümle olur mu?** Güncel fiyatlarla **evet**. 10 dönüm böğürtlen + kendin-topla satışı 2031'de **~2,3 M TL/yıl net** (aylık ~193 bin TL) getiriyor. 20 dönüm bunun yaklaşık iki katı (~4,4 M TL/yıl).
3. **Alanı bölmek, sera, farklı bitkiler?** Bugünkü fiyatlarla **daha kârlı değil.** Tünelde saksılı ahududu, ortalama satış fiyatı **≥ 700 TL/kg** olmadıkça açık tarla böğürtleni geçemiyor (2026 yaz-sonbahar ahududu hal ortalaması 228 TL/kg). Domates serası ve topraksız çilek günlük bakım istiyor ve uzaktan yönetime uymuyor; topraksız çileğin kurulumu 3,8-5,6 M TL/da. "Çok katlı" sistem böğürtlende uygulanamıyor. Bu ölçekte en kârlı "bölme" ürün çeşitlendirmesi değil, **satış kanalı çeşitlendirmesi**: kendin-topla satışında kg başı katkı 360 TL, halde 149 TL.
4. **Önerim:** **10 dönüm, tamamı böğürtlen (3 çeşit, hibrit fidan) + yol kenarındaki sıralarda kendin-topla + 300 m²'lik deneme tüneli** (Bölüm 4). Başlangıç yatırımı **~2,1-2,2 M TL**.

| Seçenek | Başlangıç yatırımı | Cepten en yüksek | 2028 net | 2031 net | 2031 aylık ek gelir | Geri dönüş | 10 yıl IRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A.** 10 da yalnız böğürtlen | 2,08 M TL | 2,22 M TL | 0,67 M TL | 2,04 M TL | 170.049 TL | 2,6 yıl | %55,4 |
| **B.** 10 da böğürtlen + kendin-topla | 2,14 M TL | 2,28 M TL | 0,72 M TL | 2,32 M TL | 193.342 TL | 2,6 yıl | %58,6 |
| **C.** 10 da optimize: 8,5 da böğürtlen + 1 da tünel ahududu + kendin-topla | 3,18 M TL | 3,29 M TL | 0,60 M TL | 2,06 M TL | 171.886 TL | 3,2 yıl | %40,5 |
| **D.** 20 da böğürtlen + kendin-topla | 3,80 M TL | 4,01 M TL | 1,43 M TL | 4,43 M TL | 368.823 TL | 2,5 yıl | %61,6 |
| **E.** 20 da optimize: 17,5 da böğürtlen + 2 da tünel ahududu + kendin-topla | 5,91 M TL | 6,06 M TL | 1,25 M TL | 4,04 M TL | 337.042 TL | 3,1 yıl | %42,0 |

*A-E seçenekleri Bölüm 3'te. 2031 = tam verimin ilk tam yılı; tutarlar 2026 sabit fiyatlarıyla.*

---

## 1. Güncel Fiyat ve Maliyet Verileri (Ekim 2026)

| Kalem | Güncel veri | Modelde kullanılan |
|---|---|---|
| **Dolar kuru** | 49,03-49,15 TL (1-2 Ekim 2026) | 49,1 TL |
| **Böğürtlen hal fiyatı** | İstanbul 12 Haziran: 440-795 TL/kg · Türkiye ort. 13 Haziran: 327 TL/kg · 6 il ort. 9 Eylül: 259 TL/kg (aralık 60-570) · İstanbul Eylül: 300 TL/kg · **Bursa 16 Eylül: 60-70 TL/kg** | Mevsime göre ağırlıklı **199 TL/kg** (aşağıda) |
| **Böğürtlen raf fiyatı** | Migros 125 g: 209,95 TL (≈1.680 TL/kg) · CarrefourSA 125 g: 139,90 TL | Ortak üzerinden paketli üretici çıkışı **300 TL/kg** (rafın ~%20-25'i) |
| **Ahududu hal fiyatı** | Türkiye ort. 9 Ağustos: 228 TL/kg (100-350) · Nisan (sezon dışı): 1.416-2.344 TL/kg | Tünel, sezon dışı ortalama **400 TL/kg** (başabaş analizi: 700 TL) |
| **Doku kültürü fidan** | Viyolde 216 adet ≈ 5.250-5.540 TL (~25 TL/ad) · tüplü tek tek 250 TL (Chester, Loch Ness, Triple Crown) | Viyol 26 TL + kendi alıştırman 20 TL = **46 TL/ad** · 2 yaşlı tüplü toplu **150 TL/ad** |
| **Tarım işçisi yevmiyesi (Bursa)** | İnegöl 1.100-1.250 TL · İznik 1.500 TL (net, 8 saat) | **1.400 TL + %10 dayıbaşı** → paket kalitesinde hasat 28 TL/kg, dökme 22 TL/kg |
| **Asgari ücret (işveren maliyeti)** | Net 28.075 TL, işveren ~40.214 TL/ay | Sezonluk işçi (yalnız 20 da) |
| **Damla sulama sistemi** | 9.000-12.000 TL/da | 10.000 TL/da + ana hat/filtre |
| **Galvaniz direk / tel** | Boru direk 240 cm 160-200 TL · galvaniz tel 75 TL/kg | 2,7 m ağır direk **350 TL** · tel 75 TL/kg |
| **Soğuk oda paneli** | 100 mm panel 890-1.050 TL/m² | Kendi yapımın soğuk oda ~110.000 TL (panel + kapı + inverter klima + kontrolör) |
| **Plastik tünel / sera** | Basit plastik tünel 400.000-800.000 TL/da · plastik sera ~850 TL/m² + 180 TL/m² altyapı | Yüksek tünel **600.000 TL/da** |
| **Topraksız çilek serası** | Kurulum 3,8-5,6 M TL/da | Karşılaştırma için |
| **PET kap** | 250 cc kapaklı kap ~2,9 TL/ad (100'lük) | Kap + etiket + koli **25 TL/kg** |

### Böğürtlen fiyatının mevsimselliği (modelin temeli)

| Ay | Hal fiyatı varsayımı (TL/kg) | Açık tarla hasat payı |
|---|---:|---:|
| Haziran | 450 | %5 |
| Temmuz | 250 | %30 |
| Ağustos | 180 | %35 |
| Eylül | 220 | %20 |
| Ekim | 300 | %10 |
| **Ağırlıklı (−%15 hacim/kalite iskontosu ile)** | **199** | |

**Okuma:** Haziran (erken) ve ekim (geç) fiyatları temmuz-ağustostaki tepe dönemin 2-2,5 katı. Bu yüzden 3 çeşitli portföy (Loch Ness erken, Chester geç, Prime-Ark sonbahar) yalnızca riski değil fiyatı da iyileştiriyor.

> ⚠️ **En önemli belirsizlik:** Bursa halinde 16 Eylül'de böğürtlen 60-70 TL/kg'dan işlem görmüş. Bu muhtemelen yabani/düşük kalite ya da sezon sonu fazlası. Ama yerel halin büyük şehir hallerinden çok daha düşük fiyatlayabileceğini gösteriyor. Bu yüzden: (i) ortakla **taban fiyatlı** sözleşme şart; (ii) ürünü İstanbul/Bursa merkez kanallarına yönlendirmek gerekiyor; (iii) her sonucu **−%30 fiyat** senaryosuyla birlikte değerlendir (Bölüm 7).

---

## 2. Ceviz Ağaçlarının Arası

| Sorun | Açıklama |
|---|---|
| **Juglon zehirlenmesi** | Ceviz kökleri, yaprakları ve kabukları juglon salgılar. Böğürtlen (Rubus spp.) juglona hassas bitkiler arasında listeleniyor: solgunluk, sararma, gelişme geriliği. Etki taç izdüşümünün 1,5-2 katına kadar uzanabilir |
| **Gölge** | Böğürtlen tam güneş ister. Gölgede çiçek ve meyve sayısı düşer, meyve küçülür |
| **Kök rekabeti** | Ceviz derin ve geniş köklüdür; su ve besinde rekabet eder, fertigasyonun etkinliği düşer |
| **Telli sistem** | Ağaç sıraları arasında düzgün, uzun sıralar kurulamaz; makineyle ilaçlama ve ot biçme zorlaşır |
| **İlaçlama çatışması** | Cevizin mücadele takvimi (ceviz iç kurdu vb.) böğürtlen hasadına denk gelir; kalıntı riski |

**Sonuç:** Cevizli tarlada böğürtlen yalnızca ağaçlardan **en az 15-20 m uzaktaki boş kenar şeritlerinde** düşünülebilir. Cevizin altı için çayır/mera, arıcılık ya da juglona dayanıklı bitkiler uygun. Böğürtlen için ayrı, temiz bir parsel (165/9'daki 10 da) çok daha doğru.

---

## 3. 10 Dönümde Daha Fazla Kazanmanın Yolları: Seçenekler

### 3.1 Kanal başına kg katkısı (hasat ve kanal giderleri düşülmüş)

| Kanal | kg başı katkı (TL) | USD |
|---|---:|---:|
| Kendin-topla (perakende, hasat işçiliği yok) | 360 | 7,33 |
| Tünel ahududu (ortak, sezon dışı) | 254 | 5,17 |
| Böğürtlen, ortak üzerinden paketli | 188 | 3,83 |
| Böğürtlen, hal | 149 | 3,04 |
| Böğürtlen, 2. sınıf işleme | 38 | 0,77 |

### 3.2 Beş seçenek

| Seçenek | İçerik |
|---|---|
| **A** | 10 da açık tarla böğürtlen; ortak (paketli) + hal |
| **B** | A + yol kenarındaki 1-2 da'da hafta sonu **kendin-topla** (yılda ~1,5-2 t perakende satış) |
| **C** | 8,5 da böğürtlen + **1 da yüksek tünelde saksılı ahududu** (sezon dışı: Mayıs-Haziran + Ekim-Kasım) + kendin-topla |
| **D** | 20 da böğürtlen + kendin-topla |
| **E** | 17,5 da böğürtlen + 2 da tünel ahududu + kendin-topla |

Sonuçlar Bölüm 0'daki tabloda. **B, 10 dönümün en iyi seçeneği; C ondan kötü.** Nedenleri:

- **Tünel pahalı:** 1 da tünel + saksı + fidan ~1,2 M TL. Saksılar 3 yılda bir yenileniyor, plastik 4-5 yılda bir.
- **Ahududu kg başı daha kazançlı ama verim düşük:** Ahududu dönümde ~2 t veriyor (tünelde), toplaması iki kat yavaş.
- **Başabaş fiyat:** Tünel ahududu ancak **ortalama satış fiyatı ≥ ~700 TL/kg** olursa B'yi geçiyor. Nisan ithal ve sera ürünü 1.400-2.300 TL'den satılıyor, ama yerli Mayıs-Haziran ve Ekim-Kasım ürününün fiyatı belirsiz.

**Diğer alternatifler neden yok:**

- **Domates serası:** Dönümde ~25-30 t × ~25 TL/kg, yıllık net ~500 bin-800 bin TL. Ama günlük budama, askı ve hasat gerektirdiği için Ankara'dan yönetilemez; Karacabey açık tarla domatesiyle de rekabet ediyor.
- **Topraksız çilek:** Kurulum 3,8-5,6 M TL/da. Ek gelir hedefi için sermaye yoğun.
- **"Çok katlı" / dikey sistem:** Böğürtlen 2-3 m'lik odunsu bir bitki; rafa ve yapay ışığa uygun değil.
- **Farklı yaşta bloklar:** Gelir katmıyor. Çeşit portföyü (erken/geç) asıl faydayı zaten sağlıyor.

**Kendin-topla neden işe yarar:** Bursa (~3 M nüfus) ~40-50 dk, TEKNOSAB'ta 9.000+ çalışan var. Hafta sonu aile etkinliği olarak kg başı 400 TL perakende satılıyor, toplama işçiliği yok. Yalnızca ürünün ~%10'u bu kanaldan gitse bile yıllık net gelir ~280 bin TL artıyor.

### 3.3 Önerilen alan yerleşimi (10 da)

| Alan | Kullanım |
|---|---|
| ~8,7 da | Açık tarla böğürtlen: 3 m × 0,75 m sık dikim. %70 doku kültürü (viyolden kendi alıştırdığın), %30 2 yaşlı tüplü. Çeşitler: Loch Ness (erken) + Chester (geç) + Prime-Ark (sonbahar) |
| ~1 da (yola bakan sıralar) | Böğürtlenin kendin-topla bölümü: geniş sıra başı, gölgelik, tabela, otopark, portatif WC |
| ~0,3 da | Soğuk oda, depo ve alet alanı, sensör/kontrol kabini, **300 m²'lik deneme tüneli** (Prime-Ark ya da ahududu; sezon dışı fiyatı ölçmek için, tünel + saksı + fidan ~300-350 bin TL, isteğe bağlı, modele dahil değil) |

---

## 4. Önerilen Plan (B): Yatırım Kalem Kalem

| Faz | Grup | Kalem | Miktar | TL | USD |
|---|---|---|---|---:|---:|
| 0 | Arazi | Toprak analizi, dip kazan, lazer tesviye, sedde | 10,0 da | 97.200 | 1.980 |
| 0 | Arazi | Yanmış çiftlik gübresi 4 t/da | 40 t | 86.400 | 1.760 |
| 0 | Arazi | Agrotekstil malç örtü (sedde üstü) | 3.400 m² | 91.800 | 1.870 |
| 0 | Fidan | Doku kültürü fidan, viyolde (216'lık viyol ~5.300 TL) + 2-3 ay saksıda alıştırma (kendin) | 3.171 ad × 46 TL | 157.535 | 3.208 |
| 0 | Fidan | 2 yaşlı tüplü sertifikalı fidan (hızlı blok, %30) | 1.359 ad × 150 TL | 220.158 | 4.484 |
| 0 | Fidan | Dikim işçiliği |  | 27.000 | 550 |
| 0 | Telli sistem | Galvaniz direk 2,7 m, 8 m ara + baş direkleri | 483 ad × 350 TL | 182.432 | 3.716 |
| 0 | Telli sistem | Galvaniz tel 3 kat (75 TL/kg) + gergi/ankraj + montaj | 9.999 m | 117.987 | 2.403 |
| 0 | Sulama | Damla: basınç ayarlı çift lateral (~10.000 TL/da) + hidrant bağlantısı, disk filtre, ana hat |  | 172.800 | 3.519 |
| 0 | Teknoloji | Fertigasyon: ESP32 kontrolör, selenoid vanalar, venturi, asit pompası, hat içi EC/pH |  | 108.000 | 2.200 |
| 0 | Teknoloji | LoRaWAN gateway + 4G router |  | 23.760 | 484 |
| 0 | Teknoloji | Toprak düğümü: ESP32-LoRa + 2 RS485 nem/EC/sıcaklık probu + solar | 6 × 13.500 TL | 87.480 | 1.782 |
| 0 | Teknoloji | Referans prob + meteoroloji istasyonu (yaprak ıslaklığı) |  | 75.600 | 1.540 |
| 0 | Teknoloji | Debimetre/basınç, mini PC + UPS, solar 4G kamera |  | 75.600 | 1.540 |
| 0 | Diğer | ÇKS, tarımsal yapı izni, proje |  | 32.400 | 660 |
| 1 | Soğuk zincir | DIY soğuk oda: 100 mm panel (~32 m² × 1.000 TL), kapı, inverter klima 24k BTU, kontrolör, ön soğutma fanı |  | 118.800 | 2.420 |
| 1 | Soğuk zincir | Monofaze/trifaze elektrik bağlantısı + pano |  | 43.200 | 880 |
| 1 | Hasat | NFC tartı (kendin), terazi, QR etiket yazıcı, sıcaklık logger, kasa/arabalar |  | 81.000 | 1.650 |
| 1 | Hasat | Gıda işletme kaydı + İyi Tarım belgesi |  | 54.000 | 1.100 |
| 1 | Kalite | %35 gölge filesi + montaj | 5.000 m² | 226.800 | 4.619 |
| 1 | Kendin-topla | Tabela, otopark düzeni, portatif WC, gölgelik, satış tezgâhı, terazi |  | 64.800 | 1.320 |
| | | **Faz 0 — kurulum (Q4-2026 / Q1-2027)** | | **1.556.152** | **31.694** |
| | | **Faz 1 — ilk büyük hasattan önce (2027 sonu)** | | **588.600** | **11.988** |
| | | **BAŞLANGIÇ YATIRIMI TOPLAMI** | | **2.144.752** | **43.681** |

*%8 beklenmeyen gider payı dahildir. Yenilemeler (elektronik, file, tünel plastiği, saksı) 10 yıllık nakit akışında ayrıca yer alır.*

**Önceki rapora (v7) göre fark:** Fidan bütçesi v7'deki ~1,0 M TL yerine güncel fiyatlarla ~405 bin TL. Doku kültürü fidanı viyolden alıp 2-3 ay saksıda kendin alıştırırsan adet maliyeti ~46 TL'ye iniyor. Soğuk oda reefer + trifaze yerine kendi yaptığın panel oda (elektrik bağlantısıyla ~160 bin TL).

---

## 5. İşletme Giderleri (B)

| Sabit gider (TL/yıl) | 2027 | 2028 | 2029 | 2030 | 2031+ |
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

**Değişken giderler (kg başı):** paket kalitesinde hasat 28 TL, dökme hasat 22 TL, kap + etiket + koli 25 TL, ortağa yükleme 5 TL, hal komisyonu %10 + kasa 8 TL, kendin-topla görevli/kap 40 TL.

---

## 6. 10 Yıllık Gelir, Kâr ve Nakit (B)

| TL | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Böğürtlen (t) | 1,5 | 10,1 | 17,9 | 20,0 | 20,0 | 20,0 | 20,0 | 20,0 | 18,0 | 16,0 |
| — Ortak üzerinden paketli | 145k | 1.399k | 2.582k | 2.854k | 2.795k | 2.755k | 2.755k | 2.755k | 2.440k | 2.125k |
| — Hal | 105k | 340k | 471k | 520k | 509k | 502k | 502k | 502k | 445k | 387k |
| — Kendin-topla | 0k | 200k | 480k | 600k | 720k | 800k | 800k | 800k | 800k | 800k |
| — 2. sınıf → işleme | 19k | 131k | 233k | 260k | 260k | 260k | 260k | 260k | 234k | 208k |
| **Gelir** | **269k** | **2.070k** | **3.765k** | **4.234k** | **4.284k** | **4.317k** | **4.317k** | **4.317k** | **3.919k** | **3.521k** |
| Değişken gider (hasat, kap, kanal) | −60k | −461k | −832k | −928k | −924k | −922k | −922k | −922k | −827k | −732k |
| Sabit gider | −341k | −548k | −623k | −649k | −659k | −659k | −659k | −659k | −659k | −659k |
| **FAVÖK** | **−131k** | **1.061k** | **2.310k** | **2.657k** | **2.701k** | **2.737k** | **2.737k** | **2.737k** | **2.433k** | **2.130k** |
| Amortisman | −205k | −295k | −295k | −295k | −295k | −196k | −180k | −180k | −190k | −175k |
| Stopaj %2 | −5k | −41k | −75k | −85k | −86k | −86k | −86k | −86k | −78k | −70k |
| **Net kâr** | **−342k** | **724k** | **1.940k** | **2.277k** | **2.320k** | **2.454k** | **2.470k** | **2.470k** | **2.165k** | **1.884k** |
| Aylık net | −28k | 60k | 162k | 190k | 193k | 205k | 206k | 206k | 180k | 157k |
| Yatırım / yenileme | −589k | 0k | 0k | 0k | 0k | −120k | 0k | −295k | 0k | 0k |
| **Kümülatif nakit** | **−2.282k** | **−1.262k** | **973k** | **3.545k** | **6.160k** | **8.691k** | **11.341k** | **13.697k** | **16.052k** | **18.237k** |

*Tutarlar bin TL (k), 2026 sabit fiyatlarıyla.*

---

## 7. Stres Testi (B)

| Senaryo | 2031 net | Geri dönüş | 10 yıl IRR |
|---|---:|---:|---:|
| Baz | 2,32 M TL | 2,6 yıl | %58,6 |
| Tüm fiyatlar −%30 | 1,06 M TL | 3,6 yıl | %32,8 |
| Verim −%25 | 1,58 M TL | 3,1 yıl | %44,3 |
| İşçilik +%40 (TEKNOSAB) | 2,08 M TL | 2,7 yıl | %53,9 |
| Ortak fiyatı hal fiyatına iner (200 TL) | 1,41 M TL | 3,2 yıl | %40,6 |
| Fiyat −%30 + verim −%15 + işçilik +%20 | 0,69 M TL | 4,4 yıl | %22,7 |

- **Fiyat −%30 bile kârlı:** 2031 net ~1,06 M TL, geri dönüş 3,6 yıl. Önceki raporlardaki baz senaryodan hâlâ iyi.
- **Ortak fiyatı hal seviyesine (200 TL) inerse** ek gelir ~%40 düşer. Sözleşmede taban fiyat bu yüzden kritik.
- **Üçlü şok** (fiyat −%30, verim −%15, işçilik +%20) gelse bile yatırım 4,4 yılda geri dönüyor.

---

## 8. 20 Dönüm (D) Ne Değiştirir?

| Senaryo | 2031 net | Geri dönüş | 10 yıl IRR |
|---|---:|---:|---:|
| Baz | 4,43 M TL | 2,5 yıl | %61,6 |
| Tüm fiyatlar −%30 | 2,00 M TL | 3,5 yıl | %33,9 |
| Verim −%25 | 2,95 M TL | 3,0 yıl | %45,7 |
| İşçilik +%40 (TEKNOSAB) | 3,94 M TL | 2,6 yıl | %56,2 |
| Ortak fiyatı hal fiyatına iner (200 TL) | 2,48 M TL | 3,2 yıl | %40,4 |
| Fiyat −%30 + verim −%15 + işçilik +%20 | 1,25 M TL | 4,4 yıl | %22,4 |

20 dönümde (D) başlangıç yatırımı ~3,8 M TL, 2031 net ~4,4 M TL/yıl. Sezonluk bir saha işçisi ve ikinci bir soğuk oda gerekiyor. Satılması gereken ürün 40 tona çıktığı için fiyat baskısı riski artıyor; ortak kapasitesi ve taban fiyatı 20 dönümde daha da kritik.

**Önerilen yol:** 2027'de 10 da (B). 2028 sezonunda ≥ 9 t ortalama ≥ 180 TL/kg net fiyatla satılırsa, ikinci 10 da 2029 ilkbaharında dikilir (ek ~1,7 M TL).

---

## 9. Neden Önceki Raporlardan Bu Kadar Farklı?

| Kalem | v7 varsayımı (USD, 47 TL) | v8 güncel veri (TL) | Etki |
|---|---|---|---|
| Hal fiyatı | $2,50 ≈ 118 TL/kg | Ağırlıklı ~199 TL/kg | Gelir ↑ |
| Paketli üretici fiyatı | $5,65 ≈ 266 TL/kg | 300 TL/kg | Gelir ↑ |
| Doku kültürü fidan | $3,0 ≈ 141 TL/ad | Viyol ~25 TL + alıştırma | Yatırım ↓ |
| Saksılı fidan | $6,5 ≈ 306 TL/ad | Tüplü toplu ~150 TL | Yatırım ↓ |
| Hasat işçiliği | $0,70 ≈ 33 TL/kg | 28 TL/kg (yevmiye 1.400 TL) | Gider ↓ |
| Soğuk oda | 20' reefer + trifaze ~$15,6k (~765 bin TL) | Kendi yapımın panel oda + bağlantı ~160 bin TL | Yatırım ↓ |

Önceki raporlar bilinçli olarak temkinliydi, ama güncel veriye göre fazla temkinli kalmış. Gerçek fiyat büyük ölçüde **ürünün hangi kanaldan ve hangi ayda satıldığına** bağlı. İlk sezonun (2028) gerçek satış verisi bütün bu tahminlerden daha değerli olacak.

---

## 10. Doğrulama Listesi (yatırımdan önce)

1. **Satış ortağından yazılı fiyat teklifi:** ay bazında kg fiyatı ve taban fiyat.
2. **Bursa ve İstanbul hal kayıtları:** son 2 sezonda kültür böğürtleni (Loch Ness/Chester) için haftalık fiyat. haldefiyat.com ve Bursa Büyükşehir hal sayfası üzerinden.
3. **Fidanlık teklifleri:** viyolde doku kültürü (3 çeşit, toplu fiyat, teslim tarihi) ve 2 yaşlı tüplü fidan (1.300+ adet).
4. **Elektrik:** arazide monofaze/trifaze hat var mı (TEDAŞ).
5. **Kendin-topla için:** belediye ve İl Tarım'a ziyaretçi kabulü, otopark ve WC şartları sorulmalı.

---

### Ek A — Kaynaklar (Ekim 2026)

- Kur: [Halk TV 2 Ekim 2026](https://halktv.com.tr/ekonomi/2-ekim-2026-doviz-kurlari-euro-kac-tl-dolar-kac-tl-sterlin-kac-tl-1058876h), [Gazete Kritik](https://gazetekritik.com/ekonomi/dolartl-ve-doviz-kurlari-bugun-ne-kadar-dolar-4914-tl-seviyesinde/415113)
- Böğürtlen hal: [haldefiyat — böğürtlen](https://haldefiyat.com/urun/bogurtlen), [Tarım Ziraat — böğürtlen fiyatları](https://www.tarimziraat.com/fiyat/bogurtlen_fiyatlari-a97.html), [Bursa Büyükşehir hal fiyatları](https://www.bursa.bel.tr/hal_fiyatlari)
- Raf fiyatı: [Migros böğürtlen 125 g](https://www.migros.com.tr/hemen/bogurtlen-125-g-p-19cc015), [CarrefourSA böğürtlen 125 g](https://www.carrefoursa.com/bogurtlen-125-g-p-30149587)
- Ahududu: [haldefiyat — ahududu](https://haldefiyat.com/urun/ahududu), [Tarım Ziraat — ahududu](https://www.tarimziraat.com/fiyat/ahududu_fiyatlari-a1268~2.html), [Hanım Köylü — ahududu kârlılık](https://www.hanimkoylu.net/ahududu-yetistirmek-karli-mi-gercekci-karlilik-analizi/)
- Fidan: [Elma Tarım — doku kültürü Chester](https://elmatarim.com.tr/urun/doku-kulturuyle-uretilmis-chester-bogurtlen-fidani/), [Bursa Tarım Market — doku kültürü çoklu satış](https://www.bursatarimmarket.com/doku-kulturu-ile-coklu-satis), [Fidandeposu](https://www.fidandeposu.com/dikensiz-bogurtlen-fidani)
- Yevmiye ve asgari ücret: [Bursadabugün — Bursa tarım işçisi tarifesi](https://www.bursadabugun.com/haber/bursa-da-tarim-iscilerine-gunluk-ne-kadar-odenecek-yeni-tarife-belli-oldu-1923814.html), [Sanayi Gazetesi — 2026 yevmiyeler](https://sanayigazetesi.com.tr/2026-sezonluk-isciucretleri/), [QNB — 2026 asgari ücret](https://www.qnbinvest.com.tr/investodak/qnbarastirma/2026-asgari-ucret-aciklandi-net-28075-tl)
- Sulama, direk, panel: [Tarım Memleketi — damla sulama](https://tarimmemleketi.com/1-donum-damla-sulama-maliyeti), [Panel Çit Ankara — boru direk](https://www.panelcitankara.com/urundetay/boru-direk), [Yapıpan — soğuk oda paneli](https://yapipanmetal.com/urun/sandvic-panel/sandvic-soguk-oda-paneli-100mm-ral-9002/)
- Sera: [Hidroponik Farm — sera maliyet hesaplama](https://hidroponikfarm.com/pages/sera-kurulum-maliyeti-hesaplama), [Tarım Sosyal — 1 dönüm sera geliri](https://tarimsosyal.com/blog/1-donum-seradan-ne-kadar-kazanilir-2026-guncel-gelir-gider-analizi), [Tarım Memleketi — topraksız çilek](https://tarimmemleketi.com/1-donum-topraksiz-cilek-sera-maliyeti)
- Juglon: [Ontario — walnut toxicity](https://ontario.ca/page/walnut-toxicity), [Morton Arboretum](https://mortonarb.org/?p=87881)
- Ambalaj: [n11 — 250 cc kapaklı kap](https://www.n11.com/arama?m=Pgs)
