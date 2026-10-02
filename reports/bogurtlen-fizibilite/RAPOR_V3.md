# Muratlı Berry Lab — Fizibilite v3: Hibrit Model, Mevsim Riskleri, Yıllık Takvim, 20 Dönüm Planı ve 10 Yıllık Projeksiyon

**Kapsam:** 10 da pilot + **20 da hedef işletme** dikensiz böğürtlen (3 çeşitli portföy). Kanal planı: taze çoğunluk (100/200/500 g + kurumsal paket), dondurulmuş (IQF) ve liyofilize (fason) yan kanallar. Soğuk zincir ve AgTech altyapısı v2'den devralınır.
**Lokasyon:** Bursa / Karacabey / Muratlı Mah. · **Kurucu:** Ankara merkezli, düzenli saha ziyaretli uzaktan yönetim
**Rapor tarihi:** 2 Ekim 2026 · **Sürüm:** v3 (v2'yi günceller; CAPEX kalem detayı için v2 Bölüm 3 geçerlidir)
**Para birimi:** 2026 sabit fiyatlarıyla USD (reel); 1 USD = 47 TL
**Hesap modeli:** [`model_v3.py`](model_v3.py) (`--tables` ve `--mc` ile tüm tablolar yeniden üretilebilir)

---

## 0. Yönetici Özeti

**Sorularının kısa cevapları:**

1. **Böğürtlen doğru seçim mi?** Evet. Toprak (pH 7-7,5, killi-tınlı), DSİ suyu, iklim, taze + dondurulmuş + liyofilize hibrit kanal ve teknoloji konsepti birlikte değerlendirildiğinde en dengeli seçenek böğürtlen. İki değişiklik öneriyorum: (a) tek çeşit yerine **3 çeşitli portföy** kur; hasat sezonu 6 haftadan **haziran ortası–ekim sonu arasında ~4,5 aya** yayılıyor. (b) Living lab içinde **1 da ahududu pilotu** dene; ahududu liyofilize pazarının en değerli meyvesi.
2. **Mevsim risklerini gözünde mi büyütüyorsun?** Kısmen evet. 5.000 senaryoluk risk simülasyonunda bu plandaki önlemlerle **olgun bir yılın zararla kapanma olasılığı %0,1**. Önlemsiz kurulan bir bahçede bu oran %17,1. Mevsim riskleri ölçülebilir ve büyük ölçüde yönetilebilir. Asıl riskler başka yerde: **pazar** (sezonda günde 300-500 paketin satılabilmesi), **ölçek** (10 da'da sabit giderler ağır kalıyor) ve **uzaktan yönetim** (sahadaki teknisyenin kalitesi).
3. **20 dönüm planı?** Bölüm 7'de: iki seçenek (tek seferde / kademeli), ek yatırım, organizasyon, kapasite ve 10 yıllık tablolar.
4. **Yılın nasıl geçecek?** Bölüm 3'te ay ay anlatılıyor. Olgun bir yılda haziran ortasından ekim sonuna kadar **~60 hasat günü** var. Her bitki yılda **15-20 kez** toplanıyor ve hasat 2-3 günde bir tekrarlanıyor. Sen yılda **~30 ziyaretle** yönetiyorsun: kışın ayda 1, hasat zirvesinde haftalık veya sahada kalarak.

**10 yıllık tablo — üç plan (baz senaryo):**

| Gösterge | 10 da | 20 da — tek seferde (2027) | 20 da — kademeli (2027 + 2029) |
|---|---:|---:|---:|
| Toplam yatırım (10 yıl, yenileme dahil) | $134.910 | $193.459 | $193.459 |
| 2032 rekolte | 20 t | 40 t | 40 t |
| 2032 gelir | $122.427 | $220.017 | $220.017 |
| 2032 vergi öncesi kâr | $30.642 | $67.215 | $65.784 |
| 10 yıl toplam gelir | $901.543 | $1.626.926 | $1.487.220 |
| 10 yıl toplam net kâr | $81.991 | $251.306 | $218.968 |
| Proje IRR | %9,5 | %16,7 | %15,0 |
| Özsermaye IRR (kredili) | %12,0 | %21,4 | %19,1 |
| Proje NPV (%12) | −$15.631 | $46.210 | $27.719 |
| Geri dönüş (kaldıraçsız) | 6,9 yıl | 5,8 yıl | 6,6 yıl |
| Azami özsermaye ihtiyacı | $103.797 | $133.058 | $129.462 |

**Karar: Hedef işletme 20 da.** 10 da tek başına "iyi bir tarım işletmesi" düzeyinde kalıyor: düşük riskli, pozitif nakit üretiyor, ama %12 hedefin altında (IRR %9,5). Soğuk zincir, pakethane, dondurucu ve AgTech altyapısı ancak 20 da'da tam kullanılıyor ve getiri %15-17'ye çıkıyor (Bölüm 7).
- **Varsayılan yol: kademeli 20 da.** 2027'de 10 da, 2029'da ikinci 10 da. İkinci bloğun $30.445'lik tarla yatırımı, 2028 satış verisi görüldükten sonra (Kapı 2) yapılıyor.
- **Tek seferde 20 da**, ancak **Mart 2027'den önce** yılda ≥ 5 t'luk bir kurumsal ortak veya ön sözleşme sağlanırsa seçilmeli. IRR'si 1,7 puan daha yüksek, ama pazarı görmeden iki kat ürünü satmayı varsayıyor.

---

## 1. Böğürtlen Bu Senaryoda En Mantıklı Seçim mi?

### 1.1 Aday ürünlerin karşılaştırması

Puanlar 1 (zayıf) ile 5 (güçlü) arasında, bu arazi ve bu iş modeli için verildi.

| Kriter | **Dikensiz böğürtlen** | Ahududu | Yaban mersini | Çilek (tünel) | Aronya | Kiraz | Goji |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Toprak uyumu (pH 7-7,5, killi-tınlı) | **5** | 3 (kök çürüklüğüne hassas) | 1 (pH 4,5-5,5 ister) | 3 | 5 | 3 (ağır toprakta riskli) | 5 |
| Karacabey iklimi (yaz 35 °C+) | **4** (fileyle) | 2 (sıcağa hassas) | 3 | 3 | 5 | 4 | 5 |
| İlk ürün / tam verim | **1. yıl az / 4. yıl** | 1. yıl / 3. yıl | 3. / 6-7. yıl | 1. yıl / her yıl dikim | 3. / 5. yıl | 4. / 7-8. yıl | 2. / 4. yıl |
| Kurulum maliyeti | **3** | 3 | 1 (saksı + RO, v1) | 2 | 4 | 4 | 4 |
| İşçilik yoğunluğu (5 = az) | 3 | 2 | 3 | 1 | 5 (makineli hasat) | 3 | 3 |
| Taze pazar talebi ve fiyatı | **4** (arz az) | 5 | 5 | 3 (arz çok) | 1 (taze yenmez) | 4 (arz çok) | 1 |
| Dondurulmuş / liyofilize uygunluğu | **4** | 5 | 4 | 4 | 3 | 2 | 3 |
| Raf ömrü (taze) | 3 (soğuk zincirle 7-10 gün) | 2 (3-5 gün) | 5 | 2 | – | 4 | – |
| Bölgede rekabet (5 = az) | **5** | 4 | 4 | 2 | 4 | 2 | 4 |
| Teknoloji / izlenebilirlik değeri | 4 | 4 | 4 | 5 | 2 | 3 | 2 |
| **Toplam (yaklaşık)** | **~39** | ~35 | ~31 | ~28 | ~33 | ~29 | ~30 |

**Sonuç:**
- **Böğürtlen** bu arazinin doğal yapısıyla (nötr pH, derin toprak, bol su) en uyumlu yüksek değerli meyve. Bölgede ticari dikensiz böğürtlen üreticisi az olduğu için taze pazarda rekabet sınırlı.
- **Ahududu** daha pahalı satılıyor ve liyofilize pazarında en çok aranan meyve. Ancak sıcağa ve ağır topraktaki kök çürüklüğüne hassas. Bu nedenle ana ürün değil, **living lab'de 1 da pilot** olarak öneriyorum (Y3, ~$3.500; sonbahar ürünlü primocane çeşitlerle). Başarılı olursa ikinci blokta %20-30 pay alabilir.
- **Aronya** toprağa ve iklime en dayanıklı seçenek, ama taze tüketilmediği için paketli taze modeline uymuyor. Tamamen işleme odaklı bir senaryoda düşünülebilir.
- **Yaban mersini** v1'de saksı + RO maliyeti ($185k+) nedeniyle elenmişti; bu karar geçerli.

### 1.2 Neden üç çeşit?

| Çeşit | Alan payı | Tip | Hasat penceresi (Karacabey, tahmini) | Tam verim |
|---|---:|---|---|---:|
| Loch Ness | %30 (3 da) | floricane, yarı dik | 5 Tem – 10 Ağu | 2,2 t/da |
| Chester | %40 (4 da) | floricane, yarı yatık, geç | 25 Tem – 10 Eyl | 2,0 t/da |
| Prime-Ark Freedom / Traveler | %30 (3 da) | primocane (1. yıl kolda sonbahar ürünü) | 15 Haz – 5 Tem (az) + 1 Eyl – 31 Eki | 1,6 t/da |

Ağırlıklı tam verim ≈ **1,94 t/da** (modelde 2,0 t/da). Portföyün faydaları:
1. **Hasat 6 haftadan ~4,5 aya yayılıyor.** Günlük tepe hacim yarıya iniyor; daha az işçi, daha küçük soğuk oda ve daha kolay satış demek.
2. **Risk dağılıyor.** Bir sıcak dalgası, yağış veya fiyat çöküşü sezonun yalnız bir bölümünü vuruyor.
3. **Primocane çeşit dikim yılında (2027 sonbaharı) ürün veriyor.** Erken nakit ve pazar testi için fırsat.

> ⚠️ Prime-Ark Freedom ve Prime-Ark Traveler, Arkansas Üniversitesi'nin lisanslı çeşitleri. Türkiye'de sertifikalı ve doku kültürü tedariki fidanlıklarla doğrulanmalı. Bulunamazsa Chester ile birlikte, olgunlaşma tarihi farklı dikensiz çeşitler (ör. Triple Crown, Navaho) kullanılarak benzer bir yayılım kurulabilir.

---

## 2. Böğürtleni Tanımak

### 2.1 Biyolojisi: anlaman gereken tek şey

- **Kök ve taç çok yıllık** (ekonomik ömür 12-15 yıl), **kollar (kamçılar) iki yıllık.**
- **1. yıl kolu = primocane.** İlkbaharda topraktan çıkar ve büyür. Floricane çeşitlerde bu yıl meyve vermez.
- **2. yıl kolu = floricane.** Aynı kol ikinci yazında çiçek açar, meyve verir ve **ölür.** Hasattan sonra dipten kesilir.
- Yani her yaz bitkide iki kuşak kol yan yana bulunur: meyve veren yaşlılar ve gelecek yılın meyvesini taşıyacak gençler. **Böğürtlen yönetiminin özü, bu iki kuşağı tele doğru bağlayıp ayırmak.**
- **Primocane çeşitler** (Prime-Ark) 1. yıl kolunun ucunda, sonbaharda da meyve verir. Bu yüzden dikim yılında ürün alınabiliyor.
- **Kendine verimli** (tozlayıcı çeşit gerekmez), ama arılar meyve tutumunu ve iriliğini artırır. Modelde çiçeklenmede 15 kovan kiralanıyor.
- **Kök boğulmasına hassas.** Seddeli dikim ve damla sulama zorunlu. Toprak nemi sensörü burada gerçek bir değer üretiyor.

### 2.2 Hasat: kaç kez, nasıl?

| Soru | Cevap |
|---|---|
| Bir çeşidin hasat süresi | 4-7 hafta |
| Hasat sıklığı | Aynı sıra **2-3 günde bir** toplanır. SWD sineği nedeniyle 3 günü geçmemeli |
| Bir bitki yılda kaç kez toplanır | **15-20 kez** |
| Yılda toplam hasat günü (3 çeşit) | **~60 gün** (haziran ortası – ekim sonu, çakışmalarla) |
| Tepe dönem | 25 Temmuz – 10 Ağustos (Loch Ness + Chester üst üste) |
| Tepe günlük hacim | ~400-450 kg/gün → **7-8 toplayıcı** |
| Günlük çalışma saatleri | 05:30-11:00 hasat (serin saatler), 2 saat içinde ön soğutma, öğleden sonra paketleme, akşam sevkiyat |
| Olgunluk ölçütü | Parlak siyahtan **mat siyaha** dönen meyve. Parlak siyah meyve henüz ekşidir |
| Toplama biçimi | Paketli ürün doğrudan tarlada punnet'e toplanır (ikinci kez elleme yok) |

### 2.3 Bitkinin hayat eğrisi

| Yaş | Dönem | Verim (10 da, baz) |
|---|---|---:|
| 2027 (1. yıl) | Dikim, primocane büyümesi; Prime-Ark'ta sonbahar ürünü | 0,5 t |
| 2028 (2. yıl) | İlk floricane hasadı | 5,5 t |
| 2029 (3. yıl) | Kanopi doluyor | 14,5 t |
| 2030-2034 | Tam verim | 20 t |
| 2035-2036 | Hafif yaşlanma | 18 → 16 t |
| 2037+ | Yenileme kararı: kısmi yeniden dikim veya gençleştirme budaması | – |

---

## 3. Bir Yılın Nasıl Geçecek: Dönem Dönem

### 3.1 Kuruluş dönemi (Ekim 2026 – Aralık 2027)

| Dönem | Sahada | Masada (Ankara'dan) | Ziyaret |
|---|---|---|---|
| **Ekim-Kasım 2026** | Toprak analizi, dip kazan (toprak kuruyken), lazer tesviye, 40 t organik gübre, sedde yapımı (kış yağmurlarından önce) | Ltd. kuruluşu, Ziraat Faz 1 kredi başvurusu (**31.12.2026 öncesi**), elektrik keşfi, 5403 yapı izni başvurusu, fidan siparişi (3 çeşit) | 3-4 ziyaret |
| **Aralık 2026 – Şubat 2027** | Telli terbiye direkleri ve teller, ana sulama hattı | Teknisyen işe alımı (Şubat'tan itibaren), sensör düğümlerinin tasarımı ve prototipi, ambalaj ve marka tasarımı | Ayda 1 |
| **Mart 2027** | Lateraller, fertigasyon ünitesi, malç örtü, gateway + meteoroloji istasyonu | Edge sunucu ve panel yazılımının ilk sürümü | 2 ziyaret |
| **Nisan 2027** | **Dikim** (doku kültürü fidanlar, don riskinden sonra), ilk sulama ayarları, kameralar | Alarm kuralları (don, kuru toprak, güvenlik) | 2 ziyaret, dikim haftası sahada |
| **Mayıs-Ağustos 2027** | Primocane'lerin büyümesi; kolların tele bağlanması (2 haftada bir), ot kontrolü, tuzaklar, ilk sezon IPM | Sensör verisiyle sulama modelinin kalibrasyonu, alıcı görüşmeleri, KKYDP başvurusu | Ayda 2 |
| **Eylül-Ekim 2027** | **İlk hasat: Prime-Ark sonbahar ürünü (~0,5 t)**. Yerel satış ve numune dağıtımı | Fiyat ve paket testi, alıcılardan geri bildirim | Ayda 2 |
| **Kasım-Aralık 2027** | Kış hazırlığı, toprak analizi | **Kapı 1:** ≥ 2 alıcı ön anlaşması → Faz 2 (soğuk zincir + pakethane) siparişi | Ayda 1 |

### 3.2 Olgun bir yıl (2030 ve sonrası) — ay ay

| Ay | Bitkide ne oluyor | Saha işleri | Teknoloji ne yapıyor | Ticaret ve yönetim | Senin ziyaretin |
|---|---|---|---|---|---|
| **Ocak** | Dinlenme | **Kış budaması:** bitki başına 4-6 sağlam kol bırak, yan dalları 30-45 cm'ye kısalt, tele yelpaze şeklinde bağla. Kış bakır ilaçlaması | Sensör kalibrasyonu, yazılım güncellemesi, geçen sezon verisinin analizi | Yıllık plan; kurumsal ve HoReCa sözleşmeleri; ambalaj siparişi. **Dondurulmuş ve liyofilize stok satışı** | 1 (budama denetimi) |
| **Şubat** | Dinlenme, gözler şişmeye başlar | Budamanın tamamlanması, tel gerginlik kontrolü, damla hat bakımı | Fertigasyon sistemi testi, debimetre kontrolü | Hasat ekibi ön görüşmeleri, sezon kutusu ön siparişi | 1 |
| **Mart** | Uyanma, sürgünler | İlk gübreleme (fertigasyon başlar), ot kontrolü | **Don alarmı aktif** (gece sıcaklığı < 0 °C → bildirim) | Fiyat listesi, distribütör anlaşması | 1-2 |
| **Nisan** | Sürgün gelişimi, yeni primocane'ler çıkar | IPM başlar (akar, yaprak biti), SWD tuzakları kurulur, sıra arası biçim | Toprak nemi/EC ile sulama planı; hastalık modeli (yaprak ıslaklığı) | Living lab pilot anlaşmaları | 2 |
| **Mayıs** | **Çiçeklenme** (Loch Ness → Chester) | Arı kovanları gelir, primocane'ler seyreltilir, sulama artar | Çiçeklenme takibi; meyve sayım kameraları kalibre edilir | İşçi ekibinin kesinleşmesi | 2 |
| **Haziran** | Meyve gelişimi; Prime-Ark ilk küçük hasadı | **Gölge filesi gerilir** (Haziran ortası), primocane bağlama, hasat ekipmanı hazırlığı | **Rekolte tahmini** (kameralar, 3 hafta önceden) → satış miktarları sözleşmelere bağlanır | Soğuk zincir testi, ambalaj stoğu | 2-3 |
| **Temmuz** | **Loch Ness hasadı**, ayın sonunda Chester başlar | 2-3 günde bir hasat, ön soğutma, paketleme; SWD için düşük meyve temizliği | NFC hasat takibi, soğuk zincir alarmları, sıcak dalgasında serinletme sulaması | Günlük sevkiyat, kurumsal teslimatlar | **Haftalık veya sahada kalış** |
| **Ağustos** | **Tepe:** Loch Ness biter, Chester zirvede | Tepe hasat (7-8 toplayıcı), 2. sınıf ve fazla ürün şok dondurucuya | Günlük otomatik saha raporu (LLM); lot bazında izlenebilirlik | Fiyat takibi; bolluk varsa dondurucuya yönlendirme | **Haftalık veya sahada kalış** |
| **Eylül** | Chester biter; **Prime-Ark sonbahar hasadı** başlar | **Meyve vermiş kollar dipten kesilir**; yeni primocane'ler bağlanır | Sezon verisi kapanışı: kg/da, kg/işçi-saat, m³/kg, fire % | Sezon sonu görüşmeleri; liyofilize partisi fasona gönderilir | 2 |
| **Ekim** | Prime-Ark hasadı (ilk sert soğuğa kadar) | Son potasyum gübresi, sıra arası örtü bitkisi ekimi | Yıllık KPI raporu | Gelecek yılın sözleşme müzakeresi; IQF satışı başlar | 2 |
| **Kasım** | Yaprak dökümü | Bakır, toprak analizi, drenaj kontrolü, file sökümü | Donanım bakımı, yedekleme | Muhasebe, hibe ve kredi başvuruları | 1 |
| **Aralık** | Dinlenme | Hafif bakım | Yazılım geliştirme, yeni sensör denemeleri | Living lab proje yazımı, kurumsal yılbaşı kutuları (liyofilize) | 1 |

**Ziyaret toplamı:** ~25-30 (modelde ulaşım ve konaklama için $3.500/yıl ayrıldı). Ankara–Karacabey ~470 km ve ~5 saat. Sezonda, pakethane konteynerine eklenecek basit bir dinlenme alanıyla 3-4 günlük kalışlar en verimlisi.

### 3.3 Hasat sezonunda tipik bir gün

| Saat | İş |
|---|---|
| 05:30 | Toplayıcılar gelir, NFC kartla giriş, günün sıra planı tabletten okunur |
| 05:45-11:00 | Hasat: paketli kalite doğrudan punnet'e, 2. sınıf kasaya. Her kasa tartılır, kayda toplayıcı ve sıra yazılır |
| Her 45-60 dk | Dolu kasalar gölgeden ön soğutma tüneline (hedef: hasattan 2 saat içinde iç sıcaklık < 5 °C) |
| 11:00-15:00 | Paketleme: top-seal, QR lot etiketi, koli. 2. sınıf şok dondurucuya |
| 15:00-17:00 | Sevkiyat hazırlığı, soğuk zincir logger'larının koliye konması, distribütör teslimi |
| 17:00 | Otomatik gün sonu raporu sana ulaşır: kg, kanal, fire, işçi verimi, yarının hasat tahmini, uyarılar |

### 3.4 Ankara'dan uzaktan yönetim modeli

| Rol | Kim | Sorumluluk |
|---|---|---|
| **Kurucu (sen)** | Ankara + ziyaret | Strateji, satış ve kurumsal ilişkiler, teknoloji geliştirme, finans, haftalık KPI değerlendirmesi |
| **Saha şefi / tarım teknisyeni** | Daimi, Karacabey/Muratlı'dan | Günlük operasyon, işçi yönetimi, ilaçlama ve gübre uygulaması, ilk müdahale |
| **Sezonluk pakethane sorumlusu** | Haziran-Ekim | Paketleme kalitesi, soğuk zincir, sevkiyat |
| **Ziraat danışmanı** | Aylık ziyaret, sözleşmeli | Budama, hastalık ve beslenme kararlarına ikinci göz (v2 sabit giderlerine dahil) |

**Uzaktan yönetim araçları:** canlı panel, kritik alarmların telefona bildirimi (don, kuru toprak, soğuk oda sıcaklığı, hareket algılama), kameralar, haftalık görüntülü toplantı, LLM ile otomatik günlük rapor.
**Kural:** Kritik kararlar (ilaçlama, hasat başlangıcı, fiyat) sahadan fotoğraf ve sensör verisiyle **senin onayınla** alınır. Otomasyon, sulama ve alarm dışında kendi kendine karar vermez.

---

## 4. Hibrit Kanal Modeli: Taze Çoğunluk, Dondurulmuş ve Kuru Emniyet Supabı

### 4.1 Kanal ekonomisi (taze kg başına katkı payı)

| Kanal | Taze kg başına katkı (USD) | Not |
|---|---:|---|
| Kurumsal markalı paket | 6,38 | Ön sözleşmeli, fiyat sabit |
| Taze paketli (100/200/500 g) | 3,26 | Ana kanal; raf ömrü 7-10 gün |
| Liyofilize — kendi makine | 3,13 | Makine + izin: ~$4.200/yıl sabit |
| Liyofilize — fason | 1,83 | Yatırımsız, 12-24 ay raf ömrü |
| IQF dondurulmuş | 1,71 | Kış satışı, emniyet supabı |
| Hal / dökme taze | 1,50 | Bolluk yılında −%30 |
| İşleme tesisine 2. sınıf | 0,66 | Dondurucu yoksa tek çıkış |

**Kural basit:** Ürün önce **en yüksek katkılı kanala** gider: kurumsal → taze paketli. Paketlenemeyen veya 2. sınıf ürün **hal yerine dondurucuya** gider. Dondurulan ürün kışın IQF olarak satılır, bir kısmı fasonda liyofilize edilir.

### 4.2 Hacim akışı (baz)

| Yıl | Rekolte | Taze paketli | Kurumsal | Hal | IQF | Liyofilize girdi → kuru | Taze payı |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2027 | 0,5 t | 0,0 t | 0,0 t | 0,4 t | 0,0 t | 0,0 t → 0 kg | %80 |
| 2028 | 5,5 t | 2,2 t | 0,0 t | 2,2 t | 0,0 t | 0,0 t → 0 kg | %80 |
| 2029 | 14,5 t | 7,2 t | 0,5 t | 1,9 t | 3,9 t | 1,0 t → 114 kg | %67 |
| 2030 | 20,0 t | 10,9 t | 1,5 t | 1,8 t | 4,1 t | 1,7 t → 205 kg | %71 |
| 2031 | 20,0 t | 10,8 t | 2,5 t | 1,4 t | 3,2 t | 2,1 t → 252 kg | %73 |
| 2032 | 20,0 t | 10,4 t | 3,0 t | 1,3 t | 2,6 t | 2,6 t → 312 kg | %74 |
| 2033 | 20,0 t | 10,4 t | 3,0 t | 1,3 t | 2,6 t | 2,6 t → 312 kg | %74 |
| 2034 | 20,0 t | 10,4 t | 3,0 t | 1,3 t | 2,6 t | 2,6 t → 312 kg | %74 |
| 2035 | 18,0 t | 9,1 t | 3,0 t | 1,1 t | 2,4 t | 2,4 t → 279 kg | %74 |
| 2036 | 16,0 t | 7,8 t | 3,0 t | 1,0 t | 2,1 t | 2,1 t → 246 kg | %74 |

Gelirin ~%73'ü taze (paketli + kurumsal + hal), ~%16'sı dondurulmuş ve liyofilize, kalanı hizmet, lab ve danışmanlık (2032).

### 4.3 Neden kendi liyofilize makinesi değil, fason?

Kendi makine fasona göre taze kg başına $1,30 tasarruf sağlıyor. Ama makine amortismanı ve gıda üretim izni/HACCP yılda ~$4.200 sabit maliyet getiriyor. Başabaş için yılda **~3,2 t taze girdi** gerekiyor; 10 da'da liyofilizeye giden miktar 2,1-2,6 t. Kendi makine ancak **20 da'da** (girdi ~5 t) mantıklı. O güne kadar fason ile ürün, pazar ve fiyat test edilir.

### 4.4 Faz 3 ve yenileme yatırımları

| Yıl | Kalem | USD | Ömür |
|---|---|---:|---:|
| 2028 sonu | İkinci 40' reefer, -20 °C dondurulmuş stok deposu | 8.500 | 10 yıl |
| 2028 sonu | Şok dondurucu (-35 °C, 300 kg/parti) | 14.000 | 8 yıl |
| 2032 sonu | Elektronik yenileme (sensör, kamera, edge) | 8.000 | 5 yıl |
| 2034 sonu | Gölge filesi + malç örtü yenileme | 4.900 | 7 yıl |

Faz 3 (şok dondurucu + dondurulmuş depo, $22.500) 2. sınıf ürünün değerini $0,66'dan ~$1,71-1,83/kg'a çıkarıyor. Asıl değeri ise **bolluk yılında fazla ürünü hale düşük fiyattan vermek zorunda kalmamak.** Risk simülasyonundaki önlemlerin önemli bir kısmı bu yatırıma dayanıyor.

---

## 5. Mevsim Riskleri: Gözünde mi Büyütüyorsun?

### 5.1 Risk olayları ve önlemlerin etkisi

| Olay | Yıllık olasılık | Önlemsiz verim kaybı | Önlemli verim kaybı |
|---|---:|---:|---:|
| Sıcak dalgası / güneş yanığı | %30 | %15 | %5 |
| Hasat döneminde yoğun yağış (meyve çürümesi) | %15 | %10 | %6 |
| SWD (Drosophila suzukii) salgını | %35 | %20 | %5 |
| Geç bahar donu | %5 | %20 | %10 (+ TARSİM %60) |
| Dolu | %5 | %40 | %40 (+ TARSİM %60) |
| İşçi bulamama | %20 | işçilik +%35, ürünün %6'sı toplanamaz | işçilik +%15, %1 |
| Pazar bolluğu (fiyat çöküşü) | %25 | hal −%30, paketli −%10 | hal −%30, paketli −%5, fazla ürün dondurucuya |
| Normal dalgalanma (her yıl) | – | verim σ %8, fiyat σ %7 | aynı |

**Önlemler ve yaklaşık maliyetleri:**

| Önlem | Neye karşı | Maliyet |
|---|---|---|
| %35 gölge filesi + sıcak dalgasında serinletme sulaması | Güneş yanığı | $4.100 CAPEX |
| 3 çeşitli portföy | Sıcak, yağış, fiyat ve işçi yoğunlaşması | Ek maliyet yok |
| SWD tuzak ağı + AI sayım + 2 günde bir hasat + düşük meyve temizliği | SWD | Kameralar $450 + ilaç bütçesi |
| Meteoroloji istasyonu + hastalık modeli | Yağış sonrası küf/çürüme | v2'de dahil |
| Orman rüzgâr kıranı + don alarmı | Geç don | Doğal |
| **TARSİM** (dolu, don, fırtına) | Dolu, don | ~$600/yıl |
| NFC tartılı parça başı ödeme + köyden sabit ekip + sezon başı avans | İşçi bulamama | v2'de dahil |
| Şok dondurucu + dondurulmuş depo | Fiyat çöküşü, satılamayan ürün | $22.500 (Faz 3) |
| Kurumsal ön sözleşmeler | Fiyat çöküşü | Satış emeği |
| Ön soğutma + soğuk zincir | Raf ömrü, fire | v2'de dahil |

### 5.2 Risk simülasyonu: 5.000 farklı 10 yıl

Her senaryoda yukarıdaki olaylar her yıl kendi olasılığıyla rastgele gerçekleşiyor; üstüne verimde ±%8 ve fiyatta ±%7 doğal dalgalanma ekleniyor. "Önlemsiz" bahçe: tek çeşit, gölge filesi yok, sigorta yok, dondurucu yok (2. sınıf işleme tesisine, fazla ürün hale), kurumsal sözleşme yok.

| Gösterge (5.000 simülasyon) | Önlemsiz | Önlemli (bu plan) |
|---|---:|---:|
| Sermayenin 10 yılda geri dönmeme olasılığı (reel) | %55,9 | %0,0 |
| %12 hedef getirinin altında kalma olasılığı (NPV@12 < 0) | %100,0 | %96,4 |
| Proje IRR — kötü / ortanca / iyi (P10/P50/P90) | −%4,9 / −%0,4 / %3,5 | %7,6 / %9,4 / %11,2 |
| Olgun yıllarda (2031-36) bir yılın zararla kapanma olasılığı | %17,1 | %0,1 |
| Olgun yıl vergi öncesi kâr — kötü (P10) | −$3.561 | $16.368 |
| Olgun yıl vergi öncesi kâr — ortanca (P50) | $9.817 | $27.966 |
| Olgun yıl vergi öncesi kâr — iyi (P90) | $23.568 | $40.889 |
| 2030-36'da ortalama zarar yılı sayısı (7 yılda) | 1,7 | 0,1 |
| 7 yılda 2+ zarar yılı yaşama olasılığı | %56,6 | %0,0 |

### 5.3 Yorum

1. **Mevsim riskleri gerçek ama yönetilebilir.** Önlemsiz bir bahçe 7 olgun yılın ortalama 1,7'sini zararla kapatıyor ve sermayesini 10 yılda geri alamama olasılığı %56. Bu plandaki önlemlerle zarar yılı neredeyse ortadan kalkıyor (%0,1) ve sermayenin geri dönmeme olasılığı simülasyonda sıfır. Korkun haklı, ama önlemleri zaten planda var.
2. **Simülasyonun kötü senaryosu (P10) bile kârlı:** olgun bir yılda vergi öncesi en az ~$16.000.
3. **Simülasyonun yakalayamadığı asıl riskler** aşağıda.

**Pazar riski:** paketli fiyatın veya satış kapasitesinin **kalıcı olarak** düşük çıkması. Deterministik pesimistik senaryo (Bölüm 6.4) bunu gösteriyor: bütün olumsuzluklar 10 yıl boyunca birlikte olursa proje zararda. Önlem: Kapı 1 ve Kapı 2 (ön anlaşma ve 2028 satış verisi görülmeden büyük yatırım yok).

**Ölçek riski:** 10 da'da proje IRR'si %9,5 ile hedefin altında. Önlem: 2. blok veya kurumsal ortak.

**Uygulama riski:** Ankara'dan yönetimde teknisyenin kalitesi. Önlem: iyi ücret + performans primi, ilk sezon sık ziyaret, danışman ziraat mühendisi.

---

## 6. 10 Yıllık Finansal Projeksiyon (2027-2036)

### 6.1 Gelir tablosu — Kuruluş ve büyüme (2027-2031)

| USD | 2027 | 2028 | 2029 | 2030 | 2031 |
|---|---:|---:|---:|---:|---:|
| Rekolte (t) | 0,5 | 5,5 | 14,5 | 20,0 | 20,0 |
| Taze paketli | 0 | 12.436 | 40.783 | 61.471 | 61.047 |
| Kurumsal paket | 0 | 0 | 4.500 | 13.500 | 22.500 |
| Hal / dökme taze | 1.000 | 5.500 | 4.856 | 4.531 | 3.375 |
| İşleme (2. sınıf, dondurucu öncesi) | 130 | 1.430 | 0 | 0 | 0 |
| IQF dondurulmuş | 0 | 0 | 10.847 | 11.392 | 8.988 |
| Liyofilize (kuru) | 0 | 0 | 4.558 | 8.206 | 10.071 |
| Hizmet + lab + danışmanlık | 0 | 0 | 1.500 | 5.000 | 11.000 |
| **TOPLAM GELİR** | **1.130** | **19.366** | **67.044** | **104.101** | **116.981** |
| Hasat | −275 | −3.355 | −9.132 | −12.856 | −12.995 |
| Ambalaj + pakethane | 0 | −1.574 | −5.520 | −8.854 | −9.516 |
| Dağıtım + komisyon | −189 | −3.240 | −8.533 | −13.255 | −14.173 |
| Dondurma + IQF lojistik | 0 | 0 | −2.237 | −2.459 | −2.054 |
| Liyofilize (fason/kendi) + ambalaj | 0 | 0 | −2.108 | −3.795 | −4.658 |
| Hizmet maliyeti | 0 | 0 | −525 | −1.550 | −2.700 |
| Sabit giderler | −13.600 | −25.950 | −30.800 | −31.450 | −31.450 |
| **FAVÖK** | **−12.934** | **−14.754** | **8.189** | **29.881** | **39.434** |
| Amortisman | −5.020 | −12.486 | −15.086 | −14.753 | −14.403 |
| Faiz | −3.538 | −7.261 | −7.917 | −5.992 | −3.605 |
| **VERGİ ÖNCESİ KÂR** | **−21.492** | **−34.501** | **−14.814** | **9.137** | **21.427** |
| Kurumlar vergisi (%25) | 0 | 0 | 0 | 0 | 0 |
| **NET KÂR** | **−21.492** | **−34.501** | **−14.814** | **9.137** | **21.427** |
| Net marj | −%1902 | −%178 | −%22 | %9 | %18 |

### 6.2 Gelir tablosu — Olgunluk (2032-2036)

| USD | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|
| Rekolte (t) | 20,0 | 20,0 | 20,0 | 18,0 | 16,0 |
| Taze paketli | 58.786 | 58.786 | 58.786 | 51.551 | 44.316 |
| Kurumsal paket | 27.000 | 27.000 | 27.000 | 27.000 | 27.000 |
| Hal / dökme taze | 3.250 | 3.250 | 3.250 | 2.850 | 2.450 |
| İşleme (2. sınıf, dondurucu öncesi) | 0 | 0 | 0 | 0 | 0 |
| IQF dondurulmuş | 7.420 | 7.420 | 7.420 | 6.636 | 5.852 |
| Liyofilize (kuru) | 12.471 | 12.471 | 12.471 | 11.153 | 9.835 |
| Hizmet + lab + danışmanlık | 13.500 | 16.000 | 16.000 | 16.000 | 16.000 |
| **TOPLAM GELİR** | **122.427** | **124.927** | **124.927** | **115.190** | **105.453** |
| Hasat | −13.010 | −13.010 | −13.010 | −11.718 | −10.426 |
| Ambalaj + pakethane | −9.588 | −9.588 | −9.588 | −8.672 | −7.756 |
| Dağıtım + komisyon | −14.359 | −14.359 | −14.359 | −13.035 | −11.711 |
| Dondurma + IQF lojistik | −1.828 | −1.828 | −1.828 | −1.635 | −1.442 |
| Liyofilize (fason/kendi) + ambalaj | −5.768 | −5.768 | −5.768 | −5.158 | −4.549 |
| Hizmet maliyeti | −3.225 | −3.750 | −3.750 | −3.750 | −3.750 |
| Sabit giderler | −31.450 | −31.450 | −31.450 | −31.450 | −31.450 |
| **FAVÖK** | **43.198** | **45.173** | **45.173** | **39.771** | **34.369** |
| Amortisman | −11.107 | −11.427 | −11.427 | −11.584 | −10.822 |
| Faiz | −1.449 | −303 | 0 | 0 | 0 |
| **VERGİ ÖNCESİ KÂR** | **30.642** | **33.443** | **33.746** | **28.187** | **23.547** |
| Kurumlar vergisi (%25) | 0 | −5.960 | −8.437 | −7.047 | −5.887 |
| **NET KÂR** | **30.642** | **27.482** | **25.310** | **21.140** | **17.660** |
| Net marj | %25 | %22 | %20 | %18 | %17 |

**Notlar:**
- 2027-2029 zararları (toplam $70.807) 5 yıl boyunca mahsup ediliyor. Kurumlar vergisi ilk kez **2033'te** ödeniyor. 2027 zararının mahsup süresi 2032'de doluyor.
- Sabit giderler v2 bazı + kurucu ulaşımı ($3.500) + arı kovanları ($300) + dondurulmuş depo elektriği ($900, 2029+). Toplam olgun yılda $31.450.
- 2035-36'daki verim düşüşü, bitki yaşlanmasının temkinli bir tahmini. İyi gençleştirme budamasıyla verim 2037+'ya kadar korunabilir.

### 6.3 Nakit akışı ve finansman

| USD | Y0 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FAVÖK | 0 | −12.934 | −14.754 | 8.189 | 29.881 | 39.434 | 43.198 | 45.173 | 45.173 | 39.771 | 34.369 |
| Vergi | 0 | 0 | 0 | 0 | 0 | 0 | 0 | −5.960 | −8.437 | −7.047 | −5.887 |
| Yatırım + yenileme | −45.130 | −54.380 | −22.500 | 0 | 0 | 0 | −8.000 | 0 | −4.900 | 0 | 0 |
| Kalıntı değer (net defter değerinin %50'si) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8.396 |
| Kredi kullanımı | 22.565 | 27.190 | 11.250 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Faiz | 0 | −3.538 | −7.261 | −7.917 | −5.992 | −3.605 | −1.449 | −303 | 0 | 0 | 0 |
| Anapara | 0 | 0 | 0 | −4.578 | −9.396 | −10.245 | −5.896 | −1.639 | 0 | 0 | 0 |
| **Özsermaye nakit akışı** | −22.565 | −43.662 | −33.265 | −4.306 | 14.494 | 25.585 | 27.854 | 37.271 | 31.837 | 32.725 | 36.879 |
| **Kümülatif** | −22.565 | −66.227 | −99.491 | −103.797 | −89.304 | −63.719 | −35.865 | 1.406 | 33.243 | 65.967 | 102.846 |

Kredi kurgusu: Faz 1, 2 ve 3'ün %50'si Ziraat Hazine faiz destekli TL kredisiyle karşılanıyor (%18,5, 2+3 yıl). **Özsermaye ihtiyacı 2029'da tepe yapıyor: $103.797.** Kümülatif özsermaye nakdi **2033'te** pozitife dönüyor. Ayrıca temmuz-ekim arasında, alıcı vadeleri nedeniyle $10-15k sezonluk işletme sermayesi gerekir.

### 6.4 Senaryolar

| Gösterge | Baz | Pesimistik | İyimser |
|---|---:|---:|---:|
| 10 yıl toplam gelir | $901.543 | $594.061 | $1.095.352 |
| 10 yıl toplam vergi öncesi kâr | $109.322 | −$131.534 | $234.907 |
| 10 yıl toplam net kâr | $81.991 | −$131.534 | $176.180 |
| Tam verim yılı (2032) net kâr | $30.642 | −$1.637 | $35.538 |
| Proje NPV (%12) | −$15.631 | −$124.758 | $32.911 |
| Proje IRR | %9,5 | −%14,0 | %16,8 |
| Özsermaye IRR (kredili) | %12,0 | −%17,0 | %21,6 |
| Geri dönüş (kaldıraçsız) | 6,9 yıl | geri dönmez | 5,7 yıl |
| Azami özsermaye ihtiyacı | $103.797 | $156.480 | $96.020 |

- **Baz:** Bu raporun varsayımları. Mevsim olayları "ortalama bir yıl" düzeyinde.
- **Pesimistik (stres testi):** Verim −%25, tüm fiyatlar −%20, hasat işçiliği +%30, **10 yıl boyunca her yıl birlikte.** Mevsim olaylarının rastgele değil kalıcı bir pazar ve verim sorunu olduğu durumu gösteriyor. Gerçekleşme olasılığı düşük, ama Kapı 1-2'nin neden şart olduğunu açıklıyor.
- **İyimser:** Verim +%20 (tam verimde 24 t), fiyatlar +%5.

### 6.5 Ölçek

10 da'nın getirisi ölçek nedeniyle sınırlı. 20 da planı ve tabloları bir sonraki bölümde.

---

## 7. 20 Dönüm Planı

### 7.1 Neden 20 da?

v2'den bu yana tekrar eden bulgu şu: pakethane, soğuk zincir, şok dondurucu, AgTech ağı, teknisyen ve marka giderleri 10 da'yı da 20 da'yı da neredeyse aynı maliyetle taşıyor. 10 da'da kg başı sabit gider ~$1,57; 20 da'da ~$1,25'e iniyor. Ayrıca liyofilize girdisi ~6 t'ya çıktığı için **kendi makine ekonomik hâle geliyor** (başabaş 3,2 t, Bölüm 4.3).

### 7.2 İki seçenek

| | **A. Tek seferde** (2 × 10 da, Nisan 2027) | **B. Kademeli** (10 da 2027 + 10 da Nisan 2029) |
|---|---|---|
| İkinci blok tarla yatırımı | Q4-2026 / Q1-2027 | Q4-2028 / Q1-2029 (Kapı 2 sonrası) |
| İlk 20 da tam verim yılı | 2030 | 2032 |
| Pazar bilgisi | Pazarı görmeden iki kat ürün varsayımı | 2028 satış verisi görüldükten sonra karar |
| Proje IRR / özsermaye IRR | %16,7 / %21,4 | %15,0 / %19,1 |
| Azami özsermaye | $133.058 | $129.462 |
| Ne zaman seçilmeli | Mart 2027'den önce ≥ 5 t/yıl kurumsal ortak veya ön sözleşme varsa | **Varsayılan** |

İki seçenekte de **toplam yatırım aynı** ($193.459, 10 yıl, yenilemeler dahil). Fark zamanlamada: A, iki yıl önce tam verime ulaştığı için daha yüksek getiri sağlıyor. B ise ikinci $30k'yı pazar kanıtlandıktan sonra harcıyor. Bölüm 5'te gösterildiği gibi asıl risk mevsim değil pazar olduğu için **B öneriliyor**.

### 7.3 Ek yatırım (10 da → 20 da)

| Kalem (2. blok, 10 da) | USD | TL |
|---|---:|---:|
| Toprak analizi + dip kazan + lazer tesviye + 40 t organik gübre + sedde | 3.850 | 180.950 |
| Sedde üstü agrotekstil malç (3.400 m²) | 1.100 | 51.700 |
| Doku kültürü M1 sertifikalı fidan 3.000 ad + %5 yedek + dikim | 10.050 | 472.350 |
| Telli terbiye: ~630 galvaniz direk, 3 kat tel, T-kol, ankraj, montaj | 8.500 | 399.500 |
| Sulama hidroliği: DSİ hidrant bağlantısı, ana hat, disk+kum filtre, 6.600 m çift lateral | 2.450 | 115.150 |
| 8 adet ek DIY toprak düğümü (LoRaWAN ağı genişletme) | 2.240 | 105.280 |
| Beklenmeyen giderler (%8) | 2.255 | 105.994 |
| **Tarla kurulumu toplamı** (dikimden önceki kış) | **30.445** | **1.430.924** |
| Gölge filesi (ilk hasattan önce, %8 dahil) | 4.104 | 192.888 |
| Kendi liyofilize makinesi + kurulum (20 da'da ekonomik) | 24.000 | 1.128.000 |
| **20 da için ek yatırım toplamı** | **58.549** | **2.751.812** |

İkinci blok mevcut pakethane, reefer, GES, dondurucu, gateway ve edge sunucuyu paylaşıyor. Kapasite kontrolü:

| Varlık | 20 da tepe yükü | Kapasite | Durum |
|---|---|---|---|
| Ön soğutma tüneli | ~850-900 kg/gün | ~1 t/parti, günde 2 parti | Yeterli |
| 40' reefer (0/+2 °C) | 2-3 günlük taze stok (~2,5 t) | ~8-10 t | Yeterli |
| Top-seal makinesi | Tepe günde ~1.500 paket | 400-600 paket/saat | Yeterli (3-4 saat) |
| Şok dondurucu | ~300-400 kg/gün | 300 kg/parti | Tepe günlerde 2 parti |
| İkinci reefer (-20 °C) | Yıllık ~12 t dondurulmuş | ~10 t anlık | Kış satışıyla döner; gerekirse fason depo |
| GES 10 kWp | Elektrik ihtiyacı ~1,6 kat | – | Şebeke takviyeli; Faz 3'te +5 kWp değerlendirilebilir |

### 7.4 Organizasyon (20 da)

| Rol | 10 da | 20 da |
|---|---|---|
| Saha şefi / tarım teknisyeni (daimi) | 1 | 1 |
| Daimi tarım işçisi | – | **1** (ikinci blok dikiminden itibaren) |
| Sezonluk pakethane sorumlusu | 1 | 1 (+1 yardımcı tepe dönemde) |
| Tepe hasat toplayıcısı | 7-8 | **14-15** |
| Budama ekibi (Ocak-Şubat, yevmiyeli) | 3-4 kişi × 2 hafta | 3-4 kişi × 4 hafta |
| Kurucu ziyareti | ~25-30/yıl | ~30-35/yıl (sezonda daha uzun kalış) |

14-15 toplayıcıyı her sezon bulmak 20 da'nın en zorlu operasyonel işi. Muratlı ve çevre köylerden sabit bir ekip (sezon başı avans, kg başı prim, servis aracı) ve 3 çeşit portföyünün yaydığı hasat bu yüzden kritik.

### 7.5 20 da kademeli plan — hacim akışı

| Yıl | Rekolte | Taze paketli | Kurumsal | Hal | IQF | Liyofilize girdi → kuru | Taze payı |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2027 | 0,5 t | 0,0 t | 0,0 t | 0,4 t | 0,0 t | 0,0 t → 0 kg | %80 |
| 2028 | 5,5 t | 2,2 t | 0,0 t | 2,2 t | 0,0 t | 0,0 t → 0 kg | %80 |
| 2029 | 15,0 t | 7,5 t | 0,5 t | 2,0 t | 4,0 t | 1,0 t → 118 kg | %67 |
| 2030 | 25,5 t | 12,3 t | 2,2 t | 2,9 t | 5,6 t | 2,4 t → 284 kg | %68 |
| 2031 | 34,5 t | 17,2 t | 3,8 t | 3,3 t | 6,1 t | 4,1 t → 482 kg | %70 |
| 2032 | 40,0 t | 19,8 t | 4,5 t | 3,9 t | 5,9 t | 5,9 t → 697 kg | %70 |
| 2033 | 40,0 t | 19,8 t | 4,5 t | 3,9 t | 5,9 t | 5,9 t → 697 kg | %70 |
| 2034 | 40,0 t | 19,8 t | 4,5 t | 3,9 t | 5,9 t | 5,9 t → 697 kg | %70 |
| 2035 | 38,0 t | 18,6 t | 4,5 t | 3,6 t | 5,6 t | 5,6 t → 660 kg | %70 |
| 2036 | 36,0 t | 17,5 t | 4,5 t | 3,4 t | 5,3 t | 5,3 t → 624 kg | %71 |

Sezon başına ~96.000 paket, ~4,5 t kurumsal ürün, ~700 kg liyofilize. Kendi liyofilize makinesi 2031 sonunda alınıyor ve 2032'den itibaren fasonun yerini alıyor.

### 7.6 20 da kademeli plan — gelir tablosu (2027-2031)

| USD | 2027 | 2028 | 2029 | 2030 | 2031 |
|---|---:|---:|---:|---:|---:|
| Rekolte (t) | 0,5 | 5,5 | 15,0 | 25,5 | 34,5 |
| Taze paketli | 0 | 12.436 | 42.252 | 69.250 | 97.065 |
| Kurumsal paket | 0 | 0 | 4.500 | 20.250 | 33.750 |
| Hal / dökme taze | 1.000 | 5.500 | 5.031 | 7.373 | 8.348 |
| İşleme (2. sınıf, dondurucu öncesi) | 130 | 1.430 | 0 | 0 | 0 |
| IQF dondurulmuş | 0 | 0 | 11.228 | 15.777 | 17.202 |
| Liyofilize (kuru) | 0 | 0 | 4.718 | 11.364 | 19.273 |
| Hizmet + lab + danışmanlık | 0 | 0 | 1.500 | 5.000 | 11.000 |
| **TOPLAM GELİR** | **1.130** | **19.366** | **69.229** | **129.014** | **186.637** |
| Hasat | −275 | −3.355 | −9.446 | −16.200 | −22.113 |
| Ambalaj + pakethane | 0 | −1.574 | −5.706 | −10.376 | −14.970 |
| Dağıtım + komisyon | −189 | −3.240 | −8.818 | −16.013 | −22.802 |
| Dondurma + IQF lojistik | 0 | 0 | −2.316 | −3.405 | −3.932 |
| Liyofilize (fason/kendi) + ambalaj | 0 | 0 | −2.182 | −5.256 | −8.914 |
| Hizmet maliyeti | 0 | 0 | −525 | −1.550 | −2.700 |
| Sabit giderler | −13.600 | −25.950 | −38.050 | −46.850 | −48.400 |
| **FAVÖK** | **−12.934** | **−14.754** | **2.186** | **29.365** | **62.807** |
| Amortisman | −5.020 | −12.486 | −18.131 | −18.384 | −18.034 |
| Faiz | −3.538 | −7.261 | −10.304 | −8.336 | −5.591 |
| **VERGİ ÖNCESİ KÂR** | **−21.492** | **−34.501** | **−26.249** | **2.646** | **39.182** |
| Kurumlar vergisi (%25) | 0 | 0 | 0 | 0 | 0 |
| **NET KÂR** | **−21.492** | **−34.501** | **−26.249** | **2.646** | **39.182** |
| Net marj | −%1902 | −%178 | −%38 | %2 | %21 |

### 7.7 20 da kademeli plan — gelir tablosu (2032-2036)

| USD | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|
| Rekolte (t) | 40,0 | 40,0 | 40,0 | 38,0 | 36,0 |
| Taze paketli | 111.920 | 111.920 | 111.920 | 105.408 | 98.896 |
| Kurumsal paket | 40.500 | 40.500 | 40.500 | 40.500 | 40.500 |
| Hal / dökme taze | 9.625 | 9.625 | 9.625 | 9.065 | 8.505 |
| İşleme (2. sınıf, dondurucu öncesi) | 0 | 0 | 0 | 0 | 0 |
| IQF dondurulmuş | 16.590 | 16.590 | 16.590 | 15.716 | 14.843 |
| Liyofilize (kuru) | 27.882 | 27.882 | 27.882 | 26.414 | 24.946 |
| Hizmet + lab + danışmanlık | 13.500 | 16.000 | 16.000 | 16.000 | 16.000 |
| **TOPLAM GELİR** | **220.017** | **222.517** | **222.517** | **213.103** | **203.690** |
| Hasat | −25.645 | −25.645 | −25.645 | −24.372 | −23.099 |
| Ambalaj + pakethane | −17.387 | −17.387 | −17.387 | −16.562 | −15.738 |
| Dağıtım + komisyon | −26.503 | −26.503 | −26.503 | −25.275 | −24.047 |
| Dondurma + IQF lojistik | −4.088 | −4.088 | −4.088 | −3.873 | −3.658 |
| Liyofilize (fason/kendi) + ambalaj | −5.193 | −5.193 | −5.193 | −4.920 | −4.646 |
| Hizmet maliyeti | −3.225 | −3.750 | −3.750 | −3.750 | −3.750 |
| Sabit giderler | −49.925 | −49.925 | −49.925 | −49.925 | −49.925 |
| **FAVÖK** | **88.051** | **90.026** | **90.026** | **84.426** | **78.826** |
| Amortisman | −17.738 | −18.058 | −18.058 | −18.215 | −17.453 |
| Faiz | −4.529 | −2.438 | −1.406 | −763 | −323 |
| **VERGİ ÖNCESİ KÂR** | **65.784** | **69.529** | **70.561** | **65.447** | **61.050** |
| Kurumlar vergisi (%25) | −6.342 | −17.382 | −17.640 | −16.362 | −15.262 |
| **NET KÂR** | **59.441** | **52.147** | **52.921** | **49.086** | **45.787** |
| Net marj | %27 | %23 | %24 | %23 | %22 |

### 7.8 20 da kademeli plan — nakit akışı

| USD | Y0 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 | 2033 | 2034 | 2035 | 2036 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FAVÖK | 0 | −12.934 | −14.754 | 2.186 | 29.365 | 62.807 | 88.051 | 90.026 | 90.026 | 84.426 | 78.826 |
| Vergi | 0 | 0 | 0 | 0 | 0 | 0 | −6.342 | −17.382 | −17.640 | −16.362 | −15.262 |
| Yatırım + yenileme | −45.130 | −54.380 | −52.945 | −4.104 | 0 | −24.000 | −8.000 | 0 | −4.900 | 0 | 0 |
| Kalıntı değer (net defter değerinin %50'si) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 15.941 |
| Kredi kullanımı | 22.565 | 27.190 | 26.473 | 2.052 | 0 | 12.000 | 0 | 0 | 0 | 0 | 0 |
| Faiz | 0 | −3.538 | −7.261 | −10.304 | −8.336 | −5.591 | −4.529 | −2.438 | −1.406 | −763 | −323 |
| Anapara | 0 | 0 | 0 | −4.578 | −9.396 | −13.333 | −8.929 | −4.210 | −2.734 | −2.063 | −1.748 |
| **Özsermaye nakit akışı** | −22.565 | −43.662 | −48.487 | −14.748 | 11.633 | 31.882 | 60.250 | 65.995 | 63.346 | 65.238 | 77.433 |
| **Kümülatif** | −22.565 | −66.227 | −114.714 | −129.462 | −117.828 | −85.946 | −25.696 | 40.299 | 103.645 | 168.882 | 246.315 |

Kredi kurgusu: Faz 1-3, ikinci blok ve liyofilize makinesinin %50'si Ziraat Hazine faiz destekli TL kredisi; yenileme yatırımları özsermayeden.

### 7.9 20 da risk simülasyonu (önlemli plan)

| Önlemli plan, 5.000 simülasyon | 10 da | 20 da — tek seferde (2027) | 20 da — kademeli (2027 + 2029) |
|---|---:|---:|---:|
| Sermayenin geri dönmeme olasılığı | %0,0 | %0,0 | %0,0 |
| %12 hedefin altında kalma olasılığı | %96,4 | %0,5 | %3,6 |
| Proje IRR P10 / P50 / P90 | %7,6 / %9,4 / %11,2 | %14,4 / %16,5 / %18,6 | %12,9 / %14,9 / %16,8 |
| Olgun yılın zararla kapanma olasılığı | %0,1 | %0,0 | %0,0 |
| Olgun yıl vergi öncesi kâr P10 / P50 | $16.368 / $27.966 | $39.373 / $61.153 | $36.111 / $61.633 |

20 da'da hedef getirinin altında kalma olasılığı %96'dan **%3,6'ya (kademeli)** ve **%0,5'e (tek seferde)** düşüyor. Simülasyonun kapsamadığı pazar riski (Bölüm 5.3) 20 da'da iki kat büyük. Kademeli yolun öncelikli olmasının nedeni bu.

### 7.10 20 da takviminde farklar

- **2027:** İkinci blok için yalnız gözlem: toprak analizi, drenaj, örtü bitkisi.
- **Eylül 2028 (Kapı 2):** 2028 sezon verisi olumluysa fidan siparişi (doku kültürü için 5-6 ay tedarik süresi).
- **Ekim 2028 – Mart 2029:** İkinci blokta toprak hazırlığı, sedde, telli terbiye, sulama, sensör ağının genişletilmesi.
- **Nisan 2029:** İkinci blok dikimi. Aynı yıl birinci blokta ilk büyük hasat (14,5 t): 2029 en yoğun yıl.
- **2031 sonu:** Kendi liyofilize makinesi ve gıda üretim izni.
- **Olgun yıl takvimi** (Bölüm 3.2) aynı; budama ve hasat iş günleri yaklaşık iki katına çıkıyor.

---

## 8. Finansman, Hukuki Yapı ve Ortaklık (v2'den değişenler)

- **Toplam fon ihtiyacı:** CAPEX $122.010 (3 faz) + ilk yıl işletme açıkları + $10-15k sezon sermayesi. Kredi payı $61.005, **özsermaye tepe ihtiyacı $103.797.**
- **Hibe:** KKYDP %50 hibesi (soğuk depo + paketleme + şok dondurucu) gelirse özsermaye tepe ihtiyacı yaklaşık $70-75k'ya iner. Başvuru takvimi Faz 2/3 zamanlamasını belirlemeli.
- **Şirket:** Ltd. Şti. önerisi geçerli: zarar mahsubu, ortak ve kurum alımı, fason liyofilizeyle kendi markanla satış.
- **20 da kademeli plan:** Toplam yatırım $193.459 (10 yıl), özsermaye tepe ihtiyacı **$129.462** (2029-2030). Kurumsal ortak ikinci bloğu finanse ederse bu ihtiyaç ~$110-115k'ya iner.
- **Kurumsal ortak:** İkinci 10 da'nın en iyi finansman yolu bu (v2 Bölüm 9.2). Kurum CAPEX'i finanse eder, ürünün yarısını sabit fiyatla kendi markasıyla alır. Bu model aynı zamanda pazar riskine karşı en güçlü önlem.

---

## 9. 10 Yıllık Yol Haritası ve Karar Kapıları

| Yıl | Odak | Karar kapısı |
|---|---|---|
| 2026 Q4 | Şirket, kredi, izinler, toprak hazırlığı, fidan siparişi | Kredi onayı |
| 2027 | Dikim (3 çeşit), AgTech v1, marka; ilk sonbahar ürünüyle pazar testi | **Kapı 1:** ≥ 2 alıcı ön anlaşması → Faz 2 |
| 2028 | Faz 2 (soğuk zincir + pakethane), ilk floricane hasadı (5,5 t) | **Kapı 2 (Eylül):** paketli fiyat ≥ $5/kg ve satış oranı ≥ %80 → Faz 3 + 2. blok fidan siparişi |
| 2029 | **2. blok dikimi (Nisan)**, Faz 3 (dondurucu), ilk IQF ve fason liyofilize, 1 da ahududu pilotu, ilk living lab projesi | Liyofilize B2B fiyatı ≥ $35/kg mı? |
| 2030-2031 | 1. blok tam verim, 2. blok büyüme, kurumsal kanal, danışmanlık | **Kapı 3 (2031 sonu):** liyofilize girdi ≥ 3,2 t → kendi makine |
| 2032 | Elektronik yenileme, FaaS pilot birimi tasarımı | **Kapı 4:** 3 yıllık doğrulanmış veri seti → FaaS |
| 2033-2036 | Olgun işletme, FaaS büyümesi, kısmi yenileme dikimi planı | 2036: bahçe yenileme / gençleştirme kararı |

---

## 10. Sonuç

1. **Böğürtlen doğru ürün.** 3 çeşitli portföy (Loch Ness + Chester + Prime-Ark) ile sezon ~4,5 aya yayılıyor ve risk dağılıyor. Ahududu, living lab'de 1 da pilot olarak deneniyor.
2. **Mevsim riskleri yönetilebilir.** Plandaki önlemlerle olgun bir yılın zararla kapanma olasılığı %0,1. Korkulması gereken mevsim değil, **pazar ve ölçek**. Bunlar karar kapılarıyla yönetiliyor.
3. **Hibrit model** (taze ~%73, dondurulmuş + liyofilize ~%16) satılamayan ürünü bir kayıptan stoklanabilir bir ürüne çeviriyor. Liyofilize fasonla başlıyor; kendi makine 20 da'da.
4. **10 da** (10 yıl): gelir $901.543, net kâr $81.991, IRR %9,5. **20 da kademeli:** gelir $1,49 M, net kâr $218.968, IRR %15,0, özsermaye IRR %19,1. 10 da'yı pilot, 20 da'yı hedef işletme olarak planla. Mart 2027'den önce kurumsal ortak bulunursa iki bloğu birlikte dik (IRR %16,7).
5. **İlk adımlar:** Ltd. kuruluşu ve Ziraat Faz 1 kredi başvurusu 31.12.2026'dan önce; 3 çeşit için fidanlık tedarik teyidi; toprak işlerinin kış yağmurlarından önce bitirilmesi.

---

### Ek A — v3'te değişen varsayımlar

| Varsayım | Değer |
|---|---|
| Çeşit portföyü | Loch Ness %30, Chester %40, Prime-Ark %30 → verim 0,5 / 5,5 / 14,5 / 20 t ... 2035: 18, 2036: 16 t |
| Dondurma | Şok dondurucu 2029 sezonundan itibaren; 2. sınıf ürünün tamamı ve paketlenemeyen tazenin %50'si |
| Liyofilize | Dondurulmuş havuzun %20 → %50'si; 8,5 kg taze = 1 kg kuru; B2B $40/kg; fason $2,00/kg taze girdi; ambalaj $1,50/kg kuru (**fiyatlar tahmin, teklif alınmalı**) |
| IQF | B2B $2,80/kg, ambalaj $0,10, navlun $0,15, komisyon %5 |
| Kurucu ulaşımı | $3.500/yıl (~30 Ankara–Karacabey ziyareti) |
| Kalıntı değer | 2036 sonu net defter değerinin %50'si ($8.396) |
| Vergi | %25 kurumlar vergisi, zarar mahsubu 5 yıl (süre dolan zarar düşer) |
| Risk simülasyonu | 5.000 tekrar; olay olasılıkları Bölüm 5.1; baz verim önlemli planın ortalama yılı kabul edildi |
