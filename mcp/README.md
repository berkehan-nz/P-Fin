# P-Fin MCP — Claude Chat'ten sistemi yonetme

Claude Chat'in bu depoyu okumasini ve **PR uzerinden** degistirmesini saglayan
uzak MCP sunucusu. Cloudflare Workers'ta calisir, GitHub ile kimlik dogrular.

## Neden bu tasarim

Sunucu **hicbir veri saklamaz.** Okumalar `main` dalindan, yazmalar tek bir
calisma dalina gider ve oradan **tek bir PR** acilir. Boylece:

- Deponun "tum durum dosyada tutulur" ilkesi bozulmaz.
- Her degisiklik bir commit oldugu icin denetim izi kendiliginden olusur.
- Sen tek bir yerden — PR'in *Files changed* sekmesinden — hepsini gorursun.
- PR'da CI calisir; sema **gercek Python koduyla** (`src/inbox.py`,
  `src/overrides.py`) dogrulanir. TypeScript tarafi yalnizca on eleme yapar.

Dogrudan `main`'e yazilmaz. Bir analiz metni yanlis olabilir; geri almanin yolu
"revert commit" degil, "PR'i kapat" olmali.

## Sayisal alan sinirI

Chat'teki ajan **metrik, fiyat veya puan yazamaz** — deponun ana sozlesmesi
neyse o gecerli. Veride gercekten hata varsa `report_data_issue` kullanilir:
duzeltme metrige degil **ham donem verisine** yazilir (`data/overrides.json`),
**kaynak zorunludur**, ve duzeltilen degerden marjlar, puanlar ve huni karari
kendiliginden yeniden hesaplanir. Kartta "ELLE DUZELTME" uyarisi ve kaynak
gorunur.

> Veri duzeltmeleri PR birlestikten sonra **bir sonraki veri hatti kosusunda**
> (Scan / Bootstrap) etkili olur — inbox analizleri gibi 30 saniyede degil.
> Hemen gormek icin: Actions -> Bootstrap -> ilgili sembol.

## Araclar

| Arac | Ne yapar |
|---|---|
| `list_candidates` | Adaylari puana gore siralar; "analiz gerekenler" filtresi var |
| `get_card` | Kartin bir bolumunu okur (ozet / metrikler / analiz / skor detay) |
| `list_pending_changes` | PR'a girecek bekleyen degisiklikler |
| `write_analysis` | Analiz metnini `claude_inbox/<T>.json`'a yazar |
| `set_decision` | AL / BEKLE / ELE + gerekce |
| `set_catalyst_score` | Katalizor puani (toplam puanin %25'i, otomatik hesaplanmaz) |
| `add_to_watchlist` | Izleme listesine ekler |
| `report_data_issue` | Ham veri duzeltmesi — kaynak zorunlu |
| `submit_for_review` | Biriken her seyi **tek** PR olarak sunar |
| `whoami` | Oturum ve yetki |

`ALLOWED_LOGIN` disindaki GitHub kullanicilari yalnizca okuma araclarini gorur.

---

## Kurulum

### 1. GitHub OAuth App

<https://github.com/settings/developers> -> **New OAuth App**

- Homepage URL: `https://pfin-mcp.<hesabin>.workers.dev`
- Authorization callback URL: `https://pfin-mcp.<hesabin>.workers.dev/callback`

Client ID'yi not al, **Generate a new client secret** ile bir secret uret.

> Worker'i henuz dagitmadigin icin tam adresi bilmiyorsun. Once adim 3'u
> calistirip adresi ogren, sonra OAuth App'i duzenleyip callback'i yaz.
> Yerel gelistirme icin ayrica ikinci bir App ac; callback'i
> `http://localhost:8788/callback` yap.

### 2. KV alani

```bash
cd mcp
npm install
npx wrangler kv namespace create "OAUTH_KV"
```

Ciktidaki `id` degerini `wrangler.jsonc` icindeki `<Add-KV-ID>` yerine yaz.

### 3. Dagit

```bash
npx wrangler deploy
```

### 4. Gizli degerler

```bash
npx wrangler secret put GITHUB_CLIENT_ID
npx wrangler secret put GITHUB_CLIENT_SECRET
npx wrangler secret put COOKIE_ENCRYPTION_KEY   # openssl rand -hex 32
```

`GITHUB_REPO` ve `ALLOWED_LOGIN` gizli degil; `wrangler.jsonc` icinde duruyor.

### 5. Claude'a bagla

claude.ai -> **Settings -> Connectors -> Add custom connector**

```
https://pfin-mcp.<hesabin>.workers.dev/mcp
```

GitHub ile oturum ac, izin ver. Sohbette **+** ile bagliyi ac.

---

## Yerel calistirma

```bash
cp .dev.vars.example .dev.vars     # ikinci OAuth App'in degerlerini gir
npm run dev                        # http://localhost:8788/mcp
```

## Gunluk akis

1. Chat'te: *"En dusuk analiz kapsamali uc sirketi incele ve not yaz."*
2. Ajan `list_candidates` / `get_card` ile okur, `write_analysis` ile yazar.
3. `submit_for_review` tek PR acar.
4. Sen PR'i okursun, birlestirirsin.
5. **Merge** is akisi kartlari gunceller, GitHub Pages yayinlar (~1 dk).


## Jeton, yetki ve okuma yolu

**Okumalar jeton istemez.** Depo public; `list_candidates`, `get_card` gibi
araclar `raw.githubusercontent.com` uzerinden okur. Bunun sebebi somut: GitHub
bir OAuth uygulamasi icin kullanici basina jeton sayisi asilinca **en eskisini
iptal eder**. Baglayici birden fazla oturum actiginda eski jeton olur ve
eskiden TUM araclar (okumalar dahil) 401 veriyordu. Artik jeton yalnizca
YAZMA icin gerekli.

Calisma dalindan yapilan okumalar API'den gider: raw CDN birkac dakika
onbelleklidir ve bayat icerik, ajanin kendi yazdigini ezmesine yol acar.

**`whoami` gercek dogrulama yapar.** `GET /user` + depo izin kontrolu calistirir.
Onceki surum hicbir cagri yapmadan "yazma yetkin var" diyordu; jeton iptal
edilmisken bile. Simdi jeton olmusse acikca soyler ve ne yapilacagini yazar.

**Jeton gecersizse:** claude.ai > Settings > Connectors > P-Fin baglayicisini
kaldirip yeniden bagla.

## Dagitim — otomatik

`mcp/` altinda bir degisiklik main'e girince **MCP dagitimi** is akisi
(`.github/workflows/mcp-deploy.yml`) sunucuyu kendiliginden gunceller.
Tip hatasi olan kod canliya gitmez.

Eskiden sunucu yalnizca bir bilgisayardan terminalle (`npm run deploy`)
dagitilabiliyordu. Kod depoda guncellense bile canlidaki surum eski
kaliyordu ve bunu kimse fark etmiyordu.

### Tek seferlik kurulum (3 adim, ~5 dakika)

**1. Cloudflare'den anahtar al**

- https://dash.cloudflare.com adresine gir
- Sag ustte profil simgesi > **My Profile**
- Sol menude **API Tokens** > **Create Token**
- **Edit Cloudflare Workers** satirinda **Use template**
- *Account Resources*: kendi hesabini sec. *Zone Resources*: **All zones**
- **Continue to summary** > **Create Token**
- Cikan uzun metni KOPYALA. **Bir daha gosterilmez.**

**2. GitHub'a kaydet**

- Depo > **Settings** > **Secrets and variables** > **Actions**
- **New repository secret**
- Name: `CLOUDFLARE_API_TOKEN`
- Secret: kopyaladigin metni yapistir > **Add secret**

(SEC_USER_AGENT, FINNHUB_API_KEY ve FRED_API_KEY'i de ayni yerden
eklemistin.)

**3. Ilk dagitimi baslat**

- Depo > **Actions** > sol listede **MCP dagitimi** > **Run workflow**
- 1-2 dakika icinde yesil tik gormelisin

**Dogrulama:** Claude sohbetinde "whoami calistir" de. Cikti
`Jeton: GECERLI (dogrulandi)` ile baslamali.

Kirmizi carpi cikarsa ve hata "CLOUDFLARE_ACCOUNT_ID" diyorsa, birden
fazla Cloudflare hesabin var demektir: Cloudflare ana sayfasinda sag
taraftaki **Account ID**'yi kopyalayip ayni yoldan `CLOUDFLARE_ACCOUNT_ID`
adiyla ikinci bir secret olarak ekle.

### Elle dagitim (gelistirici icin)

```bash
cd mcp && npm ci && npm run type-check && npm run deploy
```


## Araclar

### Okuma (jeton gerektirmez)

| Arac | Ne cevaplar |
|---|---|
| `list_candidates` | Puana gore siralanmis adaylar |
| `get_card` | Tek sirketin tam karti |
| `list_cards(filter)` | Kirici tetiklenmis / not bekleyen / dusuk kapsamali / veri sorunlu / karar yok |
| `get_portfolio` | Deger, K/Z, dilim agirliklari ve sapmalari, uyarilar, TL basa bas |
| `get_weekly_review` | Cuma raporu — kac madde eylem gerektiriyor |
| `get_funnel_status` | Tarama nerede, ELENDI / VERI_YOK ayrimi, yeniden deneme kuyrugu |
| `get_pulse` | Endeksler, VIX, risk notu, yaklasan kritik tarihler |
| `list_pending_changes` | Birlestirilmemis degisiklikler + bayat dal uyarisi |
| `whoami` | GERCEK dogrulama (GET /user + depo izni) |

Her arac YALNIZCA kendi sorusunun cevabini dondurur. Ham dosyalar 100 KB'i
asiyor ve cogu alan sorulan seyle ilgisiz; ajanin indirip ayiklamasi
gereksiz.

### Yazma (PR akisi)

| Arac | Not |
|---|---|
| `write_analysis` | Analiz metni. SAYISAL ALAN YAZAMAZ |
| `set_decision` | AL / BEKLE / ELE + gerekce |
| `set_catalyst_score` | Katalizor puani (elle girilen tek puan) |
| `add_to_watchlist` | Izleme listesi |
| `record_position` | STOCK / ETF / **TL_DEPOSIT**, dilim, kademeli alim |
| `close_position` | **Gerekce zorunlu**: tez_kirici / hedef_fiyat / yeniden_dengeleme / nakit_ihtiyaci / tez_degisti |
| `set_thesis_breakers` | **Yapilandirilmis** kirici (metric/op/value/consecutive_quarters) |
| `set_target_price` | Hedef + gerekce (zorunlu) |
| `report_data_issue` | HAM donem verisi duzeltmesi, kaynak zorunlu |
| `submit_for_review` | Tek PR acar |
| `trigger_bootstrap` | Tek sembol icin karti yeniden uretir — **PR akisi disinda** |

Iki tasarim notu:

**Sayisal alan yasagi metriklere ve puanlara aittir**, pozisyon verisine
degil. Bir kiricinin esik degeri bir TERCIHTIR, olculen bir buyukluk
degil; hisse adedi ve mevduat anaparasi da oyle. Yasagin amaci, hesaplanan
bir sayinin elle ezilip girdiyle ciktinin celismesini onlemek.

**`set_thesis_breakers` yapilandirilmis bicim ister** cunku serbest metin
bir kirici ("rakip pazar payi alirsa") makine tarafindan degerlendirilemez
ve o yuzden hicbir zaman tetiklenmez. Yapilandirilmis bicimde gunluk kosu
kart verisine bakip kendiliginden karar verir. Seri yoksa TETIKLEMEZ ve
"veri_yok" der — yari bilgiyle alarm calmak, bir sure sonra tum alarmlarin
gormezden gelinmesini ogretir.

**`trigger_bootstrap` PR akisinin disindadir** ve bunu ciktisinda acikca
soyler: is akisi biter bitmez kart main'e yazilir. Veri duzeltmesi
birlestirildikten sonra ya da bilanco sonrasi kullanilir.
