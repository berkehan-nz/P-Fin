# Böğürtlen İş Planı — Risk ve Gerçekçilik Testi: Bölgedeki Çiftçi Neden Yapmıyor, ROI Nerede İyimser?

*Ekim 2026 · 10 da böğürtlen + kendin-topla (son hâl) · Ekim 2026 TL, reel · model: [model_risk.py](model_risk.py)*

> **Kısa cevap.** Haklısınız, son hâldeki ROI iyimser. Rapordaki her varsayım tek başına makul. Ama hepsi aynı anda iyi tarafta duruyor. Asıl kırılgan nokta fiyat. Model tüm kanalların ortalamasında **214 TL/kg** satış varsayıyor. Bursa'da sahada konuşulan rakamlar 60-150 TL/kg aralığında. Varsayımları gerçekçi tarafa çektiğimizde 2031 net kâr **2,43 M TL'den ~0 TL'ye** iniyor ve yatırım 10 yılda geri dönmüyor. Proje ancak **≥ ~200 TL/kg ortalama satış fiyatı yazılı olarak garanti altına alınabilirse** cazip. Bu yüzden ilk iş toprak analizinin yanında **fiyatı doğrulamak**. 1,57 M TL'nin tamamı ancak ondan sonra harcanmalı.

---

## 1. Bölgedeki çiftçi neden yapmıyor?

Böğürtlen Bursa için yeni bir ürün değil. Bursa ahududu-böğürtlen üretiminde Türkiye'nin önde gelen illerinden ([Uludağ Üni. ekonomik analiz](https://acikerisim.uludag.edu.tr/items/83c730ce-852a-4cb8-9cbc-9f8073082824)). Ama ovada, Karacabey'de, büyük ölçekte yapılmıyor. Bunun yapısal nedenleri var:

1. **Alıcı garantisi yok.** Domates, mısır, pancar, biber için kontratlı fabrika ya da tüccar ağı hazır. Böğürtlende Bursa'da organize bir alıcı yok. Ürün ya hale ya da birkaç tüccara gidiyor. Kestel üreticisinin ifadesiyle *"birkaç tüccar kendi arasında anlaşarak köylüden istediği fiyata ürünü alıyor"* ([Bursa Hakimiyet](https://www.bursahakimiyet.com.tr/bursa/bursa-kestel-de-ahududu-ve-bogurtlen-uretimi-sirbistan-modeliyle-artirilacak-1563261)).
2. **Ürün 2-3 günde bozuluyor, pazarlık gücü sıfır.** Soğuk odası olmayan üretici aynı gün satmak zorunda. Tüccar bunu bildiği için fiyatı akşamüstü kırıyor.
3. **Hasat çok pahalı.** Kestel'de bir işçi günde en fazla ~25 kg ahududu topluyor, yevmiye 1.500 TL. Yani yalnızca toplama maliyeti ~60 TL/kg ([Bursa Hakimiyet](https://www.bursahakimiyet.com.tr/bursa/bursa-kestel-de-ahududu-ve-bogurtlen-uretimi-sirbistan-modeliyle-artirilacak-1563261)). Böğürtlen daha hızlı toplanıyor ama paket kalitesinde ~40-55 kg/gün. Mısırda bu maliyet yok, biçerdöver geliyor.
4. **Dış kaynaklı ürünle fiyat rekabeti var.** Aynı haberde 150 TL/kg üretici çıkışına rağmen *"dış kaynaklardan aynı fiyata getirilen ürünler nedeniyle üreticiler mücadele edemedi"* deniyor. Dondurulmuş ve işlemelik pazar ithalat ve Sırbistan fiyatına bağlı.
5. **Sabır ve sermaye ister.** Mısır her yıl nakit getiriyor. Böğürtlen 1,5 M TL yatırım istiyor ve ilk 2 yıl zarar yazıyor. Ovada ortalama işletme küçük ve borçlu, 3-4 yıl beklemeyi kaldıramıyor.
6. **Bilgi gerektiriyor.** Çeşit seçimi, sürgün yönetimi, tel sistemi, SWD mücadelesi ve hasat zamanlaması tarla bitkisinden çok farklı. Erken toplanan dikensiz böğürtlen ekşi kalıyor ve satılmıyor.
7. **Emek havuzu daralıyor.** Ahududunun Kestel'de *"tükenmek üzere"* olmasının ana sebebi rekolte ve işçilik ([Türk Haber](https://www.turkhaber.com/haber/ahududu-bursa-da-yok-olmak-uzere-4118617)). TEKNOSAB devreye girdikçe Karacabey'de sezonluk işçi bulmak zorlaşacak, yevmiye artacak.

**Sonuç:** Çiftçi böğürtlenin kârsız olduğunu düşündüğü için değil, **satış riski ve işçilik yükü kendi ölçeğine göre fazla geldiği için** yapmıyor. Bizim planın farkı da tam olarak bu iki noktaya dayanıyor: ortak, kendin-topla ve soğuk oda. Bu yüzden planın kaderi o iki noktanın gerçekten çalışmasına bağlı.

## 2. Üreticiler nelerden şikâyet ediyor?

| Şikâyet | Kaynak / örnek | Bizim plandaki karşılığı |
|---|---|---|
| Tüccar fiyatı belirliyor, emek boşa gidiyor | Kestel üreticileri ([Bursa Hakimiyet](https://www.bursahakimiyet.com.tr/bursa/bursa-kestel-de-ahududu-ve-bogurtlen-uretimi-sirbistan-modeliyle-artirilacak-1563261)); tarlada-hal arası fiyat makası genel bir sorun ([Gazete Vatan](https://www.gazetevatan.com/ekonomi/tarlada-6-lira-makbuzda-28-lira-fiyat-oyununun-belgesi-ortaya-cikti-2407793)) | Ortağın fiyatı **sözleşmede taban fiyat** olarak yoksa model çöker |
| İşçi bulunamıyor, toplama maliyeti ürün değerine yaklaşıyor | 25 kg/gün, 1.500 TL yevmiye (Kestel) | Model 55 kg/gün varsayıyor. Bu iyimser |
| Ekşi meyve satılmıyor, söküp attı | Dikensiz böğürtlen söken üretici, yalnız reçellik gidiyor ([armuro forum](https://forum.armuro.com/tr/konular/forum/calilar/bogurtlen/)) | Çeşit (Loch Ness/Chester) ve tam olgun hasat şart. Erken toplama = 2. sınıf |
| Akar (böğürtlen akarı), geç don | Aynı forum | Mücadele programı + TARSİM; yine de verim kaybı yılları olacak |
| Fiyat yıldan yıla çakılıyor | Hal ortalaması 13 Haziran 2026'da 327 TL/kg ([haldefiyat](https://haldefiyat.com/urun/bogurtlen)). Eylül'de Bursa'da 60-70 TL/kg. Bazı ilanlarda 12 TL/kg ([tarimziraat](https://www.tarimziraat.com/fiyat/bogurtlen_fiyatlari-a97~3.html)) | Sezonun en kalabalık ayları (Tem-Ağu) en ucuz aylar. Bizim hasadın %65'i de bu aylara denk geliyor |
| Gübre fazlası meyveyi yumuşatıyor, raf ömrü düşüyor | Yetiştirici rehberleri | Fertigasyon EC izleme bu yüzden pakette |

Başarı hikâyeleri de var ([Hürriyet: "siparişlere yetişemiyor"](https://www.hurriyet.com.tr/ekonomi/izledigi-belgeselden-etkilenip-bogurtlen-ekti-simdi-siparislere-yetisemiyor-41225650), [Tarım TV: "fiyat üreticiyi sevindirdi"](https://www.tarimtv.gov.tr/tr/video-detay/bogurtlen-fiyati-ureticiyi-sev-4699)). Ama bunlar genellikle **1-5 da**, **doğrudan satış** yapan ve **kendi emeğini katan** küçük üreticiler. Haber olan, başaranlar. Söküp atanlar haber olmuyor. Bu bir hayatta kalan yanılgısıdır.

## 3. Rapordaki ROI nerede iyimser?

Aşağıdaki tabloda rapordan başlanıyor ve **her seferinde yalnız bir varsayım** gerçekçi değere çekiliyor:

| Tek başına geri çekilen varsayım | 2031 net | Fark | 5 yıl net | Geri dönüş |
|---|---:|---:|---:|---:|
| *Rapor (son hâl)* | 2,43 M TL | — | 7,42 M TL | 2,3 yıl |
| Tam verim 2,0 → 1,5 t/da, yavaş rampa | 1,69 M TL | −0,74 M TL | 4,10 M TL | 3,1 yıl |
| Ortak fiyatı 300 → 220 TL/kg | 1,70 M TL | −0,73 M TL | 4,86 M TL | 2,7 yıl |
| %10 satılamayan/çürüyen ürün | 2,11 M TL | −0,32 M TL | 6,32 M TL | 2,4 yıl |
| Kendin-topla 2 t → 0,8 t, 400 → 300 TL | 2,17 M TL | −0,25 M TL | 6,69 M TL | 2,4 yıl |
| Babanın emeği ücretli sayılırsa 240 bin TL/yıl | 2,19 M TL | −0,24 M TL | 6,22 M TL | 2,6 yıl |
| 2. sınıf %20 → %25, 65 → 45 TL | 2,19 M TL | −0,24 M TL | 6,60 M TL | 2,4 yıl |
| Sezonluk saha sorumlusu 200 bin TL/yıl | 2,23 M TL | −0,20 M TL | 6,62 M TL | 2,4 yıl |
| Hal fiyatı 199 → 120 TL/kg | 2,23 M TL | −0,20 M TL | 6,66 M TL | 2,4 yıl |
| Toplama hızı 55 → 40 kg/gün (paket) | 2,27 M TL | −0,16 M TL | 6,85 M TL | 2,4 yıl |
| Paketliye giden pay %80 → %60 | 2,32 M TL | −0,11 M TL | 7,03 M TL | 2,4 yıl |
| Arazi fırsat maliyeti (kira) 40 bin TL/yıl | 2,39 M TL | −0,04 M TL | 7,22 M TL | 2,3 yıl |

Tek tek bakınca hiçbiri ölümcül değil. En büyük iki etki **verim** ve **ortak fiyatı**, her biri yılda ~0,7 M TL. Sorun şu ki bunlar birbirinden bağımsız değil. Kötü yılda verim de düşer, fiyat da düşer, işçi de bulunmaz. Hepsi birlikte geri çekildiğinde toplam etki, tek tek etkilerin toplamından daha büyük oluyor.

**Rapordaki diğer iyimser noktalar:**

- **Hal fiyatı 199 TL/kg**, ağırlıklı olarak İstanbul/Ankara ve sezon başı kayıtlarından türetildi. Bursa'da Temmuz-Ağustos gerçek çıkış fiyatı bunun yarısı olabilir.
- **Ortak 300 TL/kg ve %80 paket payı** henüz konuşulmuş bir ortağa dayanmıyor. Bir zincir market tedarikçisi yeni ve küçük bir üreticiye genelde önce düşük hacim ve hale yakın fiyat verir.
- **Kendin-topla 2 t/yıl × 400 TL**: Bursa merkezine ~50-60 km uzaklıkta, hafta sonu, 60 günlük sezon. Bu hedef ayda ~650 ziyaretçi demek. İlk yıllarda 0,5-1 t daha olası.
- **Kayıpsız ürün**: model yağmurda çatlayan, kuşun yediği, çürüyen ya da satılamayan meyve için %0 varsayıyor. Sektörde %5-15 normal.
- **Babanın emeği, arazi kirası, sizin zamanınız bedava** varsayılıyor. Bu nakit açısından doğru ama "bu işin gerçek kârı" sorusunu cevaplamıyor.
- **Hastalıksız, donsuz 10 yıl** varsayılıyor. Böğürtlende 10 yılda 2-3 kötü yıl normal sayılır.
- **Arz etkisi yok sayılıyor**: bölgede birkaç kişi daha başlarsa (Kestel belediyesi fidan dağıtıyor) yerel fiyat düşer.

## 4. Üç senaryo yan yana

**Gerçekçi senaryo:** hal 120 TL/kg; ortak 220 TL/kg, paket payı %60; kendin-topla 0,8 t × 300 TL; tam verim 1,5 t/da (yavaş rampa); toplama hızı 40 kg/gün (paket) ve 55 kg/gün (dökme); %10 kayıp; 2. sınıf %25 × 45 TL; sezonluk saha sorumlusu 200 bin TL/yıl; arazi fırsat maliyeti 40 bin TL/yıl.

**Kötü senaryo:** hal 90 TL/kg; ortak 180 TL/kg ve yalnız %30 paket; tam verim 1,2 t/da; %15 kayıp; 2030'da don/hastalık yılı (verim −%60).

| | Rapor (son hâl) | Gerçekçi | Kötü |
|---|---:|---:|---:|
| Ortalama satış fiyatı 2031 (TL/kg, tüm kanallar) | 214 | 134 | 87 |
| Rekolte 2031 (ton) | 20,0 | 15,0 | 12,0 |
| Net kâr 2027 | −0,27 M TL | −0,43 M TL | −0,49 M TL |
| Net kâr 2028 | 0,83 M TL | −0,61 M TL | −0,86 M TL |
| Net kâr 2029 | 2,04 M TL | −0,29 M TL | −0,78 M TL |
| Net kâr 2030 | 2,39 M TL | −0,08 M TL | −0,90 M TL |
| Net kâr 2031 | 2,43 M TL | 0,00 M TL | −0,70 M TL |
| **5 yıl toplam net** | **7,42 M TL** | **−1,41 M TL** | **−3,73 M TL** |
| Cepten en yüksek (kümülatif nakit dibi) | 1,70 M TL | 2,38 M TL | 7,27 M TL |
| Geri dönüş | 2,3 yıl | dönmüyor | dönmüyor |
| 10 yıl IRR (reel) | %71,4 | −%15,2 | — |
| NPV @%12 reel | 8,90 M TL | −1,81 M TL | −4,72 M TL |

> **Gerçekçi senaryoda işletme nakit üretiyor** (2031 nakit ~190 bin TL). Ama amortisman, saha sorumlusu ve arazinin fırsat maliyeti düşülünce **kâr sıfırlanıyor**. Saha sorumlusu ve kira çıkarılırsa ("kendi arazim, babam bakıyor" bakışı) 2031 net ~240 bin TL, yani **aylık ~20 bin TL ek gelir**, ve geri dönüş ~8,3 yıl. Bu, raporda konuşulan "aylık 200 bin TL" hikâyesinden çok farklı.
>
> Kötü senaryodaki "cepten en yüksek" rakamı, zarara rağmen 10 yıl devam edildiği varsayımıyla hesaplandı. Gerçekte 2. veya 3. yılda durmak gerekir (bkz. §7). 2028 veya 2029 sonunda durulursa kötü senaryonun gerçek maliyeti **~1,9-2,6 M TL** olur (taşınabilir ekipmanın satışından gelecek ~0,2-0,3 M TL hariç).

## 5. Fiyat, her şeyi belirleyen değişken

Gerçekçi senaryonun maliyet ve verim yapısı sabit tutulup yalnızca ortalama satış fiyatı değiştirildiğinde:

| Tüm kanallar ortalama satış fiyatı (2031) | 2031 net kâr | 5 yıl toplam net | Geri dönüş |
|---|---:|---:|---:|
| 134 TL/kg (gerçekçi) | ~0 | −1,41 M TL | dönmüyor |
| 167 TL/kg | 0,44 M TL | −0,06 M TL | 6,3 yıl |
| 200 TL/kg | 0,88 M TL | 1,30 M TL | 4,4 yıl |
| 234 TL/kg | 1,33 M TL | 2,65 M TL | 3,7 yıl |

**Başabaş ~135 TL/kg.** Yılda ~1 M TL kâr için ~210 TL/kg gerekiyor. Yatırım kararı bu yüzden "toprak uygun mu?" sorusundan çok **"bana kilosu en az 200 TL'den, yılda en az 8-10 ton alacağını yazan biri var mı?"** sorusuna bağlı.

## 6. Monte Carlo: 5.000 olası 10 yıl

Varsayımlar:

- Fiyat seviyesi rapordan ~%25 düşük, ±%20 belirsizlik.
- Verim rapordaki değerin %65-105'i.
- Yıllık olay olasılıkları: don/dolu %10 (verim −%40); SWD/küf/kök çürüklüğü %15 (−%25); sıcak dalgası %15 (−%15); işçi bulunamaması %20 (−%10).
- Her yıl %12 ihtimalle ortak kaybı. O yıldan sonra paket payı %20'ye iniyor.
- %3-15 kayıp, saha sorumlusu dahil, kira hariç.

| Gösterge | Kötü %10 | Medyan | İyi %10 |
|---|---:|---:|---:|
| 2031 net kâr | −0,09 M TL | 0,49 M TL | 1,31 M TL |
| 5 yıl toplam net | −1,00 M TL | 0,82 M TL | 3,46 M TL |
| NPV @%12 reel (10 yıl) | −1,57 M TL | 0,62 M TL | 3,77 M TL |

- **10 yılda para kaybetme ihtimali (NPV < 0): %37**
- 10 yılda hiç geri dönmeme ihtimali: %20
- 4 yıl içinde geri dönme ihtimali: %32 (raporda 2,3 yıl görünüyordu)
- Geri dönenler içinde medyan geri dönüş: **4,3 yıl**
- 2031'de ≥ 1 M TL net kâr ihtimali: %20

Yani dürüst cevap şu: **beklenen sonuç pozitif ama mütevazı** (medyan 2031 net ~0,49 M TL/yıl). Yaklaşık üçte bir ihtimalle de para kaybediliyor. Rapordaki 2,4 M TL/yıl sonucuna simülasyonların yalnızca **%0,6**'sı ulaşıyor.

## 7. Kapsamlı risk matrisi

Olasılık ve etki 10 yıllık dönem için verilmiştir. Y = yüksek, O = orta, D = düşük.

| # | Risk | Olasılık | Etki | Erken sinyal | Önlem |
|---|---|:-:|:-:|---|---|
| **Pazar** | | | | | |
| 1 | Ortalama satış fiyatı < 150 TL/kg | Y | Y | Sezon başı tekliflerin hale endekslenmesi | Taban fiyatlı yazılı sözleşme; ilk yıl %50'den fazlasını hale bağlamamak |
| 2 | Ortak hacmi almıyor, geç ödüyor ya da çekiliyor | O | Y | Ödeme vadesinin uzaması, "bu hafta alamıyoruz" | En az 2 alıcı; 15 gün vade sınırı; dondurma/işleme yedek kanalı (2. sınıf için) |
| 3 | Bölgede arz artışı (belediye fidan dağıtımı, yeni bahçeler) | O | O | Kestel/Karacabey'de yeni dikimler | Erken/geç çeşitle sezonu kaydırmak; markalı doğrudan satış |
| 4 | Kendin-topla ziyaretçi gelmiyor | O | O | İlk sezon hafta sonu < 30 aile | Bursa merkez ilanı, okul/aile grupları; olmazsa paket kanalına kaydırmak |
| **Biyolojik / iklim** | | | | | |
| 5 | SWD (sirke sineği), gri küf | Y | O | Tuzak sayımı | 2-3 günde hasat; tuzak + izinli ilaç takvimi; raf ömrü için soğuk oda |
| 6 | Kök çürüklüğü (Phytophthora), ağır/su tutan toprak | O | Y | Sararma, kuruyan sürgünler | **Toprak analizi + profil çukuru + 40 cm sedde**: bu yüzden ilk adım |
| 7 | Geç don, dolu | O | Y | — | TARSİM; Chester gibi geç çiçekleyen çeşit |
| 8 | 38 °C üzeri sıcak dalgası, güneş yanığı | Y | O | Hava düğümü alarmı | %35 gölge filesi (pakette); sabah hasadı |
| 9 | Akar ve virüs (fidandan gelen) | O | O | Kırmızı kalan dane | Sertifikalı fidan; fidanlık garanti yazısı |
| **İşgücü / yönetim** | | | | | |
| 10 | Hasatta işçi bulunamaması, yevmiye artışı (TEKNOSAB etkisi) | Y | Y | 2027'de dayıbaşının "gelemeyiz" demesi | Sezonluk 2-3 kişilik sabit ekip; kendin-topla payı; yevmiye + kg primi |
| 11 | Uzaktan yönetim: siz Ankara'dasınız | Y | O | Sulama/ilaç takvimi kaçırma | Sezonluk saha sorumlusu (200 bin TL); sensör + kamera; haftalık rapor |
| 12 | Babaya bağımlılık (sağlık, yaş) | O | Y | — | Saha sorumlusu yedeği; işi yazılı prosedürlere dökmek |
| 13 | Tükenmişlik: ek iş olarak başlayıp tam zamanlı iş olması | Y | O | Haziran-Eylül her hafta sonu Bursa | Kapasiteyi 10 da ile sınırlamak; kendin-topla günlerini sabitlemek |
| **Operasyon** | | | | | |
| 14 | Soğuk oda arızası veya elektrik kesintisi (1 gece = 1 parti ürün) | O | O | Sıcaklık alarmı | Telegram alarmı (pakette); yedek klima, servis sözleşmesi |
| 15 | Hırsızlık, hayvan, kuş zararı | O | D | Kamera | Çit + kamera; kuş filesi gerekirse |
| 16 | Sulama suyu yetersiz, bor/tuz | D-O | Y | Su analizi | DSİ hidrant kapasitesi teyidi; su analizi ilk adımda |
| **Finansal / yasal** | | | | | |
| 17 | Bütçe aşımı (%15-30 normal) | Y | O | İlk teklifler | %8 yedek mevcut; %20'ye çıkarmak |
| 18 | Kur ve girdi enflasyonu (direk, tel, PE, gübre) | Y | O | — | Kritik malzemeyi erken almak |
| 19 | Vergi/SGK: gelir büyürse stopajın ötesine geçme, Bağ-Kur | O | D | Ortağın fatura istemesi | Muhasebeciyle baştan netleştirmek |
| 20 | Hazine faiz destekli kredi desteğinin 31.12.2026'da bitmesi | Y | D | — | Öz kaynakla gidiliyor. Etkisi düşük |
| **Arazi / bölge** | | | | | |
| 21 | TEKNOSAB ve imar: kamulaştırma, yol, toz, işçi rekabeti | O | O-Y | Plan değişikliği askısı | Taşınabilir yatırım payını yüksek tutmak (soğuk oda, sensör, saksılı fidan); TARSİM dışı |
| 22 | Komşu ilaçlaması (drift), toz | O | D | Yaprakta leke | Rüzgâr perdesi, komşuyla takvim |

**En tehlikeli üçlü:** fiyat (1), ortak (2) ve işçi (10). Üçü aynı yıl kötü giderse, ki bu birbirleriyle bağlantılı olabilir, işletme o yıl zarar yazar.

## 8. Ne yapmalı? Riski azaltan yol haritası

Bu tablo "yapma" demiyor. **"Fiyatı kanıtlamadan büyük para koyma"** diyor. Hızlı sonuç isteğinizle çelişmeyen bir sıralama:

1. **Ekim-Kasım 2026: doğrulama (~30-50 bin TL).**
   - Toprak ve su analizi + profil çukuru (planlandığı gibi).
   - Bursa'da **en az 3 aktif böğürtlen üreticisini** ziyaret etmek (Kestel, Gürsu, Karacabey) ve şunları sormak: geçen yıl kaça sattın, kime sattın, kaç kişiyle topladın, kg/gün kaç, kaç yılda bir kötü yıl yaşadın, bıraksan neden bırakırsın?
   - Ortak adayından **yazılı niyet mektubu**: kg fiyatı (taban), hacim, vade, kalite şartı. Hedef ≥ 220 TL/kg brüt ve ≥ 8 t/yıl.
2. **Karar kapısı (Aralık 2026):**
   - ≥ 200 TL/kg ortalama yazılı olarak teyit edildiyse → son hâldeki planla devam.
   - 150-200 TL/kg aralığındaysa → **3-4 da ile başla** (direk, tel ve damla ölçekle azalır). Fiyatı ilk sezonda kanıtla, sonra 10 da'ya genişlet.
   - < 150 TL/kg ise → böğürtlen ana gelir olarak **yapma**. Ya yalnız kendin-topla odaklı 2-3 da hobi/yan gelir bahçesi kur, ya da arazi için başka seçeneklere bak.
3. **İlk sezon (2027-2028):** kanal testi.
   - Bölümlü satış: aynı hafta ortak, hal ve kendin-topla fiyatlarını kaydet.
   - Gerçek kg/gün toplama hızını ölç.
   - Bu veriler gelince bu modeli yeniden çalıştırırız. Model hazır: `model_risk.py`.
4. **Durma kuralları:**
   - 2028 sonunda gerçekleşen ortalama fiyat < 140 TL/kg ise genişleme yok.
   - 2029 sonunda nakit hâlâ eksideyse taşınabilir yatırımlar (soğuk oda, teknoloji) satılır veya başka ürüne devredilir. Böylece kayıp, sökülemeyen tesis (arazi hazırlığı, fidan, tel, damla: ~1,05 M TL) ve o güne kadarki işletme zararlarıyla sınırlı kalır.

---

### Kaynaklar

- [Bursa Hakimiyet: Kestel'de ahududu ve böğürtlen üretimi Sırbistan modeliyle artırılacak](https://www.bursahakimiyet.com.tr/bursa/bursa-kestel-de-ahududu-ve-bogurtlen-uretimi-sirbistan-modeliyle-artirilacak-1563261): 25 kg/gün, 1.500 TL yevmiye, 150 TL çıkış, tüccar ve dış kaynak sorunu
- [Türk Haber: Ahududu Bursa'da yok olmak üzere](https://www.turkhaber.com/haber/ahududu-bursa-da-yok-olmak-uzere-4118617)
- [Uludağ Üniversitesi: Bursa'da üzümsü meyvelerin üretim ve pazarlamasının ekonomik analizi](https://acikerisim.uludag.edu.tr/items/83c730ce-852a-4cb8-9cbc-9f8073082824)
- [armuro forum: böğürtlen yetiştirici deneyimleri](https://forum.armuro.com/tr/konular/forum/calilar/bogurtlen/): ekşi meyve, akar, don
- [haldefiyat: böğürtlen hal fiyatı 2026](https://haldefiyat.com/urun/bogurtlen) · [tarimziraat: böğürtlen fiyatları](https://www.tarimziraat.com/fiyat/bogurtlen_fiyatlari-a97~3.html)
- [Gazete Vatan: Tarlada 6 lira, makbuzda 28 lira](https://www.gazetevatan.com/ekonomi/tarlada-6-lira-makbuzda-28-lira-fiyat-oyununun-belgesi-ortaya-cikti-2407793): genel aracı makası örneği, böğürtlene özgü değil
- [Hürriyet: Belgeselden etkilenip böğürtlen ekti, siparişlere yetişemiyor](https://www.hurriyet.com.tr/ekonomi/izledigi-belgeselden-etkilenip-bogurtlen-ekti-simdi-siparislere-yetisemiyor-41225650) · [Tarım TV: Böğürtlen fiyatı üreticiyi sevindirdi](https://www.tarimtv.gov.tr/tr/video-detay/bogurtlen-fiyati-ureticiyi-sev-4699)

*Not: Gerçekçi ve kötü senaryo parametreleri (fiyat, toplama hızı, kayıp oranı, olay olasılıkları) yayımlanmış tek bir veri setinden değil, yukarıdaki saha haberleri ve yetiştirici deneyimlerinden türetilmiş tahminlerdir. Üretici ziyaretleriyle teyit edilmeleri gerekir.*
