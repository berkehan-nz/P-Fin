"""Test sirketleri icin elle kurulmus mali tablolar (milyon USD).

NOT — VERININ KAYNAGI: bu rakamlar sirketlerin FY2025 kamuya acik mali
tablolarindan derlenmis YAKLASIK degerlerdir ve sartnamede verilen hedef
oranlari (EV/EBIT, FCF verimi, F-Score, Z'', Beneish M) uretecek sekilde
tutarli hale getirilmistir. Amac hesap MOTORUNU dogrulamaktir, EDGAR
verisinin kendisini degil.

EDGAR'dan gelen gercek rakamlarla dogrulama ``tests/test_live_edgar.py``
icindeki ``network`` isaretli testlerle yapilir; onlar yalnizca ag erisimi
oldugunda (GitHub Actions) calisir.
"""

from src.fundamentals import build_annual_fundamentals

# --------------------------------------------------------------------------
# DBX — Dropbox. Karli, nakit ureten, ozkaynagi geri alimlarla NEGATIF.
# Beklenen: EV/EBIT ~14.7, FCF verimi ~%9.1, F=6, Beneish ~-3.1,
#           roic_method="b", z_unreliable=True
# --------------------------------------------------------------------------
DBX_FY2024 = {
    "period_end": "2024-12-31", "fiscal_year": 2024, "fiscal_period": "FY",
    "revenue": 2550, "cost_of_revenue": 460, "gross_profit": 2090,
    "operating_income": 600, "net_income": 450,
    "pretax_income": 560, "tax_expense": 110, "interest_expense": 25,
    "sga": 820, "rnd": 670, "dep_amort": 210,
    "cfo": 850, "capex": 30, "cfi": -150, "sbc": 340,
    "assets": 3050, "current_assets": 1550, "liabilities": 3330,
    "current_liabilities": 1450, "equity": -280,
    "cash": 800, "short_term_investments": 400,
    "long_term_debt": 1390, "short_term_debt": 0,
    "operating_lease_current": 90, "operating_lease_noncurrent": 320,
    "goodwill": 380, "retained_earnings": -1000,
    "receivables": 280, "ppe_net": 360, "debt_due_2y": 0,
    "shares_diluted": 330, "shares_basic": 325,
}

DBX_FY2025 = {
    "period_end": "2025-12-31", "fiscal_year": 2025, "fiscal_period": "FY",
    "revenue": 2470, "cost_of_revenue": 420, "gross_profit": 2050,
    "operating_income": 640, "net_income": 490,
    "pretax_income": 610, "tax_expense": 120, "interest_expense": 30,
    "sga": 780, "rnd": 630, "dep_amort": 200,
    "cfo": 880, "capex": 24, "cfi": -100, "sbc": 320,
    "assets": 3100, "current_assets": 1400, "liabilities": 3450,
    "current_liabilities": 1600, "equity": -350,
    "cash": 700, "short_term_investments": 472,
    "long_term_debt": 1980, "short_term_debt": 0,
    "operating_lease_current": 85, "operating_lease_noncurrent": 300,
    "goodwill": 380, "retained_earnings": -1200,
    "receivables": 265, "ppe_net": 320, "debt_due_2y": 0,
    "shares_diluted": 300, "shares_basic": 296,
}


def dbx():
    f = build_annual_fundamentals(
        "DBX", [DBX_FY2024, DBX_FY2025],
        name="Dropbox, Inc.", cik=1467623, sic=7372, exchange="Nasdaq",
    )
    f.price = 28.67
    f.shares_outstanding = 300.0
    return f


# --------------------------------------------------------------------------
# LSCC — Lattice Semiconductor. Kaliteli ama PAHALI; borcsuz, saglam bilanco.
# Beklenen: EV/Hasilat ~30, FCF verimi ~%0.8, F=5, Z'' ~10.4
# --------------------------------------------------------------------------
LSCC_FY2024 = {
    "period_end": "2024-12-31", "fiscal_year": 2024, "fiscal_period": "FY",
    "revenue": 509, "cost_of_revenue": 156, "gross_profit": 353,
    "operating_income": 45, "net_income": 40,
    "pretax_income": 47, "tax_expense": 7, "interest_expense": 2,
    "sga": 130, "rnd": 170, "dep_amort": 38,
    "cfo": 140, "capex": 30, "cfi": -45, "sbc": 60,
    "assets": 940, "current_assets": 570, "liabilities": 250,
    "current_liabilities": 170, "equity": 690,
    "cash": 120, "short_term_investments": 0,
    "long_term_debt": 0, "short_term_debt": 0,
    "operating_lease_current": 8, "operating_lease_noncurrent": 25,
    "goodwill": 285, "retained_earnings": 245,
    "receivables": 60, "ppe_net": 95, "debt_due_2y": 0,
    "shares_diluted": 139, "shares_basic": 137,
}

LSCC_FY2025 = {
    "period_end": "2025-12-31", "fiscal_year": 2025, "fiscal_period": "FY",
    "revenue": 520, "cost_of_revenue": 162, "gross_profit": 358,
    "operating_income": 60, "net_income": 55,
    "pretax_income": 64, "tax_expense": 9, "interest_expense": 2,
    "sga": 132, "rnd": 166, "dep_amort": 36,
    "cfo": 150, "capex": 25, "cfi": -40, "sbc": 62,
    "assets": 1000, "current_assets": 620, "liabilities": 265,
    "current_liabilities": 180, "equity": 735,
    "cash": 130, "short_term_investments": 0,
    "long_term_debt": 0, "short_term_debt": 0,
    "operating_lease_current": 8, "operating_lease_noncurrent": 22,
    "goodwill": 285, "retained_earnings": 290,
    "receivables": 62, "ppe_net": 92, "debt_due_2y": 0,
    "shares_diluted": 140, "shares_basic": 138,
}


def lscc():
    f = build_annual_fundamentals(
        "LSCC", [LSCC_FY2024, LSCC_FY2025],
        name="Lattice Semiconductor Corp.", cik=855658, sic=3674, exchange="Nasdaq",
    )
    f.price = 112.36
    f.shares_outstanding = 140.0
    return f


# --------------------------------------------------------------------------
# KVYO — Klaviyo. Hizli buyuyen, EBIT NEGATIF ama FCF pozitif -> Kol B.
# Beklenen: EBIT<0, EV/Brut kar ~5.0, 40 Kurali ~48.5, F=4
# --------------------------------------------------------------------------
KVYO_FY2024 = {
    "period_end": "2024-12-31", "fiscal_year": 2024, "fiscal_period": "FY",
    "revenue": 938, "cost_of_revenue": 208, "gross_profit": 730,
    "operating_income": -155, "net_income": -130,
    "pretax_income": -140, "tax_expense": -10, "interest_expense": 0,
    "sga": 560, "rnd": 260, "dep_amort": 25,
    "cfo": 175, "capex": 20, "cfi": -60, "sbc": 300,
    "assets": 1500, "current_assets": 1100, "liabilities": 520,
    "current_liabilities": 430, "equity": 980,
    "cash": 780, "short_term_investments": 0,
    "long_term_debt": 0, "short_term_debt": 0,
    "operating_lease_current": 12, "operating_lease_noncurrent": 45,
    "goodwill": 30, "retained_earnings": -520,
    "receivables": 190, "ppe_net": 40, "debt_due_2y": 0,
    "shares_diluted": 262, "shares_basic": 255,
}

KVYO_FY2025 = {
    "period_end": "2025-12-31", "fiscal_year": 2025, "fiscal_period": "FY",
    "revenue": 1220, "cost_of_revenue": 280, "gross_profit": 940,
    "operating_income": -90, "net_income": -55,
    "pretax_income": -70, "tax_expense": -15, "interest_expense": 0,
    "sga": 700, "rnd": 330, "dep_amort": 30,
    "cfo": 250, "capex": 25, "cfi": -80, "sbc": 340,
    "assets": 2000, "current_assets": 1300, "liabilities": 650,
    "current_liabilities": 500, "equity": 1350,
    "cash": 900, "short_term_investments": 0,
    "long_term_debt": 0, "short_term_debt": 0,
    "operating_lease_current": 14, "operating_lease_noncurrent": 50,
    "goodwill": 30, "retained_earnings": -575,
    "receivables": 250, "ppe_net": 45, "debt_due_2y": 0,
    "shares_diluted": 280, "shares_basic": 272,
}


def kvyo():
    f = build_annual_fundamentals(
        "KVYO", [KVYO_FY2024, KVYO_FY2025],
        name="Klaviyo, Inc.", cik=1835830, sic=7372, exchange="NYSE",
    )
    f.price = 20.00
    f.shares_outstanding = 280.0
    return f


ALL = {"DBX": dbx, "LSCC": lscc, "KVYO": kvyo}
