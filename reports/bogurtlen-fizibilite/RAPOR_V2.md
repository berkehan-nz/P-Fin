# Muratlı Berry Lab — Akıllı Böğürtlen Üretim, Soğuk Zincir ve AgTech Test Tesisi (Fizibilite v2)

**Kapsam:** 10 da dikensiz böğürtlen + ön soğutma/soğuk depo + 100/200/500 g paketleme + kendi geliştirilen AgTech altyapısı
**Lokasyon:** Bursa / Karacabey / Muratlı Mah. (DSİ Uluabat 2. Kısım AT-TİGH sahası)
**Rapor tarihi:** 2 Ekim 2026 · **Sürüm:** v2 (v1'in yerini alır; v1 = `RAPOR.md`)
**Para birimi:** 2026 sabit fiyatlarıyla USD (reel). TL karşılıkları 1 USD = 47 TL ile verilmiştir.
**Hesap modeli:** [`model_v2.py`](model_v2.py). Bu rapordaki her tablo `python reports/bogurtlen-fizibilite/model_v2.py --tables` çıktısıdır.

> "Muratlı Berry Lab" bir çalışma adıdır; marka tescili için TÜRKPATENT araştırması yapılmalıdır.

---

## 0. Yönetici Özeti

**v1'den bu yana değişenler:**

1. Soğuk zincir ve paketleme artık opsiyon değil, iş modelinin parçası. Ürün 100/200/500 g paketlerle satılıyor. Süpermarket zincirine marka olarak girilmiyor. Satış yerel/bölgesel zincirler, butik market ve manavlar, HoReCa (pastane, otel, kafe), online sezon kutusu ve kurumsal hediye kanallarından yapılıyor.
2. AgTech altyapısı hazır paket alınmak yerine kurucunun kendi mühendisliğiyle kuruluyor. Sensör başına maliyet ~%60 düşüyor, buna karşılık sensör yoğunluğu artıyor. Ölçüm noktası sayısı 3'ten 8'e çıkıyor ve pakete soğuk zincir, tuzak ve meyve sayım kameraları ekleniyor.
3. Tesisin iki rolü var: **tarımsal gelir üreten bir işletme** ve **dünya teknolojilerinin denendiği bir test alanı (living lab)**. Gelir modeli de buna göre 4 katmana ayrıldı (Bölüm 1).

| Gösterge | Baz | Pesimistik | İyimser |
|---|---:|---:|---:|
| Toplam CAPEX (Faz 1 + 2) | $99.510 (4,68 M TL) | $99.510 | $99.510 (−$22.500 hibe) |
| Y5 (2031) gelir | $106.497 | $48.610 | $160.735 |
| Y5 vergi öncesi kâr | $25.258 | −$18.367 | $63.362 |
| Y5 net kâr | $25.258 | −$18.367 | $47.522 |
| Proje IRR (10 yıl) | %10,9 | negatif | %30,3 |
| Kaldıraçsız geri dönüş | 6,5 yıl | geri dönmez | 4,1 yıl |
| Azami özsermaye ihtiyacı | $85.157 | $148.384 | $63.393 |

**Beş ana bulgu:**

1. **Paketleme iyi bir karar.** Paketli kanalın kg başı katkı payı **$3,26**, halde dökme satışınki **$1,50**. Tam verimde fark yılda ~$19.000 ediyor ve bu, pakethanenin $45.000'lık yatırımını, ek sabit giderler düşüldükten sonra 3-5 yılda geri ödüyor. Daha önemlisi, v1'deki en büyük risk olan tüccar/hal fiyat baskısını yapısal olarak azaltıyor.
2. **Tesis 10 da için büyük.** Soğuk zincir, pakethane ve AgTech yatırımı 10 da'lık bahçeye bağlanınca kg başı sabit maliyet $1,34, amortisman $0,59 oluyor. Baz senaryoda proje IRR'si %10,9 ile %12 hedefin altında kalıyor. Bu, konseptin değil ölçeğin sorunu. Aynı pakethane **20 da'yı** taşıdığında IRR **%21,8**, KKYDP hibesiyle **%24,5**.
3. **Yatırımı en çok iyileştiren üç kaldıraç:** (a) KKYDP "ekonomik yatırımlar" kapsamında soğuk depo ve paketlemeye %50 hibe (IRR +3,5 puan), (b) saha emeğinin ortaktan gelmesi (+6,8 puan), (c) 2. 10 da'nın eklenmesi (+10,9 puan). Üçünden en az ikisi sağlanmalı.
4. **Teknoloji gelir kalemleri hesaba temkinli girdi.** Living lab, danışmanlık ve hizmet gelirleri baz senaryoda Y5'te toplam $11.000 (gelirin %10'u). Bunlar sıfır olsa da tarım işletmesi Y4'ten itibaren vergi öncesi kâr yazıyor (Y5'te $16.958). İşletmenin tarımsal gelirle ayakta durması ilkesi korunuyor: teknoloji tarımı süslemiyor, kârlılığını büyütüyor.
5. **Asıl ölçeklenme fırsatı Katman 4 (Farm-as-a-Service).** Kurumların ve yatırımcıların finanse ettiği yeni bahçe birimleri, bu tesiste kanıtlanmış tasarım ve yazılım yığınıyla kurulup yönetim ücreti + kâr payı karşılığında işletilebilir. Bu katman 5 yıllık projeksiyona **dahil edilmedi**. Önce Y2-Y3'te kendi verilerinle kanıtlanmalı.

**Karar: OLUMLU, fazlı yatırımla.** Faz 1 (tarla + çekirdek AgTech, $45.130) hemen başlatılabilir. Faz 2 (soğuk zincir + pakethane, $54.380) için şartlar: Q1-2028'den önce (i) en az 2 alıcıyla (bölgesel zincir/distribütör + HoReCa) ön anlaşma, (ii) hibe başvurusunun sonuçlanması veya ikinci 10 da kararının verilmesi.

---

## 1. İş Modeli

### 1.1 Dört katmanlı gelir mimarisi

| Katman | Ne satılıyor? | Müşteri | Başlangıç | Y5 baz gelir payı |
|---|---|---|---|---:|
| **1. Çekirdek — İzlenebilir premium meyve** | 100/200/500 g top-seal paketli taze böğürtlen. Her pakette QR: hasat günü, sıra no, toprak/iklim verisi, soğuk zincir sıcaklık grafiği | Bölgesel zincirler, butik market, manav, pastane/otel/kafe, online sezon kutusu | Y2 (2028) | %57 |
| **1b. Kurumsal markalı paket** | Şirketin kendi logolu paketi, "sizin sıranız" canlı veri paneli, hasat günü etkinliği (ESG/çalışan programı) | Bursa/İstanbul kurumları, bankalar, sanayi firmaları | Y3 | %21 |
| **1c. Hal ve işleme** | 2. sınıf ürün (dondurma, püre, reçel tesisi) ve fazla taze ürün | İşleme tesisleri, hal | Y2 | %11 |
| **2. Altyapı hizmeti** | Sezon dışı soğuk depo kapasitesi, komşu üreticilere ön soğutma ve paketleme | Karacabey üreticileri | Y3 | %4 |
| **3. Living lab / test alanı** | AgTech firmalarına pilot saha, ürün doğrulama verisi; üniversite-sanayi projeleri | AgTech girişimleri, sensör/gübre/biyolojik firmaları, Bursa Uludağ Üni. Ziraat Fak., TÜBİTAK projeleri | Y4 | %4 |
| **4. Danışmanlık → Farm-as-a-Service** | Tasarım + AgTech yığını + kurulum + işletme yönetimi | Yatırımcılar, kurumlar, arazi sahipleri | Y5 (danışmanlık) / Y6+ (FaaS) | %3 |

### 1.2 Değer önerisi

- **Alıcıya:** "Bu paketin hangi gün, hangi sırada toplandığını ve soğuk zincirin hiç kırılmadığını görebilirsin." Raf ömrü, hasattan sonra 2 saat içinde ön soğutma ve kesintisiz 0-2 °C ile 7-10 güne çıkıyor; soğutmasız ürünün raf ömrü 2-3 gün. Butik market ve pastane için bu fark, fire oranında %10-20 düşüş demek.
- **Kuruma:** Ölçülebilir ve şeffaf bir sürdürülebilirlik hikâyesi. Su/kg, kWh/kg ve karbon gibi veriler sensörlerden geldiği için tahmine değil ölçüme dayanıyor.
- **AgTech firmasına:** Gerçek ticari koşullarda, referans sensörle kalibre edilmiş, kontrol parselli bir test sahası. Türkiye'de bu nitelikte saha az.
- **Yatırımcıya (FaaS):** Kanıtlanmış verim ve maliyet verisiyle, uzaktan izlenebilen ve standartlaştırılmış bahçe birimleri.

### 1.3 İş modeli kanvası (özet)

| Blok | İçerik |
|---|---|
| Müşteri segmentleri | Bölgesel zincir ve butik marketler, HoReCa, online tüketici, kurumlar, işleme tesisleri, komşu üreticiler, AgTech firmaları, yatırımcılar |
| Kanallar | Distribütör (Bursa-İstanbul soğuk dağıtım), doğrudan HoReCa teslimatı, web/Instagram sezon kutusu, kurumsal satış, hal |
| Müşteri ilişkisi | QR ile şeffaflık, sezon öncesi ön sipariş, kurumsal yıllık sözleşme |
| Gelir akışları | Katman 1-4 (yukarıda) |
| Ana kaynaklar | DSİ sulu arazi, soğuk zincir + pakethane, kendi IoT/veri platformu, mühendislik bilgisi, veri arşivi |
| Ana faaliyetler | Üretim, hasat-ön soğutma-paketleme, dağıtım, yazılım/sensör geliştirme, pilot proje yönetimi |
| Ana ortaklar | Sertifikalı fidanlık, distribütör, işleme tesisi, Ziraat Bankası, İl Tarım (KKYDP), üniversite, AgTech firmaları |
| Maliyet yapısı | Sabit: personel, bakım, sertifika, marka. Değişken: hasat, ambalaj, dağıtım. Yatırım: tarla, soğuk zincir, AgTech |

### 1.4 "Şov değil, verimlilik" ilkesi: her teknolojinin bir KPI'ı olmalı

| Teknoloji | Ölçülen KPI | Hedef (Y4) | Ekonomik karşılığı |
|---|---|---|---|
| Toprak düğümleri + fertigasyon | m³ su / kg, gübre $/kg | %20 tasarruf | ~$800/yıl |
| NFC'li toplayıcı tartısı | kg / işçi-saat, kişi bazlı prim | +%15 verimlilik | ~$1.900/yıl hasat işçiliği |
| Ön soğutma + soğuk zincir logger'ı | Hasattan soğutmaya süre, fire % | < 2 saat, fire < %5 | Fire %12 → %5: ~$4.000/yıl |
| SWD tuzak kamerası | Sinek/tuzak/gün → ilaçlama zamanlaması | Kayıp < %5 | ~$2.000-5.000/yıl |
| Meyve sayım kameraları | Rekolte tahmin hatası | ±%15, 3 hafta önceden | Satışın önceden sözleşmeye bağlanması |
| Meteoroloji + yaprak ıslaklığı | Hastalık modeli tetikli ilaçlama sayısı | −%30 ilaçlama | ~$400/yıl + kalıntı riski |
| QR izlenebilirlik | Paket başı fiyat primi, tekrar sipariş oranı | +%10 fiyat | $5.000+/yıl |

---

## 2. Teknoloji Mimarisi

### 2.1 Katmanlar

| Katman | Bileşenler | Not |
|---|---|---|
| **Algılama** | 8 DIY toprak düğümü (30/60 cm nem, EC, sıcaklık), 1 profesyonel referans prob, meteoroloji istasyonu (yaprak ıslaklığı, PAR, rüzgâr, yağış), zon debimetreleri, hat içi EC/pH, soğuk oda ve sevkiyat logger'ları, enerji sayacı (GES/şebeke) | DIY sensörler referans proba göre sezonluk kalibre edilir. Toprak pH'ı laboratuvarda ölçülür |
| **Görüntü** | 2 PTZ AI + 1 termal güvenlik kamerası, 3 SWD tuzak kamerası, 4 sıra kamerası | Görüntü işleme edge sunucuda yapılır, buluta yalnız sayım/olay verisi gider |
| **İletişim** | LoRaWAN gateway (tarla), 4G + yedek hat, pakethanede Wi-Fi | Düşük güç; solar düğümler pille 2+ yıl çalışır |
| **Edge** | GPU'lu mini PC/Jetson + UPS: yerel zaman serisi veritabanı, kural motoru, kamera AI modelleri, fertigasyon PLC'si | İnternet kesilse de sulama ve alarmlar çalışır |
| **Bulut** | Veri yedeği, panolar, QR izlenebilirlik sayfaları, kurumsal müşteri panelleri, API (pilot firmalara veri paylaşımı) | Kendi barındırma; aylık ~$50 |
| **Uygulama** | Sulama/gübre önerisi, hastalık riski, rekolte tahmini, hasat ve işçi takibi, lot izlenebilirliği, soğuk zincir alarmı, LLM destekli günlük saha raporu ve anomali açıklaması | Claude/LLM: sensör verisinden günlük rapor, alarm yorumu ve doküman üretimi. Kontrol döngüsünde değil, insan onaylı karar destek katmanında |

### 2.2 İzlenebilirlik veri akışı (lot = hasat günü × sıra grubu)

1. Toplayıcı NFC kartını okutur. Kasa tartılır ve kayda **toplayıcı + sıra + saat** yazılır.
2. Kasa ön soğutma tüneline girer; giriş saati ve ürün iç sıcaklığı kaydedilir.
3. Paketleme sırasında lot numarası ve QR basılır. QR sayfasında hasat günü, sıra, son 7 günün toprak nemi ve sıcaklığı, ön soğutma süresi görünür.
4. Sevkiyat logger'ı koliye konur. Alıcıya teslimde sıcaklık grafiği lot sayfasına eklenir.
5. Müşteri şikâyetinde tek tıkla lot → sıra → hasat ekibi → sensör geçmişi zinciri çıkarılır (gıda güvenliği ve İyi Tarım denetimi için).

### 2.3 Living lab yol haritası: denenecek dünya teknolojileri

| Teknoloji | Olgunluk | Bu tesiste deneme şekli | Zaman |
|---|---|---|---|
| Otonom sıra arası biçme/çapa robotu | Ticari | Kiralama veya üretici firmayla pilot | Y3 |
| UV-C ile gece hastalık baskılama robotları (çilekte ticari) | Erken ticari | Firmayla pilot; böğürtlende küf/pas üzerine veri | Y3-Y4 |
| Multispektral drone + bitki stres haritası | Ticari | Faz 3 opsiyonu; üniversite projesiyle | Y3 |
| Biyostimülan ve mikrobiyal gübre denemeleri | Ticari | Kontrol parselli deneme, firmadan ücret | Y3+ |
| Yapay zekâ ile rekolte tahmini (meyve sayımı) | Araştırma → erken ticari | Kendi modelin; verisi lisanslanabilir | Y2+ |
| Hasat robotu (böğürtlen) | Araştırma | Gözlemci / veri ortağı; ticari beklenti yok | Y5+ |
| Agrivoltaik (sıra üstü yarı geçirgen PV) | Pilot | Gölge filesinin yerine 1 sırada deneme: gölge + elektrik | Y4 |

**Kural:** Her deneme ya dış fonla (pilot ücreti, TÜBİTAK/KOSGEB, firma) ya da Bölüm 1.4'teki bir KPI'yı iyileştirme hedefiyle yapılmalı. Ticari üretim alanının en fazla %10'u (3 sıra) deneme parseli olabilir.

---

## 3. CAPEX — Yatırım Kalemleri

### 3.1 Kalem kalem (amortisman ömrüyle)

| Faz | Grup | Kalem | USD | TL | Ömür |
|---|---|---|---:|---:|---:|
| 1 | Tarla | Toprak analizi + dip kazan + lazer tesviye + 40 t organik gübre + sedde | 3.850 | 180.950 | 10 yıl |
| 1 | Tarla | Sedde üstü agrotekstil malç (3.400 m²) | 1.100 | 51.700 | 5 yıl |
| 1 | Tarla | Doku kültürü M1 sertifikalı fidan 3.000 ad + %5 yedek + dikim | 10.050 | 472.350 | 10 yıl |
| 1 | Tarla | Telli terbiye: ~630 galvaniz direk, 3 kat tel, T-kol, ankraj, montaj | 8.500 | 399.500 | 10 yıl |
| 1 | Tarla | Sulama hidroliği: DSİ hidrant bağlantısı, ana hat, disk+kum filtre, 6.600 m çift lateral | 2.450 | 115.150 | 10 yıl |
| 1 | AgTech | Fertigasyon beyni: kendi PLC/ESP32 kontrolörün + 4 selenoid + röle panosu | 900 | 42.300 | 5 yıl |
| 1 | AgTech | Dozaj pompaları (2 gübre + 1 asit) + hat içi EC/pH probları | 2.200 | 103.400 | 5 yıl |
| 1 | AgTech | LoRaWAN gateway (4G backhaul) + yedek router + güneş/akü | 700 | 32.900 | 5 yıl |
| 1 | AgTech | 8 adet DIY toprak düğümü (30/60 cm nem-EC-sıcaklık, solar) | 2.240 | 105.280 | 5 yıl |
| 1 | AgTech | 1 adet profesyonel referans prob (DIY sensör kalibrasyonu) | 900 | 42.300 | 5 yıl |
| 1 | AgTech | Profesyonel mikro meteoroloji istasyonu (yaprak ıslaklığı, PAR, don) | 1.600 | 75.200 | 5 yıl |
| 1 | AgTech | Zon başı debimetre + basınç sensörü (4 zon) | 800 | 37.600 | 5 yıl |
| 1 | AgTech | Edge sunucu (GPU'lu mini PC / Jetson) + UPS + dış ortam kabini | 1.400 | 65.800 | 4 yıl |
| 1 | AgTech | Prototipleme / geliştirme bütçesi | 1.000 | 47.000 | 3 yıl |
| 1 | Güvenlik | 2 adet solar 4G PTZ AI kamera + 1 adet solar termal kamera | 2.900 | 136.300 | 5 yıl |
| 1 | Diğer | Şirket kuruluşu, proje, izinler (5403 tarımsal yapı izni dahil) | 1.200 | 56.400 | 5 yıl |
| 2 | Soğuk zincir & pakethane | Beton zemin + 60 m² gölgelik (konteyner sahası) | 4.000 | 188.000 | 15 yıl |
| 2 | Soğuk zincir & pakethane | Elektrik bağlantısı (trifaze) + pano | 3.500 | 164.500 | 15 yıl |
| 2 | Soğuk zincir & pakethane | 10 kWp çatı GES (lisanssız, mahsuplaşmalı) | 7.500 | 352.500 | 10 yıl |
| 2 | Soğuk zincir & pakethane | 40' reefer konteyner, yenilenmiş (67 m³, 0/+2 °C) | 8.500 | 399.500 | 10 yıl |
| 2 | Soğuk zincir & pakethane | Ön soğutma tüneli (cebri hava, fan + branda + kontrol) | 1.500 | 70.500 | 5 yıl |
| 2 | Soğuk zincir & pakethane | Paketleme odası: 30 m² izoleli prefabrik, hijyenik panel, lavabo, paslanmaz masa | 9.000 | 423.000 | 15 yıl |
| 2 | Soğuk zincir & pakethane | Yarı otomatik top-seal kapatma makinesi (100/200/500 g kalıp) | 5.500 | 258.500 | 8 yıl |
| 2 | Soğuk zincir & pakethane | 3 hassas terazi + 2 QR etiket yazıcı + barkod okuyucu | 1.800 | 84.600 | 5 yıl |
| 2 | Soğuk zincir & pakethane | Hasat ekipmanı: kasa, hasat arabası, NFC'li toplayıcı tartı istasyonu | 1.600 | 75.200 | 5 yıl |
| 2 | Soğuk zincir & pakethane | Transpalet + raf sistemi | 600 | 28.200 | 8 yıl |
| 2 | Soğuk zincir & pakethane | Gıda işletme kaydı, İyi Tarım belgesi, hijyen kurulumu | 1.500 | 70.500 | 5 yıl |
| 2 | AgTech | Soğuk zincir sensörleri (oda + 10 taşınabilir sevkiyat logger'ı) | 500 | 23.500 | 4 yıl |
| 2 | AgTech | 3 adet akıllı SWD tuzak kamerası (AI ile sinek sayımı) | 450 | 21.150 | 4 yıl |
| 2 | AgTech | 4 adet sıra kamerası (meyve sayımı → rekolte tahmini) | 600 | 28.200 | 4 yıl |
| 2 | Tarla | %35 gölge filesi + direk uzatma + montaj | 3.800 | 178.600 | 7 yıl |

### 3.2 Faz ve grup özeti

| Faz | Grup | USD | TL |
|---|---|---:|---:|
| 1 | Tarla | 25.950 | 1.219.650 |
| 1 | AgTech | 11.740 | 551.780 |
| 1 | Güvenlik | 2.900 | 136.300 |
| 1 | Diğer | 1.200 | 56.400 |
| 1 | Beklenmeyen giderler (%8) | 3.340 | 156.980 |
| **1** | **Faz 1 toplamı** | **45.130** | **2.121.110** |
| 2 | Soğuk zincir & pakethane | 45.000 | 2.115.000 |
| 2 | AgTech | 1.550 | 72.850 |
| 2 | Tarla | 3.800 | 178.600 |
| 2 | Beklenmeyen giderler (%8) | 4.030 | 189.410 |
| **2** | **Faz 2 toplamı** | **54.380** | **2.555.860** |
| | **GENEL TOPLAM (Faz 1 + 2)** | **99.510** | **4.676.970** |

**Gruplar:** Tarla $29.750 · AgTech + güvenlik $16.190 · Soğuk zincir ve pakethane $45.000 · Diğer $1.200 + %8 beklenmeyen.

**Teknik notlar:**
- **İzinler (kritik):** Mutlak tarım arazisinde soğuk depo, paketleme ünitesi ve konteyner yerleşimi **5403 sayılı Kanun kapsamında tarımsal amaçlı yapı izni** ister (İl Tarım uygunluk görüşü + belediye/il özel idaresi). Konteyner çözümü izin sürecini ortadan kaldırmaz ama yapı alanını küçültür. Faz 1'de başvuru yapılmalı.
- **Elektrik:** Arazide trifaze hat yoksa TEDAŞ bağlantı maliyeti $3.500'ün çok üstüne çıkabilir. Faz 1'de keşif yaptırılmalı. Alternatif olarak GES + akü ile off-grid soğuk oda düşünülebilir, ancak +$8-10k maliyeti var.
- **Yenilenmiş reefer konteyner:** Yeni soğuk odaya göre ~%40 ucuz, taşınabilir ve FaaS modelinde başka sahaya taşınabilir. Ünite kompresör durumu kontrol edilerek alınmalı.
- **Kendi geliştirilen AgTech:** v1'deki hazır sensör + fertigasyon paketine (~$8.650) denk bir bütçeyle (~$8.540) ölçüm noktası 3'ten 8'e çıkıyor ve bir referans prob ekleniyor. AgTech bütçesinin kalan ~$7.650'ı güvenlik, edge sunucu, kamera ve soğuk zincir katmanına gidiyor. Karşılığında **mühendislik zamanı** harcanıyor (tahmini 300-400 saat). Bu zaman maliyete yazılmadı, ama Katman 3-4'ün asıl sermayesi bu emek.

### 3.3 Faz 3 opsiyonları (projeksiyona dahil değil, tetikleyiciyle)

| Opsiyon | USD | Tetikleyici |
|---|---:|---|
| İkinci 40' reefer (hizmet kapasitesi) | 8.500 | Y3, soğuk depo hizmet talebi > %70 doluluk olursa |
| Şok dondurucu (-35 °C, 300 kg/parti) → IQF dondurulmuş böğürtlen | 14.000 | Y3-Y4, 2. sınıf ürünü $1,30 → $3,00/kg'a çıkarır |
| Multispektral drone + işleme yazılımı | 5.000 | Y3, living lab projesi fonlarsa |
| Frigorifik panelvan (2. el) | 20.000 | Y4, doğrudan HoReCa dağıtımı > 5 t/yıl olursa |
| Ek 10-20 da bahçe (kurumsal ortak finansmanlı) | 50.000 | Y4+, Farm-as-a-Service modeli |

---

## 4. Ürün, Kanal ve Birim Ekonomisi

### 4.1 Paket fiyatlandırması (üretici çıkış fiyatı, KDV hariç)

| Paket | Kanal payı | Üretici çıkış fiyatı | USD/kg | TL/paket | Ambalaj USD/paket |
|---|---:|---:|---:|---:|---:|
| 100 g | %15 | $0,70 | $7,00 | 33 TL | $0,09 |
| 200 g | %55 | $1,15 | $5,75 | 54 TL | $0,11 |
| 500 g | %30 | $2,40 | $4,80 | 113 TL | $0,18 |
| **Ağırlıklı** | | | **$5,65/kg** | | **$0,60/kg (koli dahil)** |

Raf fiyatı genellikle üretici çıkışının 1,7-2,2 katıdır. Örneğin 200 g paket rafta ~95-120 TL. Bu fiyatlar Mart 2028'e kadar en az 3 alıcıyla teyit edilmeli. 100 g paket HoReCa garnitür ve online için, 500 g pastane ve aile tüketimi için tasarlandı.

### 4.2 Birim ekonomi (kg başı)

| kg başı (USD) | Paketli | Hal (dökme) |
|---|---:|---:|
| Satış fiyatı | 5,65 | 2,50 |
| Kanal payı / komisyon | −0,68 | −0,25 |
| Soğuk sevkiyat / kasa | −0,30 | −0,20 |
| Ambalaj + koli | −0,60 | – |
| Pakethane işçiliği | −0,12 | – |
| Hasat işçiliği | −0,70 | −0,55 |
| **Katkı payı** | **3,26** | **1,50** |

### 4.3 Hacim ve kanal dağılımı (baz)

| Yıl | Rekolte | 2. sınıf (%20) → işleme | Kurumsal | Paketli (taze içindeki pay) | Hal | Paket adedi | Günlük paket (63 gün) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Y2 2028 | 5 t | 1,0 t | – | 2,0 t (%50) | 2,0 t | 9.700 | ~154 |
| Y3 2029 | 14 t | 2,8 t | 0,5 t | 7,0 t (%65) | 3,7 t | 33.732 | ~535 |
| Y4 2030 | 20 t | 4,0 t | 1,5 t | 10,9 t (%75) | 3,6 t | 52.744 | ~837 |
| Y5 2031 | 20 t | 4,0 t | 2,5 t | 10,8 t (%80) | 2,7 t | 52.380 | ~831 |

Günde ~830 paket, 2 kişilik paketleme hattı ve yarı otomatik top-seal makinesi (saatte 400-600 paket) ile karşılanabilir. Darboğaz paketleme değil, **günde 830 paketin satılması**. Kanal planı bu yüzden kademeli: Y2'de 1 distribütör + 5-10 HoReCa, Y3'te +1 bölgesel zincir + online sezon kutusu.

---

## 5. OPEX — İşletme Giderleri

### 5.1 Sabit giderler

| Sabit gider (USD/yıl) | Y1 | Y2 | Y3 | Y4 | Y5 |
|---|---:|---:|---:|---:|---:|
| Gübre + biyolojik/kimyasal mücadele | 1.100 | 2.000 | 2.800 | 3.000 | 3.000 |
| Budama, bağlama, ot biçimi (yevmiyeli) | 1.100 | 1.850 | 2.400 | 2.500 | 2.500 |
| DSİ su ücreti + pompa | 250 | 400 | 500 | 500 | 500 |
| Daimi tarım teknisyeni (asgari ücret, işveren maliyeti) | 4.500 | 9.000 | 9.000 | 9.000 | 9.000 |
| Sezonluk pakethane sorumlusu | 0 | 1.500 | 2.500 | 2.500 | 2.500 |
| Elektrik (GES mahsubu sonrası) | 150 | 500 | 700 | 700 | 700 |
| Bakım-onarım | 300 | 1.200 | 1.800 | 2.000 | 2.000 |
| Sigorta (TARSİM + tesis) | 0 | 900 | 1.100 | 1.150 | 1.150 |
| Bulut, SIM, yazılım, veri saklama | 500 | 600 | 600 | 700 | 700 |
| İyi Tarım denetimi, gıda güvenliği analizleri | 0 | 700 | 700 | 700 | 700 |
| Marka, ambalaj tasarımı, web, numune, fuar | 1.000 | 2.000 | 2.500 | 2.500 | 2.500 |
| Muhasebe, hukuk, şirket giderleri | 1.200 | 1.500 | 1.500 | 1.500 | 1.500 |
| **Toplam** | **10.100** | **22.150** | **26.100** | **26.750** | **26.750** |

### 5.2 Değişken giderler

| Kalem | Değer |
|---|---|
| Hasat işçiliği, paketli ürün (tarlada punnet'e) | $0,70/kg |
| Hasat işçiliği, dökme/işleme | $0,55/kg |
| Ambalaj: 100 g $0,09 · 200 g $0,11 · 500 g $0,18 / paket + koli $0,05/kg | Ağırlıklı $0,60/kg |
| Pakethane işçiliği | $0,12/kg |
| Distribütör / kanal payı (paketli) | %12 |
| Soğuk sevkiyat (paketli) | $0,30/kg |
| Kurumsal paket ek marka/etkinlik maliyeti | $1,20/kg |
| Hal komisyonu + rüsum + kasa | %10 + $0,20/kg |
| Hizmet gelirlerinin maliyeti | Soğuk depo %35, living lab %25, danışmanlık %10 |

**Hariç tutulan:** Kurucu/mühendis maaşı. Kurucu yılda $12.000 maaş alırsa baz senaryoda Y5 vergi öncesi kârı $25.258 → $13.258'e iner.

---

## 6. Beş Yıllık Finansal Projeksiyon (2027-2031)

### 6.1 Baz senaryo — Gelir tablosu

| Kalem (USD) | Y1 2027 | Y2 2028 | Y3 2029 | Y4 2030 | Y5 2031 |
|---|---:|---:|---:|---:|---:|
| Rekolte (ton) | 0,0 | 5,0 | 14,0 | 20,0 | 20,0 |
| — Paketli satış (100/200/500 g) | 0 | 11.305 | 39.313 | 61.471 | 61.047 |
| — Kurumsal markalı paket | 0 | 0 | 4.500 | 13.500 | 22.500 |
| — Hal / dökme taze | 0 | 5.000 | 9.362 | 9.062 | 6.750 |
| — 2. sınıf → işleme | 0 | 1.300 | 3.640 | 5.200 | 5.200 |
| — Soğuk depo / paketleme hizmeti | 0 | 0 | 1.500 | 3.000 | 4.000 |
| — Living lab / test-bed projeleri | 0 | 0 | 0 | 2.000 | 4.000 |
| — Danışmanlık | 0 | 0 | 0 | 0 | 3.000 |
| **TOPLAM GELİR** | **0** | **17.605** | **58.316** | **94.233** | **106.497** |
| Hasat işçiliği | 0 | −3.050 | −8.818 | −12.856 | −12.995 |
| Ambalaj + pakethane işçiliği | 0 | −1.431 | −5.334 | −8.854 | −9.516 |
| Dağıtım, komisyon, soğuk sevkiyat | 0 | −2.946 | −9.339 | −14.426 | −15.137 |
| Hizmet gelirlerinin maliyeti | 0 | 0 | −525 | −1.550 | −2.700 |
| **BRÜT KÂR** | **0** | **10.178** | **34.300** | **56.547** | **66.149** |
| Sabit işletme giderleri | −10.100 | −22.150 | −26.100 | −26.750 | −26.750 |
| **FAVÖK (EBITDA)** | **−10.100** | **−11.972** | **8.200** | **29.797** | **39.399** |
| Amortisman | −5.020 | −12.486 | −12.486 | −12.153 | −11.803 |
| Finansman gideri (Ziraat kredisi faizi) | −3.538 | −7.261 | −6.153 | −4.497 | −2.338 |
| **VERGİ ÖNCESİ KÂR** | **−18.658** | **−31.719** | **−10.440** | **13.147** | **25.258** |
| Kurumlar vergisi (%25, zarar mahsuplu) | 0 | 0 | 0 | 0 | 0 |
| **NET KÂR (VERGİ SONRASI)** | **−18.658** | **−31.719** | **−10.440** | **13.147** | **25.258** |
| FAVÖK marjı | – | −%68 | %14 | %32 | %37 |
| Net kâr marjı | – | −%180 | −%18 | %14 | %24 |

**Okuma notu:** Y1-Y3 zararları (toplam $60.817) kurumlar vergisinde 5 yıl boyunca mahsup edilebiliyor. Bu nedenle baz senaryoda 2031'e kadar vergi çıkmıyor. Kalıcı dönemde (Y6+) vergi öncesi kâr ~$27-30k, vergi ~$7k/yıl.

### 6.2 Baz senaryo — Nakit akışı ve finansman

| Nakit akışı (USD) | Y0 | Y1 2027 | Y2 2028 | Y3 2029 | Y4 2030 | Y5 2031 |
|---|---:|---:|---:|---:|---:|---:|
| FAVÖK | 0 | −10.100 | −11.972 | 8.200 | 29.797 | 39.399 |
| Ödenen vergi | 0 | 0 | 0 | 0 | 0 | 0 |
| Yatırım (CAPEX) | −45.130 | −54.380 | 0 | 0 | 0 | 0 |
| Kredi kullanımı | 22.565 | 27.190 | 0 | 0 | 0 | 0 |
| Faiz ödemesi | 0 | −3.538 | −7.261 | −6.153 | −4.497 | −2.338 |
| Anapara ödemesi | 0 | 0 | 0 | −4.578 | −9.396 | −7.963 |
| **Net nakit (özsermaye)** | −22.565 | −40.828 | −19.233 | −2.531 | 15.904 | 29.099 |
| **Kümülatif** | −22.565 | −63.393 | −82.625 | −85.157 | −69.253 | −40.154 |

Kredi kurgusu: her fazın %50'si Ziraat Bankası Hazine faiz destekli TL kredisiyle karşılanıyor (%18,5, 2 yıl ödemesiz + 3 yıl eşit anapara, TL'de yıllık %18 değer kaybı varsayımı). Faz 1 kredisi Y0'da, Faz 2 kredisi Y1 sonunda kullanılıyor.

**Özsermaye ihtiyacı:** Kümülatif en derin nokta Y3'te **−$85.157 (~4,0 M TL)**. Bu tutar CAPEX'in özsermaye payını ($49.755) ve Y1-Y3 işletme açıklarını kapsıyor. Ayrıca temmuz-eylül arasında, alıcıların 45-60 günlük vadesi yüzünden **$10-15k sezonluk işletme sermayesi** gerekir. Kısa vadeli Ziraat işletme kredisi veya KMH ile karşılanabilir.

### 6.3 Pesimistik senaryo — Gelir tablosu

Varsayımlar: verim −%25 (tam verim 15 t), 2. sınıf payı %25, tüm fiyatlar −%20, hasat işçiliği +%30, paketli pay en fazla %60, living lab ve danışmanlık geliri yok.

| Kalem (USD) | Y1 2027 | Y2 2028 | Y3 2029 | Y4 2030 | Y5 2031 |
|---|---:|---:|---:|---:|---:|
| Rekolte (ton) | 0,0 | 3,8 | 10,5 | 15,0 | 15,0 |
| — Paketli satış (100/200/500 g) | 0 | 5.087 | 17.805 | 26.736 | 27.810 |
| — Kurumsal markalı paket | 0 | 0 | 0 | 3.600 | 7.200 |
| — Hal / dökme taze | 0 | 3.375 | 7.875 | 9.675 | 8.200 |
| — 2. sınıf → işleme | 0 | 975 | 2.730 | 3.900 | 3.900 |
| — Soğuk depo / paketleme hizmeti | 0 | 0 | 0 | 1.000 | 1.500 |
| — Living lab / test-bed projeleri | 0 | 0 | 0 | 0 | 0 |
| — Danışmanlık | 0 | 0 | 0 | 0 | 0 |
| **TOPLAM GELİR** | **0** | **9.437** | **28.410** | **44.911** | **48.610** |
| Hasat işçiliği | 0 | −2.901 | −8.275 | −11.975 | −12.119 |
| Ambalaj + pakethane işçiliği | 0 | −805 | −2.817 | −4.588 | −5.116 |
| Dağıtım, komisyon, soğuk sevkiyat | 0 | −1.699 | −5.106 | −7.822 | −8.327 |
| Hizmet gelirlerinin maliyeti | 0 | 0 | 0 | −350 | −525 |
| **BRÜT KÂR** | **0** | **4.033** | **12.212** | **20.176** | **22.523** |
| Sabit işletme giderleri | −10.100 | −22.150 | −26.100 | −26.750 | −26.750 |
| **FAVÖK (EBITDA)** | **−10.100** | **−18.117** | **−13.888** | **−6.574** | **−4.227** |
| Amortisman | −5.020 | −12.486 | −12.486 | −12.153 | −11.803 |
| Finansman gideri (Ziraat kredisi faizi) | −3.538 | −7.261 | −6.153 | −4.497 | −2.338 |
| **VERGİ ÖNCESİ KÂR** | **−18.658** | **−37.865** | **−32.528** | **−23.224** | **−18.367** |
| Kurumlar vergisi (%25, zarar mahsuplu) | 0 | 0 | 0 | 0 | 0 |
| **NET KÂR (VERGİ SONRASI)** | **−18.658** | **−37.865** | **−32.528** | **−23.224** | **−18.367** |
| FAVÖK marjı | – | −%192 | −%49 | −%15 | −%9 |
| Net kâr marjı | – | −%401 | −%114 | −%52 | −%38 |

### 6.4 İyimser senaryo — Gelir tablosu ve nakit

Varsayımlar: tam verim 24-25 t, 2. sınıf payı %15, fiyatlar +%5, kurumsal satış 4 t'ye çıkıyor, living lab Y5'te $10k, danışmanlık $8k, pakethaneye KKYDP %50 hibe.

| Kalem (USD) | Y1 2027 | Y2 2028 | Y3 2029 | Y4 2030 | Y5 2031 |
|---|---:|---:|---:|---:|---:|
| Rekolte (ton) | 0,0 | 6,0 | 17,0 | 24,0 | 25,0 |
| — Paketli satış (100/200/500 g) | 0 | 15.669 | 53.802 | 82.617 | 87.024 |
| — Kurumsal markalı paket | 0 | 2.835 | 14.175 | 28.350 | 37.800 |
| — Hal / dökme taze | 0 | 5.670 | 10.198 | 9.135 | 6.792 |
| — 2. sınıf → işleme | 0 | 1.228 | 3.481 | 4.914 | 5.119 |
| — Soğuk depo / paketleme hizmeti | 0 | 0 | 2.500 | 4.500 | 6.000 |
| — Living lab / test-bed projeleri | 0 | 0 | 2.000 | 6.000 | 10.000 |
| — Danışmanlık | 0 | 0 | 0 | 4.000 | 8.000 |
| **TOPLAM GELİR** | **0** | **25.402** | **86.156** | **139.516** | **160.735** |
| Hasat işçiliği | 0 | −3.741 | −10.935 | −15.738 | −16.549 |
| Ambalaj + pakethane işçiliği | 0 | −2.104 | −7.559 | −12.106 | −13.353 |
| Dağıtım, komisyon, soğuk sevkiyat | 0 | −4.113 | −13.004 | −19.627 | −21.179 |
| Hizmet gelirlerinin maliyeti | 0 | 0 | −1.375 | −3.475 | −5.400 |
| **BRÜT KÂR** | **0** | **15.445** | **53.282** | **88.570** | **104.253** |
| Sabit işletme giderleri | −10.100 | −22.150 | −26.100 | −26.750 | −26.750 |
| **FAVÖK (EBITDA)** | **−10.100** | **−6.705** | **27.182** | **61.820** | **77.503** |
| Amortisman | −5.020 | −12.486 | −12.486 | −12.153 | −11.803 |
| Finansman gideri (Ziraat kredisi faizi) | −3.538 | −7.261 | −6.153 | −4.497 | −2.338 |
| **VERGİ ÖNCESİ KÂR** | **−18.658** | **−26.453** | **8.543** | **45.170** | **63.362** |
| Kurumlar vergisi (%25, zarar mahsuplu) | 0 | 0 | 0 | −2.151 | −15.841 |
| **NET KÂR (VERGİ SONRASI)** | **−18.658** | **−26.453** | **8.543** | **43.019** | **47.522** |
| FAVÖK marjı | – | −%26 | %32 | %44 | %48 |
| Net kâr marjı | – | −%104 | %10 | %31 | %30 |

| Nakit akışı (USD) | Y0 | Y1 2027 | Y2 2028 | Y3 2029 | Y4 2030 | Y5 2031 |
|---|---:|---:|---:|---:|---:|---:|
| FAVÖK | 0 | −10.100 | −6.705 | 27.182 | 61.820 | 77.503 |
| Ödenen vergi | 0 | 0 | 0 | 0 | −2.151 | −15.841 |
| Yatırım (CAPEX) | −45.130 | −54.380 | 0 | 0 | 0 | 0 |
| Hibe (KKYDP) | 0 | 0 | 22.500 | 0 | 0 | 0 |
| Kredi kullanımı | 22.565 | 27.190 | 0 | 0 | 0 | 0 |
| Faiz ödemesi | 0 | −3.538 | −7.261 | −6.153 | −4.497 | −2.338 |
| Anapara ödemesi | 0 | 0 | 0 | −4.578 | −9.396 | −7.963 |
| **Net nakit (özsermaye)** | −22.565 | −40.828 | 8.534 | 16.451 | 45.776 | 51.362 |
| **Kümülatif** | −22.565 | −63.393 | −54.859 | −38.408 | 7.368 | 58.730 |

### 6.5 Senaryo karşılaştırması

| Gösterge | Baz | Pesimistik | İyimser |
|---|---:|---:|---:|
| Y5 rekolte | 20,0 t | 15,0 t | 25,0 t |
| Y5 gelir | $106.497 | $48.610 | $160.735 |
| Y5 FAVÖK | $39.399 | −$4.227 | $77.503 |
| Y5 vergi öncesi kâr | $25.258 | −$18.367 | $63.362 |
| Y5 net kâr | $25.258 | −$18.367 | $47.522 |
| 5 yıl kümülatif net kâr | −$22.411 | −$130.641 | $53.973 |
| Proje IRR (10 yıl, kaldıraçsız) | %10,9 | negatif | %30,3 |
| Özsermaye IRR (kredili) | %13,8 | negatif | %40,3 |
| Geri dönüş (kaldıraçsız, Y0'dan) | 6,5 yıl | geri dönmez | 4,1 yıl |

---

## 7. Vergi ve Hukuki Yapı

| Yapı | Avantaj | Dezavantaj | Y5 (baz) yaklaşık vergi |
|---|---|---|---:|
| **A. Ltd. Şti. (tüm faaliyetler)** | Ortak/yatırımcı alımı kolay (waterfall), zarar mahsubu, hibe/kredi ve kurumsal sözleşme için güvenilir muhatap, Katman 3-4 ile uyumlu | %25 kurumlar vergisi, enflasyon düzeltmesi, muhasebe maliyeti | Y5: $0 (mahsup); kalıcı dönemde ~$7k/yıl |
| **B. Gerçek kişi çiftçi (ÇKS) + Ltd. (hizmetler)** | Taze meyve satışında %2 (borsa tescilli %1) stopaj nihai vergi olabilir. Y5 meyve geliri $95.497 → ~$1.900 | İki yapı arasında transfer fiyatlaması, paketli satışın "zirai kazanç" sayılması mali müşavirce teyit edilmeli, ortak alımı zor | Meyve ~$1.900 + hizmetler |

**Öneri:** **Y0'da Ltd. Şti.** Gerekçeler: (i) Y1-Y3 zararları ileride mahsup edilir, (ii) Farm-as-a-Service ve ortaklık modeli tüzel kişilik ister, (iii) kurumsal ve AgTech müşterileri fatura muhatabı olarak şirket ister. Arazi sahibi ÇKS kaydını korur. Arazi şirkete kiralanır veya intifa hakkı verilir. Yapı Y4'te, kâr kalıcı hâle geldiğinde B'ye göre yeniden değerlendirilmeli.

**KDV notu:** Taze meyvede KDV %1, ambalaj ve ekipmanda %20. Bu fark yapısal olarak **devreden KDV** biriktirir. İndirimli orana tabi teslimlerde yıllık KDV iadesi başvurusu süreç olarak planlanmalı.

**Teknoloji teşvikleri:** Yazılım ve sensör geliştirme için **TÜBİTAK 1507 (KOBİ Ar-Ge)** ve **KOSGEB Ar-Ge/İnovasyon** destekleri değerlendirilebilir. Bunlar living lab katmanının ilk 2 yılını fonlayabilir; projeksiyona dahil edilmedi.

---

## 8. Duyarlılık, Başabaş ve Yapısal Varyantlar

### 8.1 Başabaş (Y5, baz yapı)

| Değişken | Başabaş değeri | Baz | Güvenlik payı |
|---|---:|---:|---:|
| Tüm fiyatlar | Bazın %71'i (paketli ~$4,02/kg) | $5,65/kg | **%29** |
| Rekolte | 11,3 t (1,13 t/da) | 20 t | **%44** |
| Sadece meyve geliri (hizmet/lab/danışmanlık = 0) | Y5 vergi öncesi kâr $16.958 | $25.258 | Tarım tek başına kârlı |

v1'de stres senaryosunda proje kâr payı tamamen eriyordu. v2'de paketli kanalın yüksek katkı payı sayesinde fiyat şokuna dayanıklılık belirgin şekilde artıyor. Buna karşılık sabit maliyetler yükseldiği için **düşük rekolteye (pesimistik) duyarlılık arttı**.

### 8.2 Yapısal varyantlar (10 yıllık proje getirisi)

| Varyant | CAPEX | Y5 vergi öncesi kâr | Proje IRR | Özsermaye IRR | Geri dönüş | Azami özsermaye ihtiyacı |
|---|---:|---:|---:|---:|---:|---:|
| Baz (tam paket, 10 da) | $99.510 | $25.258 | %10,9 | %13,8 | 6,5 yıl | $85.157 |
| + KKYDP %50 hibe (pakethane) | $99.510 | $25.258 | %14,4 | %18,9 | 5,7 yıl | $63.393 |
| + Saha emeği ortaktan (teknisyen yok) | $99.510 | $34.258 | %17,7 | %23,1 | 5,3 yıl | $69.125 |
| + Hibe + ortak emeği | $99.510 | $34.258 | %21,6 | %29,5 | 4,7 yıl | $58.893 |
| 20 da (aynı pakethane, hibesiz) | $134.060 | $63.346 | %21,8 | %28,2 | 4,7 yıl | $101.603 |
| 20 da + hibe | $134.060 | $63.346 | %24,5 | %32,5 | 4,4 yıl | $85.505 |

**Okuma:**
- **En verimli kaldıraç ölçek.** Aynı pakethane ve AgTech altyapısı 20 da'yı taşıyor. Ek 10 da için ~$34.500 ek CAPEX, Y5 vergi öncesi kârı $25k'dan $63k'ya çıkarıyor. Ancak satılması gereken paket sayısı da ikiye katlanıyor (~105.000 paket/sezon). Bu yüzden 2. 10 da'nın dikimi, **Y2 (2028) satış performansı görüldükten sonra** 2029 ilkbaharında yapılmalı.
- **Hibe** azami özsermaye ihtiyacını $85k'dan $63k'ya indiriyor. KKYDP başvuru takvimi her yıl tebliğle açıklanır. Faz 2'nin zamanlaması bu takvime göre ayarlanmalı. Hibe hak edişle (yatırım bitince) ödendiği için ara finansman gerekir.
- **Ortak emeği:** Arazi sahibi ortak saha işini üstlenirse daimi teknisyen maliyeti ($9.000/yıl) düşüyor ve proje IRR'si %17,7'ye çıkıyor. v1'deki waterfall modeli bu durumda geçerliliğini korur.

---

## 9. Finansman ve Ortaklık Modeli

### 9.1 Finansman kaynakları (baz, $99.510 CAPEX + ~$25k işletme açığı + ~$12k sezon sermayesi)

| Kaynak | Tutar (USD) | Not |
|---|---:|---|
| Ziraat Bankası Hazine faiz destekli kredi | 49.755 | CAPEX'in %50'si, iki dilimde. %50 faiz indiriminin geçerliliği 31.12.2026'ya kadar açıklandı. **Faz 1 başvurusu 2026 bitmeden yapılmalı** |
| KKYDP ekonomik yatırımlar hibesi | 0-22.500 | Soğuk depo ve paketleme; başvuru takvimine bağlı |
| TÜBİTAK 1507 / KOSGEB | 0-15.000 | Yazılım/sensör geliştirme; projeksiyon dışı |
| Kurucu + ortak özsermayesi | ~63.000-85.000 | Hibeye göre değişir |
| İşletme kredisi (sezonluk) | 10.000-15.000 | Temmuz-eylül |

### 9.2 Ortaklık yapısı

- **Arazi sahibi ile (v1 waterfall, güncellenmiş):** Brüt meyve gelirinin %5'i saha ücreti, ardından sermaye iadesine kadar 85/15, %12 IRR'ye kadar 70/30, sonrasında 50/50. Arazi sahibi saha emeğini üstlenirse teknisyen giderinin yerine geçer ve payı yükselir. Önerilen değişiklik: Kademe 3'te 50/50 yerine **55/45**.
- **Kurumsal ortak ("kurumlara ürettirmek"):** Bir kurum (gıda markası, pastane zinciri, ESG bütçesi olan şirket) ek 10 da'nın CAPEX'ini (~$35k) finanse eder. Karşılığında ürünün %50'si önceden belirlenmiş fiyatla (örneğin $4,50/kg paketli) kendi markasıyla kuruma teslim edilir. Kalan ürün ve tüm işletme kontrolü tesiste kalır. Kurumun fiyat ve tedarik güvencesi olur; tesisin satış riski ve sermaye ihtiyacı düşer. 2. 10 da'yı finanse etmenin en iyi yolu budur.
- **Farm-as-a-Service (Y6+):** Standart birim 10-20 da. Kurulum tasarım ücreti: CAPEX'in %8'i. Yazılım ve izleme aboneliği: $150-250/da/yıl. İşletme yönetim ücreti: brüt gelirin %10'u. Performans payı: hedef IRR üstü kârın %20'si. 5 birimlik bir portföy, yalnız yönetim ve abonelik gelirinden yılda ~$40-60k üretir. Bu potansiyel, Y2-Y4 verileriyle kanıtlanmadan yatırımcıya sunulmamalı.

---

## 10. Riskler (v2'de yeni veya değişen)

| Risk | Olasılık | Etki | Önlem |
|---|---|---|---|
| **Günde 800+ paketi satamama** | Orta | Yüksek | Kademeli kanal planı, sezon öncesi ön sipariş, kurumsal yıllık sözleşme, fazla ürün için hal/işleme çıkışı |
| **Alıcı vadesi / tahsilat** | Yüksek | Orta | Faktoring, distribütörde teminat, HoReCa'da peşin/kısa vade |
| **Yapı izni / elektrik bağlantısı gecikmesi** | Orta | Yüksek | Faz 1'de başvuru; konteyner + GES yedek plan |
| **Gıda güvenliği olayı** | Düşük | Çok yüksek | İşletme kaydı, İyi Tarım, lot izlenebilirliği, ürün sorumluluk sigortası |
| **Aşırı mühendislik / dağınık odak** | Orta | Orta | Bölüm 1.4 KPI kuralı, deneme parseli üst sınırı %10, yıllık teknoloji bütçesi tavanı |
| **DIY sensör güvenilirliği** | Orta | Düşük-orta | Referans prob, kritik kararlar için yedekli ölçüm, otomasyonda manuel geçersiz kılma |
| **Sabit maliyet / ölçek uyumsuzluğu** | Yüksek (10 da'da) | Orta | 2. 10 da veya kurumsal ortak, komşu üreticilere hizmet |
| **Fiyat, iklim, SWD, işçi** (v1'den) | | | v1 Bölüm 4 önlemleri geçerli. Paketli kanal fiyat riskini azaltır |

---

## 11. Uygulama Yol Haritası ve Karar Kapıları

| Dönem | İş | Karar kapısı |
|---|---|---|
| Ekim-Aralık 2026 | Ltd. kuruluşu, Ziraat Faz 1 kredi başvurusu, toprak analizi, elektrik keşfi, yapı izni başvurusu, fidan siparişi | Kredi onayı |
| Q1 2027 | Faz 1 tarla kurulumu, dikim (Mart-Nisan), sensör ağının ilk sürümü | |
| 2027 | Veri platformu, QR izlenebilirlik yazılımı, marka/ambalaj tasarımı, alıcı görüşmeleri, KKYDP başvurusu | **Kapı 1 (Kasım 2027):** ≥ 2 alıcı ön anlaşması → Faz 2 onayı |
| Q1-Q2 2028 | Faz 2: konteyner pakethane, reefer, GES, gölge filesi; İyi Tarım ve işletme kaydı | |
| Haz-Ağu 2028 | İlk hasat (5 t), ilk paketli satış | **Kapı 2 (Eylül 2028):** paketli fiyat ≥ $5/kg ve satış oranı ≥ %80 → 2. 10 da (2029 ilkbahar) / kurumsal ortak |
| 2029 | 14 t, ilk kurumsal paketler, soğuk depo hizmeti, ilk living lab pilotu | **Kapı 3:** Faz 3 opsiyonları (2. reefer, şok dondurucu) |
| 2030-2031 | Tam verim, danışmanlık, FaaS pilot birimi tasarımı | **Kapı 4:** FaaS için 3 yıllık doğrulanmış veri seti |

---

## 12. Sonuç

1. Soğuk zincir ve paketleme eklenince proje **hal fiyatına mahkûm bir bahçeden kendi fiyatını kuran bir ürün işletmesine** dönüşüyor. Paketli kanalın kg başı katkı payı halin 2,2 katı.
2. Bu altyapı 10 da için büyük. Baz senaryo kâra geçiyor (Y5 vergi öncesi $25k), ancak 10 yıllık IRR %10,9 ile sınırda. Projeyi güçlü bir yatırıma çeviren unsurlar **ölçek (20 da), hibe ve kurumsal ortaklık**. Yol haritası bunları karar kapılarına bağladı.
3. Teknoloji vizyonu iş modeline doğrudan kazandırıyor: QR izlenebilirlik fiyat primi, hasat/soğuk zincir verisi fire ve işçilik tasarrufu, veri arşivi de Katman 3-4 için sermaye sağlıyor. Living lab ve danışmanlık gelirleri olmasa da tarım işletmesi tek başına kâr ediyor.
4. İlk adım zaman kritik: **Ltd. kuruluşu ve Ziraat Faz 1 kredi başvurusu 31.12.2026'dan önce yapılmalı.**

---

### Ek — Ana varsayımlar

| Varsayım | Değer |
|---|---|
| Kur | 1 USD = 47 TL (Ekim 2026 çalışma kuru; doğrulanmalı) |
| Fiyat bazı | 2026 sabit USD (TL enflasyonunun satış fiyatlarına yansıdığı varsayımı) |
| Verim (baz) | 0 / 5 / 14 / 20 / 20 t (2,0 t/da tam verim) |
| Kurumlar vergisi | %25, zarar mahsubu 5 yıl, enflasyon düzeltmesi dahil değil |
| Kredi | %50 CAPEX, %18,5 TL, 2+3 yıl, TL yıllık %18 değer kaybı |
| 10 yıllık getiri | Y6-Y8 sabit, Y9 −%10, Y10 −%20 verim; Y6'da $8k elektronik yenileme; kalıntı değer yok |
| Hibe muhasebesi | Basitlik için amortisman matrahından düşülmedi (vergi etkisi sınırlı) |
| Ekipman fiyatları | 2026 Türkiye piyasa tahminleri; her kalem için en az 3 teklif alınmalı |

Kaynaklar: Hazine destekli tarımsal kredi faiz indirimi — [Bloomberg HT](https://www.bloomberght.com/tarimsal-uretimde-kullandirilacak-kredilere-iliskin-esaslar-belirlendi-2351935), [Bloomberg HT (faiz desteği)](https://www.bloomberght.com/subvansiyonlu-tarim-kredilerinde-eski-faiz-destegi-geri-geldi-3760308); böğürtlen yetiştiriciliği — [TAGEM Yalova](https://arastirma.tarimorman.gov.tr/yalovabahce/Belgeler/brosurler/OrganikBogurtlen.pdf).
