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
