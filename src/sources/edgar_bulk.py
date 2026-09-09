"""SEC Financial Statement Data Sets — ceyreklik toplu XBRL verisi.

Neden toplu veri: companyfacts API'si sirket basina bir istek demek. 5000
sirketlik bir evren icin bu saniyede 10 istekle ~8 dakika ve 5000 buyuk JSON.
Toplu ZIP'ler ayni veriyi ceyrek basina tek indirmede verir, API limiti yoktur.

Akis:
  1. Son N ceyregin ZIP'ini indir (``sub.txt`` = basvurular, ``num.txt`` = sayilar)
  2. sqlite onbellegine yaz
  3. Sonraki kosularda yalnizca EKSIK ceyregi indir

sqlite semasi:
  filings(adsh, cik, name, sic, fy, fp, period, filed, form)
  facts(adsh, tag, ddate, qtrs, uom, value)
"""

from __future__ import annotations

import io
import sqlite3
import zipfile
from datetime import date

from .. import config
from ..util import sec_get

DB_PATH = config.CACHE_DIR / config.EDGAR["sqlite_cache"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS filings (
    adsh TEXT PRIMARY KEY,
    cik INTEGER, name TEXT, sic INTEGER,
    fy INTEGER, fp TEXT, period TEXT, filed TEXT, form TEXT
);
CREATE TABLE IF NOT EXISTS facts (
    adsh TEXT, tag TEXT, ddate TEXT, qtrs INTEGER, uom TEXT, value REAL
);
CREATE TABLE IF NOT EXISTS loaded_quarters (quarter TEXT PRIMARY KEY, loaded_at TEXT);
CREATE INDEX IF NOT EXISTS idx_filings_cik ON filings(cik);
CREATE INDEX IF NOT EXISTS idx_facts_adsh ON facts(adsh);
CREATE INDEX IF NOT EXISTS idx_facts_tag ON facts(tag);
"""

# num.txt icinden alinacak etiketler. Tamamini saklamak onbellegi 10 kat
# buyutur; huninin ihtiyaci olanlar yeterli.
WANTED_TAGS = {
    # gelir tablosu
    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
    "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfServices",
    "GrossProfit", "OperatingIncomeLoss", "NetIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    "IncomeTaxExpenseBenefit", "InterestExpense", "InterestExpenseNonoperating",
    "SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense",
    "ResearchAndDevelopmentExpense",
    "DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
    "DepreciationAndAmortization",
    # nakit akisi
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    "NetCashProvidedByUsedInInvestingActivities",
    "NetCashProvidedByUsedInFinancingActivities",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
    "ShareBasedCompensation", "AllocatedShareBasedCompensationExpense",
    "PaymentsOfDividendsCommonStock",
    # bilanco
    "Assets", "AssetsCurrent", "Liabilities", "LiabilitiesCurrent",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "CashAndCashEquivalentsAtCarryingValue", "ShortTermInvestments",
    "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
    "LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtCurrent",
    "ShortTermBorrowings", "DebtCurrent",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths",
    "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo",
    "OperatingLeaseLiabilityCurrent", "OperatingLeaseLiabilityNoncurrent",
    "Goodwill", "IntangibleAssetsNetExcludingGoodwill",
    "RetainedEarningsAccumulatedDeficit",
    "AccountsReceivableNetCurrent", "InventoryNet",
    "PropertyPlantAndEquipmentNet",
    "ContractWithCustomerLiabilityCurrent", "DeferredRevenueCurrent",
    # hisse
    "WeightedAverageNumberOfDilutedSharesOutstanding",
    "WeightedAverageNumberOfSharesOutstandingBasic",
    "EntityCommonStockSharesOutstanding",
    "CommonStockSharesOutstanding",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    return conn


def recent_quarters(n: int | None = None, today: date | None = None) -> list[str]:
    """Son ``n`` takvim ceyregi, yeniden eskiye ('2026q2' bicimi).

    SEC bir ceyregin veri setini ceyrek bittikten ~6 hafta sonra yayinlar,
    bu yuzden en guncel ceyregi atlayip bir onceki ceyrekten baslariz.
    """
    n = n or config.EDGAR["quarters_to_load"]
    today = today or date.today()
    y, q = today.year, (today.month - 1) // 3 + 1
    # yayin gecikmesi: bir ceyrek geri git
    q -= 1
    if q == 0:
        y, q = y - 1, 4
    out = []
    for _ in range(n):
        out.append(f"{y}q{q}")
        q -= 1
        if q == 0:
            y, q = y - 1, 4
    return out


def loaded_quarters() -> set[str]:
    with _connect() as conn:
        return {r[0] for r in conn.execute("SELECT quarter FROM loaded_quarters")}


def load_quarter(quarter: str, *, force: bool = False) -> int:
    """Bir ceyregin ZIP'ini indirip onbellege yazar. Kayit sayisini doner."""
    if not force and quarter in loaded_quarters():
        return 0

    year, q = quarter.split("q")
    url = config.EDGAR["bulk_zip_url"].format(year=year, quarter=q)
    print(f"  [edgar_bulk] {quarter} indiriliyor...")
    resp = sec_get(url, stream=True, timeout=180)
    blob = io.BytesIO(resp.content)

    rows = 0
    with zipfile.ZipFile(blob) as zf, _connect() as conn:
        # --- sub.txt: basvuru meta verisi ---
        subs: dict[str, tuple] = {}
        with zf.open("sub.txt") as fh:
            header = fh.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
            idx = {name: i for i, name in enumerate(header)}
            for raw in fh:
                parts = raw.decode("utf-8", "replace").rstrip("\n").split("\t")
                if len(parts) < len(header):
                    continue
                form = parts[idx["form"]]
                if form not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
                    continue
                adsh = parts[idx["adsh"]]
                subs[adsh] = (
                    adsh,
                    _int(parts[idx["cik"]]),
                    parts[idx["name"]],
                    _int(parts[idx["sic"]]),
                    _int(parts[idx["fy"]]),
                    parts[idx["fp"]],
                    parts[idx["period"]],
                    parts[idx["filed"]],
                    form,
                )
        conn.executemany(
            "INSERT OR REPLACE INTO filings VALUES (?,?,?,?,?,?,?,?,?)", subs.values()
        )

        # --- num.txt: sayisal gercekler ---
        batch: list[tuple] = []
        with zf.open("num.txt") as fh:
            header = fh.readline().decode("utf-8", "replace").rstrip("\n").split("\t")
            idx = {name: i for i, name in enumerate(header)}
            for raw in fh:
                parts = raw.decode("utf-8", "replace").rstrip("\n").split("\t")
                if len(parts) < len(header):
                    continue
                adsh = parts[idx["adsh"]]
                if adsh not in subs:
                    continue
                tag = parts[idx["tag"]]
                if tag not in WANTED_TAGS:
                    continue
                # coreg dolu satirlar bagli ortaklik detayidir, konsolide degil
                if parts[idx["coreg"]]:
                    continue
                val = _float(parts[idx["value"]])
                if val is None:
                    continue
                batch.append((adsh, tag, parts[idx["ddate"]],
                              _int(parts[idx["qtrs"]]), parts[idx["uom"]], val))
                if len(batch) >= 50_000:
                    conn.executemany("INSERT INTO facts VALUES (?,?,?,?,?,?)", batch)
                    rows += len(batch)
                    batch.clear()
        if batch:
            conn.executemany("INSERT INTO facts VALUES (?,?,?,?,?,?)", batch)
            rows += len(batch)

        conn.execute("INSERT OR REPLACE INTO loaded_quarters VALUES (?, ?)",
                     (quarter, date.today().isoformat()))
    print(f"  [edgar_bulk] {quarter}: {len(subs)} basvuru, {rows} deger")
    return rows


def sync(quarters: int | None = None, *, force: bool = False) -> list[str]:
    """Eksik ceyrekleri indirir. Zaten yuklu olanlara dokunmaz."""
    wanted = recent_quarters(quarters)
    have = loaded_quarters()
    new = []
    for q in wanted:
        if q in have and not force:
            continue
        try:
            load_quarter(q, force=force)
            new.append(q)
        except Exception as exc:  # noqa: BLE001
            print(f"  [uyari] {q} yuklenemedi: {exc}")
    return new


def prune(keep: int | None = None) -> int:
    """Eski ceyrekleri onbellekten siler; dosya suresiz buyumesin."""
    keep_set = set(recent_quarters(keep))
    with _connect() as conn:
        stale = [r[0] for r in conn.execute("SELECT quarter FROM loaded_quarters")
                 if r[0] not in keep_set]
        if not stale:
            return 0
        conn.executemany("DELETE FROM loaded_quarters WHERE quarter = ?",
                         [(q,) for q in stale])
        conn.execute("VACUUM")
    return len(stale)


def companies() -> list[dict]:
    """Onbellekteki tum sirketler (evren taramasi icin)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT cik, name, sic, MAX(filed) FROM filings "
            "WHERE cik IS NOT NULL GROUP BY cik"
        ).fetchall()
    return [{"cik": r[0], "name": r[1], "sic": r[2], "last_filed": r[3]} for r in rows]


def filings_for(cik: int) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT adsh, name, sic, fy, fp, period, filed, form FROM filings "
            "WHERE cik = ? ORDER BY period", (cik,)
        ).fetchall()
    keys = ("adsh", "name", "sic", "fy", "fp", "period", "filed", "form")
    return [dict(zip(keys, r)) for r in rows]


def facts_for(adsh_list: list[str]) -> list[dict]:
    if not adsh_list:
        return []
    placeholders = ",".join("?" * len(adsh_list))
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT adsh, tag, ddate, qtrs, uom, value FROM facts "
            f"WHERE adsh IN ({placeholders})", adsh_list
        ).fetchall()
    keys = ("adsh", "tag", "ddate", "qtrs", "uom", "value")
    return [dict(zip(keys, r)) for r in rows]


def cache_stats() -> dict:
    if not DB_PATH.exists():
        return {"exists": False}
    with _connect() as conn:
        return {
            "exists": True,
            "size_mb": round(DB_PATH.stat().st_size / 1e6, 1),
            "quarters": sorted(r[0] for r in conn.execute("SELECT quarter FROM loaded_quarters")),
            "filings": conn.execute("SELECT COUNT(*) FROM filings").fetchone()[0],
            "facts": conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0],
        }


def _int(x) -> int | None:
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def _float(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if v != v else v
