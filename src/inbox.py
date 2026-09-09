"""claude_inbox/ sozlesmesi — baska bir ajanin yazacagi dosyanin kurallari.

TASARIM KARARI: inbox'a yazan ajan SAYISAL ALANLARA DOKUNAMAZ. Yalnizca
``story`` (analiz metni) ve ``decision`` (AL/BEKLE/ELE karari) alanlari
kabul edilir. Metrikler, fiyatlar ve puanlar veri hattinin sorumlulugunda
kalir; aksi halde elle yazilmis bir sayi hesaplanmis metriklerin uzerine
yazabilirdi ve hangisinin gercek oldugu belirsizlesirdi.

Bu dosya hem dogrulamayi hem de ajanin okuyacagi semayi tanimlar.
"""

from __future__ import annotations

ALLOWED_TOP_LEVEL = {"ticker", "story", "decision", "catalyst_score", "notes"}

STORY_FIELDS = {
    "business_model": str,
    "moat": str,
    "why_cheap_diagnosis": str,
    "why_cheap_rationale": str,
    "bull_case": list,
    "bear_case": list,
    "catalyst": dict,
    "thesis_breakers": list,
    "analyst_narrative": str,
    "news_summary": str,
    "claude_verdict": str,
    "author": str,
    "updated_at": str,
}

DECISION_FIELDS = {"action": str, "date": str, "rationale": str, "author": str}
VALID_ACTIONS = {"AL", "BEKLE", "ELE", ""}

MAX_TEXT_LEN = 4000
MAX_LIST_ITEMS = 12


def validate_file(payload, ticker: str) -> list[str]:
    """Dosyayi denetler; sorun listesi doner (bos liste = gecerli)."""
    problems: list[str] = []

    if not isinstance(payload, dict):
        return ["Dosya bir JSON nesnesi olmali"]

    unknown = set(payload) - ALLOWED_TOP_LEVEL
    if unknown:
        problems.append(
            f"Izin verilmeyen alan(lar): {', '.join(sorted(unknown))}. "
            f"Yalnizca {', '.join(sorted(ALLOWED_TOP_LEVEL))} yazilabilir — "
            f"metrikler ve fiyatlar veri hattinin sorumlulugundadir.")

    declared = str(payload.get("ticker", "")).upper()
    if declared and declared != ticker:
        problems.append(f"Dosya adi {ticker}.json ama icindeki ticker {declared}")

    story = payload.get("story")
    if story is not None:
        if not isinstance(story, dict):
            problems.append("story bir nesne olmali")
        else:
            for key, value in story.items():
                if key not in STORY_FIELDS:
                    problems.append(f"story.{key} bilinmeyen bir alan")
                    continue
                expected = STORY_FIELDS[key]
                if not isinstance(value, expected):
                    problems.append(
                        f"story.{key} {expected.__name__} olmali, "
                        f"{type(value).__name__} geldi")
                elif expected is str and len(value) > MAX_TEXT_LEN:
                    problems.append(f"story.{key} cok uzun (>{MAX_TEXT_LEN} karakter)")
                elif expected is list:
                    if len(value) > MAX_LIST_ITEMS:
                        problems.append(f"story.{key} en fazla {MAX_LIST_ITEMS} madde")
                    for item in value:
                        if not isinstance(item, (str, dict)):
                            problems.append(f"story.{key} maddeleri metin olmali")
                            break

    decision = payload.get("decision")
    if decision is not None:
        if not isinstance(decision, dict):
            problems.append("decision bir nesne olmali")
        else:
            for key, value in decision.items():
                if key not in DECISION_FIELDS:
                    problems.append(f"decision.{key} bilinmeyen bir alan")
                elif not isinstance(value, DECISION_FIELDS[key]):
                    problems.append(f"decision.{key} metin olmali")
            action = decision.get("action")
            if action is not None and action not in VALID_ACTIONS:
                problems.append(
                    f"decision.action '{action}' gecersiz — "
                    f"AL, BEKLE veya ELE olmali")

    score = payload.get("catalyst_score")
    if score is not None:
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            problems.append("catalyst_score sayi olmali")
        elif not 0 <= score <= 100:
            problems.append("catalyst_score 0-100 arasinda olmali")

    return problems


def template(ticker: str) -> dict:
    """Ajanin dolduracagi bos sema."""
    return {
        "ticker": ticker.upper(),
        "story": {
            "business_model": "",
            "moat": "",
            "why_cheap_diagnosis": "",
            "why_cheap_rationale": "",
            "bull_case": [],
            "bear_case": [],
            "catalyst": {"type": "", "expected_date": "", "confidence": ""},
            "thesis_breakers": [],
            "analyst_narrative": "",
            "news_summary": "",
            "claude_verdict": "",
            "author": "claude",
            "updated_at": "",
        },
        "decision": {"action": "", "date": "", "rationale": "", "author": "berke"},
    }
