"""KADEMELI TARAMA KOSUSU — saatlik parti.

Tam evreni tek seferde taramak yerine her saat sabit sayida sirket isler.
Ilerleme ``data/scan_state.json`` icinde durur; kuyruk bitince Asama 3-4
calisir, kartlar uretilir ve yeni tur baslar.

    python -m src.run_scan                 # varsayilan parti (120 sirket)
    python -m src.run_scan --batch 60      # daha kucuk parti
    python -m src.run_scan --new-cycle     # kuyrugu bastan kur
    python -m src.run_scan --status        # yalnizca ilerlemeyi yazdir
"""

from __future__ import annotations

import argparse
import sys

from . import scan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kademeli evren taramasi (saatlik parti)")
    parser.add_argument("--batch", type=int, default=None,
                        help=f"Bu kosuda islenecek sirket sayisi (varsayilan {scan.DEFAULT_BATCH_SIZE})")
    parser.add_argument("--new-cycle", action="store_true",
                        help="Kuyrugu bastan kur (onceki turun hayatta kalanlari silinir)")
    parser.add_argument("--no-cards", action="store_true",
                        help="Tur sonunda kart uretme (yalnizca huni sonucu yaz)")
    parser.add_argument("--status", action="store_true",
                        help="Hicbir sey calistirma, yalnizca ilerlemeyi goster")
    args = parser.parse_args(argv)

    if args.status:
        state = scan.load_state()
        p = scan.progress(state)
        if not p["total"]:
            print("[tarama] Henuz tur baslatilmadi.")
            return 0
        print(f"[tarama] Tur {p['cycle']} · {p['done']}/{p['total']} (%{p['pct']}) · "
              f"hayatta kalan {p['survivors']} · kalan {p['remaining']}")
        print(f"          son parti: {state.get('last_batch_at') or '—'}")
        print(f"          son tur sonu: {state.get('last_finalized') or '—'}")
        if state.get("failed"):
            print(f"          yuklenemeyen (son {len(state['failed'])}): "
                  f"{', '.join(state['failed'][-10:])}")
        return 0

    state = scan.run(batch_size=args.batch, new_cycle=args.new_cycle,
                     build_cards=not args.no_cards)
    p = scan.progress(state)

    if p["total"] and p["done"] == 0 and state.get("last_finalized"):
        print(f"[tarama] Tur tamamlandi, yeni tur {p['cycle']} kuruldu.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
