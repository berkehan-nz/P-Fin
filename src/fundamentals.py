"""Normalize edilmis finansal veri modeli.

``edgar_bulk`` (toplu ZIP) ve ``edgar_api`` (companyfacts) ayni ``Fundamentals``
nesnesini uretir; ``metrics.py`` ve ``scores.py`` yalnizca bu nesneyi bilir.
Boylece testler ag erisimi olmadan elle ``Fundamentals`` kurabilir.

BIRIM KURALI: tum parasal alanlar MILYON USD. EDGAR ham USD dondurdugu icin
yukleme katmani 1e6'ya boler. Hisse sayilari MILYON ADET.

Akis (flow) kalemleri donem boyunca birikir (hasilat, nakit akisi);
stok (stock) kalemleri donem sonu anlik degerdir (varliklar, borc).
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Iterable

from .util import add, num

# Akis kalemleri — TTM icin toplanir
FLOW_FIELDS = (
    "revenue", "cost_of_revenue", "gross_profit", "operating_income",
    "net_income", "pretax_income", "tax_expense", "interest_expense",
    "sga", "rnd", "dep_amort", "cfo", "capex", "cfi", "cff", "sbc",
    "stock_issued", "dividends_paid",
    "shares_diluted", "shares_basic",
)

# Bunlar da SURE bazli etiketlerdir (donem boyunca agirlikli ortalama) ama
# TOPLANMAZ — 12 aylik hisse sayisi diye 4 ceyregin toplamini vermek sacmadir.
# TTM'de son ceyregin degeri alinir.
AVERAGE_FIELDS = ("shares_diluted", "shares_basic")

# Stok kalemleri — donem sonu degeri alinir
STOCK_FIELDS = (
    "assets", "current_assets", "liabilities", "current_liabilities",
    "equity", "cash", "short_term_investments", "long_term_debt",
    "short_term_debt", "operating_lease_current", "operating_lease_noncurrent",
    "goodwill", "intangibles", "retained_earnings", "receivables",
    "inventory", "ppe_net", "deferred_revenue", "debt_due_2y",
)


@dataclass
class Period:
    """Tek bir mali donem (ceyrek veya yil).

    ``period_type`` 'Q' ise akis alanlari 3 aylik, 'FY' ise 12 aylik.
    """

    period_end: str                 # ISO tarih, orn. "2025-12-31"
    period_type: str = "Q"          # "Q" | "FY"
    fiscal_year: int | None = None
    fiscal_period: str | None = None  # Q1..Q4, FY

    # --- gelir tablosu (akis) ---
    revenue: float | None = None
    cost_of_revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None      # EBIT
    net_income: float | None = None
    pretax_income: float | None = None
    tax_expense: float | None = None
    interest_expense: float | None = None
    sga: float | None = None
    rnd: float | None = None
    dep_amort: float | None = None

    # --- nakit akisi (akis) ---
    cfo: float | None = None
    capex: float | None = None                 # pozitif sayi olarak saklanir
    cfi: float | None = None
    cff: float | None = None
    sbc: float | None = None
    stock_issued: float | None = None
    dividends_paid: float | None = None

    # --- bilanco (stok) ---
    assets: float | None = None
    current_assets: float | None = None
    liabilities: float | None = None
    current_liabilities: float | None = None
    equity: float | None = None
    cash: float | None = None
    short_term_investments: float | None = None
    long_term_debt: float | None = None
    short_term_debt: float | None = None
    operating_lease_current: float | None = None      # EV'ye DAHIL EDILMEZ
    operating_lease_noncurrent: float | None = None   # ayri kolonda tutulur
    goodwill: float | None = None
    intangibles: float | None = None
    retained_earnings: float | None = None
    receivables: float | None = None
    inventory: float | None = None
    ppe_net: float | None = None
    deferred_revenue: float | None = None
    debt_due_2y: float | None = None           # 2 yil icinde vadesi gelen borc

    # --- hisse ---
    shares_diluted: float | None = None
    shares_basic: float | None = None

    # --- turetilmis ---
    @property
    def computed_gross_profit(self) -> float | None:
        """Brut kar dogrudan raporlanmadiysa hasilat - satis maliyeti."""
        if self.gross_profit is not None:
            return self.gross_profit
        r, c = num(self.revenue), num(self.cost_of_revenue)
        if r is None or c is None:
            return None
        return r - c

    @property
    def financial_debt(self) -> float | None:
        """Finansal borc. Kiralama yukumlulukleri HARIC (sartname geregi)."""
        return add(self.long_term_debt, self.short_term_debt)

    @property
    def lease_liabilities(self) -> float | None:
        return add(self.operating_lease_current, self.operating_lease_noncurrent)

    @property
    def cash_and_investments(self) -> float | None:
        return add(self.cash, self.short_term_investments)

    @property
    def fcf(self) -> float | None:
        cfo, capex = num(self.cfo), num(self.capex)
        if cfo is None:
            return None
        return cfo - (capex or 0.0)

    @property
    def ebitda(self) -> float | None:
        return add(self.operating_income, self.dep_amort) \
            if num(self.operating_income) is not None else None

    @property
    def effective_tax_rate(self) -> float | None:
        """Efektif vergi orani. Vergi oncesi kar <= 0 ise anlamsiz."""
        pre = num(self.pretax_income)
        tax = num(self.tax_expense)
        if pre is None or tax is None or pre == 0:
            return None
        return tax / pre


@dataclass
class Fundamentals:
    """Bir sirketin tum donemsel verisi + kimlik bilgileri."""

    ticker: str
    cik: int | None = None
    name: str = ""
    sic: int | None = None
    exchange: str = ""
    fiscal_year_end: str | None = None
    ipo_date: str | None = None

    # Kronolojik sirali (eskiden yeniye)
    quarters: list[Period] = field(default_factory=list)
    annuals: list[Period] = field(default_factory=list)

    # Fiyat tarafi — prices.py doldurur
    price: float | None = None
    shares_outstanding: float | None = None      # milyon adet, dei etiketinden
    price_history: list[tuple[str, float]] = field(default_factory=list)
    avg_dollar_volume_30d: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None

    # Kaynak izlenebilirligi
    sources: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- erisim
    def sorted_quarters(self) -> list[Period]:
        return sorted(self.quarters, key=lambda p: p.period_end)

    def sorted_annuals(self) -> list[Period]:
        return sorted(self.annuals, key=lambda p: p.period_end)

    def latest_period(self) -> Period | None:
        """En guncel donem — bilanco (stok) kalemleri buradan okunur."""
        qs = self.sorted_quarters()
        if qs:
            return qs[-1]
        ann = self.sorted_annuals()
        return ann[-1] if ann else None

    def latest_annual(self, back: int = 0) -> Period | None:
        """``back``=0 en son yil, 1 bir onceki yil..."""
        ann = self.sorted_annuals()
        idx = len(ann) - 1 - back
        return ann[idx] if 0 <= idx < len(ann) else None

    # ------------------------------------------------------------------ TTM
    def has_quarterly(self, n: int = 4) -> bool:
        return len(self.quarters) >= n

    def ttm(self, field_name: str, *, offset: int = 0) -> float | None:
        """Son 12 ayin akis toplami.

        ``offset``=4 bir onceki 12 ayi verir (buyume karsilastirmasi icin).
        Ceyreklik veri yetersizse yillik veriye duser: offset 0 -> son FY,
        offset 4 -> bir onceki FY.
        """
        if field_name not in FLOW_FIELDS:
            raise KeyError(f"{field_name} bir akis kalemi degil")

        qs = self.sorted_quarters()
        need = 4 + offset
        if len(qs) >= need:
            window = qs[len(qs) - need: len(qs) - offset]
            vals = [num(getattr(p, field_name)) for p in window]
            # DORT CEYREGIN HEPSI dolu olmali. Eksigi atlayip toplamak
            # 2 ceyreklik rakami "12 aylik" diye sunar; buyume ve marj
            # hesaplarini sessizce cope cevirir.
            if all(v is not None for v in vals):
                if field_name in AVERAGE_FIELDS:
                    return vals[-1]
                return sum(vals)  # type: ignore[arg-type]

        # yillik yedek
        years_back = offset // 4
        ann = self.latest_annual(years_back)
        return num(getattr(ann, field_name)) if ann else None

    def ttm_period(self, *, offset: int = 0) -> Period:
        """Akis alanlari TTM toplami, stok alanlari donem sonu olan sanal donem.

        metrics/scores bu nesne uzerinden calisir; boylece ceyreklik ve yillik
        veri ayni sekilde islenir.
        """
        qs = self.sorted_quarters()
        need = 4 + offset

        annual_fallback = self.latest_annual(offset // 4)

        if len(qs) >= need:
            window = qs[len(qs) - need: len(qs) - offset]
            end_period = window[-1]
            p = Period(period_end=end_period.period_end, period_type="TTM",
                       fiscal_year=end_period.fiscal_year,
                       fiscal_period=end_period.fiscal_period)

            for f in FLOW_FIELDS:
                vals = [num(getattr(q, f)) for q in window]
                if all(v is not None for v in vals):
                    setattr(p, f, vals[-1] if f in AVERAGE_FIELDS else sum(vals))
                else:
                    # KISMI TOPLAM YAZILMAZ. Bir ceyrek bile eksikse o kalem
                    # icin yillik tabloya duselim; o da yoksa None kalsin.
                    # Eksik ceyrekleri atlayip toplamak, 2 ceyreklik rakami
                    # 12 aylik diye sunar ve tum buyume/marj hesabini bozar.
                    setattr(p, f, num(getattr(annual_fallback, f, None))
                            if annual_fallback is not None else None)

            for f in STOCK_FIELDS:
                setattr(p, f, getattr(end_period, f))
            return p

        if annual_fallback is not None:
            return annual_fallback
        return Period(period_end="", period_type="TTM")

    # ------------------------------------------------------------- seriler
    def quarter_series(self, field_name: str, n: int = 12) -> list[float | None]:
        """Son ``n`` ceyregin degeri (grafikler icin). Eksikler None kalir."""
        qs = self.sorted_quarters()[-n:]
        return [num(getattr(p, field_name)) for p in qs]

    def quarter_labels(self, n: int = 12) -> list[str]:
        qs = self.sorted_quarters()[-n:]
        return [p.fiscal_period and f"{p.fiscal_year}{p.fiscal_period}" or p.period_end
                for p in qs]

    def rolling_ttm_series(self, field_name: str, windows: int = 20) -> list[float | None]:
        """Kayan 12 aylik toplam serisi — 'kendi 5 yillik dagilimi' icin."""
        qs = self.sorted_quarters()
        out: list[float | None] = []
        for end in range(4, len(qs) + 1):
            window = qs[end - 4:end]
            vals = [num(getattr(p, field_name)) for p in window]
            out.append(sum(v for v in vals if v is not None)
                       if all(v is not None for v in vals) else None)
        return out[-windows:]

    def market_cap(self) -> float | None:
        """Fiyat x hisse sayisi (milyon USD). Ucuncu tarafa guvenilmez."""
        p, s = num(self.price), num(self.shares_outstanding)
        if p is None or s is None:
            return None
        return p * s


def period_from_dict(d: dict) -> Period:
    """Sozlukten Period kur; bilinmeyen anahtarlari sessizce atar."""
    known = {f.name for f in fields(Period)}
    return Period(**{k: v for k, v in d.items() if k in known})


def build_annual_fundamentals(ticker: str, years: Iterable[dict], **meta) -> Fundamentals:
    """Yillik sozluk listesinden Fundamentals kur (testler ve elle veri icin)."""
    f = Fundamentals(ticker=ticker, **meta)
    for y in years:
        p = period_from_dict({**y, "period_type": "FY"})
        f.annuals.append(p)
    return f
