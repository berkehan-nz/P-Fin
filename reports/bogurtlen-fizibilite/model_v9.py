"""v9 — Asgari başlangıç sermayesi: yalnız zorunlu yatırımlar (10 da, böğürtlen + kendin-topla).

    python reports/bogurtlen-fizibilite/model_v9.py

Gelir/gider varsayımları model_v8'den (Ekim 2026 TL fiyatları); yalnız yatırım listesi ve fidan seçeneği değişir.
"""
from __future__ import annotations

import model_v8 as v8

fmt, mtl, pct = v8.fmt, v8.mtl, v8.pct

# (faz, yıl sonu, grup, kalem, miktar, TL, ömür, neden zorunlu)
def minimal(hybrid=False):
    tc = 4530 if not hybrid else 3171
    pot = 0 if not hybrid else 1359
    it = [
        (0, 0, "Arazi", "Toprak analizi (2 derinlik)", "1 set", 5000, 10, "Gübre ve pH kararı için"),
        (0, 0, "Arazi", "Dip kazan + diskaro + sedde (lazer tesviye yok: arazi toplulaştırmada düzlenmiş, eğim %1-3)", "10 da", 60000, 10, "Killi toprakta kök boğulmasını önler"),
        (0, 0, "Arazi", "Yanmış çiftlik gübresi 3 t/da", "30 t", 60000, 10, "Organik madde; ilk yıl gelişimi"),
        (0, 0, "Arazi", "Siyah PE malç (sedde üstü; agrotekstil yerine)", "3.400 m²", 22000, 3, "Ot işçiliğini yarıya indirir"),
        (0, 0, "Fidan", "Doku kültürü fidan, viyolde + 2-3 ay saksıda alıştırma (kendin)", f"{fmt(tc)} ad × 46 TL", tc * 46, 10, "Sertifikalı, virüssüz"),
        (0, 0, "Fidan", "Dikim işçiliği", "", 25000, 10, ""),
        (0, 0, "Telli sistem", "Galvaniz direk 2,7 m, 8 m ara + baş direkleri", "483 ad × 350 TL", 483 * 350, 10, "Böğürtlen telsiz yetişmez"),
        (0, 0, "Telli sistem", "Galvaniz tel 3 kat + gergi/ankraj + montaj", "~10.000 m", 110000, 10, ""),
        (0, 0, "Sulama", "Damla: basınç ayarlı çift lateral + hidrant bağlantısı, disk filtre, ana hat", "10 da", 160000, 10, "Ana su kaynağı"),
        (0, 0, "Teknoloji", "Fertigasyon: venturi + 2 selenoid vana + ESP32 zamanlayıcı/röle (kendin) + el tipi EC/pH metre", "", 35000, 5, "Gübre dozu ve pH kontrolü"),
        (0, 0, "Teknoloji", "2 toprak nemi düğümü (ESP32 + kapasitif/RS485 prob, 30 ve 60 cm) + 4G modem", "2 düğüm", 20000, 5, "Sulama zamanı ve miktarı"),
        (0, 0, "Teknoloji", "Sıcaklık/nem + yaprak ıslaklığı sensörü (bir düğüme ek)", "1", 3000, 5, "İlaçlama zamanı, don alarmı"),
        (0, 0, "Diğer", "ÇKS kaydı, tarımsal yapı bildirimi, küçük giderler", "", 15000, 5, "Yasal"),
        (1, 1, "Soğuk zincir", "Kendi yapımın soğuk oda: 100 mm panel, kapı, inverter klima 24k BTU, termostat kontrolü, ön soğutma fanı", "~12 m³", 110000, 8, "Raf ömrü 2-3 günden 7-10 güne"),
        (1, 1, "Soğuk zincir", "Elektrik bağlantısı (monofaze) + pano", "", 40000, 15, "Soğuk oda için"),
        (1, 1, "Soğuk zincir", "Soğuk oda sıcaklık sensörü + 2 sıcaklık kayıt cihazı (logger)", "", 5000, 5, "Soğuk zincir kanıtı, alarm"),
        (1, 1, "Kalite", "%35 gölge filesi, yalnız güneye bakan ve Chester sıraları (%60)", "~3.000 m²", 126000, 7, "Temmuz-ağustos güneş yanığı"),
        (1, 1, "Hasat", "60 hasat kasası, 2 el arabası, terazi, etiket yazıcı", "", 34000, 5, "Hasat ve paketleme"),
        (1, 1, "Hasat", "Gıda işletme kaydı (İyi Tarım ortak isterse sonra)", "", 10000, 5, "Paketli satış için yasal"),
        (1, 1, "Kendin-topla", "Tabela, satış tezgâhı, gölgelik (WC kiralık)", "", 20000, 5, "Perakende kanal"),
    ]
    if hybrid:
        it.insert(5, (0, 0, "Fidan", "2 yaşlı tüplü fidan (hızlı blok, %30)", f"{fmt(pot)} ad × 150 TL", pot * 150, 10, "2028 verimini ~%25 artırır"))
    return it


DEFERRED = [
    ("Lazer tesviye", "~55.000 TL", "Arazi toplulaştırmada düzlenmiş; yalnız su göllenmesi görülürse"),
    ("Agrotekstil malç (PE yerine)", "+63.000 TL", "PE malç 3 yıl dayanır; yenilemede değerlendir"),
    ("Hat içi EC/pH probları + dozaj pompaları", "~90.000 TL", "El tipi ölçüm haftada 2 kez yeterli"),
    ("LoRaWAN gateway + 6-10 düğüm", "~100.000 TL", "10 da'da 2 düğüm 4G/Wi-Fi ile yeter"),
    ("Referans prob + profesyonel meteoroloji istasyonu", "~70.000 TL", "Ücretsiz hava tahmini API'si + yaprak ıslaklığı sensörü yeter"),
    ("Mini PC sunucu + UPS", "~20.000 TL", "Ücretsiz bulut (ör. Grafana Cloud free) veya evdeki bilgisayar"),
    ("PTZ AI / termal kamera", "~110.000 TL", "Hırsızlık yaşanırsa ucuz 4G kamera (~5.000 TL)"),
    ("NFC toplayıcı tartısı", "~20.000 TL", "İlk yıl defter/tablet; kişi bazlı ödeme gerekince"),
    ("İyi Tarım belgesi", "~40.000 TL", "Ortak veya market isterse"),
    ("Gölge filesinin kalan %40'ı", "~84.000 TL", "İlk sezonda güneş yanığı görülen sıralara"),
    ("2 yaşlı tüplü fidan (hibrit)", "~204.000 TL", "Daha hızlı nakit isteniyorsa (2028'de +2,4 t)"),
    ("Tünel, GES, şok dondurucu, pakethane", "–", "Ek gelir hedefi için gerekli değil (v8)"),
]


def with_items(items_fn, yields):
    """v8 plan B'yi verilen yatırım listesi ve verimle çalıştırır."""
    orig_items, orig_y = v8.items, list(v8.BB_YIELD)
    def it(p):
        out = [(ph, y, g, k, q, v * (1 + v8.CONT), life) for ph, y, g, k, q, v, life, _ in items_fn()]
        out += [(3, y, "Yenileme", k, "", v, life) for y, k, v, life in
                [(6, "Elektronik yenileme", 25000, 5), (4, "PE malç yenileme", 22000, 3), (7, "PE malç yenileme", 22000, 3),
                 (8, "Gölge filesi yenileme", 126000, 7)]]
        return out
    v8.items = it
    v8.BB_YIELD[:] = yields
    try:
        r = v8.run("B")
        s = v8.summary("B")
        s30 = v8.summary("B", price_mult=0.7)
        start = sum(i[5] for i in it(None) if i[0] <= 1)
        f0 = sum(i[5] for i in it(None) if i[0] == 0)
    finally:
        v8.items = orig_items
        v8.BB_YIELD[:] = orig_y
    return dict(r=r, s=s, s30=s30, start=start, f0=f0)


TC_ONLY = list(v8.TC)
HYB = [0.7 * a + 0.3 * b for a, b in zip(v8.TC, v8.POT)]


def md_capex(hybrid=False):
    it = minimal(hybrid)
    out = ["| Faz | Grup | Kalem | Miktar | TL | Neden zorunlu |", "|---|---|---|---|---:|---|"]
    for ph, y, g, k, q, v, life, why in it:
        out.append(f"| {ph} | {g} | {k} | {q} | {fmt(v*1.08)} | {why} |")
    for ph, lab in ((0, "Faz 0 — dikimden önce (Q4-2026 / Q1-2027)"), (1, "Faz 1 — 2027 içinde, ilk büyük hasattan önce")):
        s = sum(i[5] for i in it if i[0] == ph) * 1.08
        out.append(f"| | | **{lab}** | | **{fmt(s)}** | |")
    s = sum(i[5] for i in it) * 1.08
    out.append(f"| | | **TOPLAM BAŞLANGIÇ SERMAYESİ** | | **{fmt(s)}** | ≈ ${fmt(s/v8.FX)} |")
    out.append("\n*Tutarlar %8 beklenmeyen gider payı dahil.*")
    return "\n".join(out)


if __name__ == "__main__":
    print(md_capex()); print()
    for lab, hyb, y in (("Yalnız doku kültürü", False, TC_ONLY), ("Hibrit (%30 tüplü)", True, HYB)):
        o = with_items(lambda h=hyb: minimal(h), y)
        R = o["r"]["rows"]; c = v8.cum(o["r"]["flows"])
        print(lab, "start", round(o["start"]), "f0", round(o["f0"]), "peak", round(o["s"]["peak"]),
              "nets", [round(x["net"] / 1000) for x in R[:6]], "cum", [round(v / 1000) for v in c[:7]],
              "pb", round(o["s"]["pb"], 2), "irr", pct(o["s"]["irr"]), "| -30%:", round(o["s30"]["y5"]["net"]), round(o["s30"]["pb"] or 0, 1))
    b = v8.summary("B"); print("v8 B start", round(b["start"]), "peak", round(b["peak"]), "pb", round(b["pb"], 2))
