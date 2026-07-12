/**
 * Kişisel Finans Ajanı — panel (§3.7).
 * state.json ile AYNI şemayı okur (memory/schema.py sözleşmesi).
 * Gösterir: açık pozisyonlar + tez + durum, ajan günlüğü, haftalık performans
 * (XU100/TÜFE kıyas çizgileriyle), gerçekleşen P&L, bütçe.
 *
 * Kullanım (kendi React uygulamanızda):
 *   import FinansPanel from "./finans-ajani-panel.jsx";
 *   <FinansPanel src="/state.json" />         // veya <FinansPanel state={stateObj} />
 */
import React, { useEffect, useState } from "react";

const fmt = (v, d = 2) =>
  v === null || v === undefined || Number.isNaN(v)
    ? "—"
    : Number(v).toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d });

const pct = (v) => (v === null || v === undefined ? "—" : `%${fmt(v)}`);

function useStateJson(src, injected) {
  const [state, setState] = useState(injected || null);
  const [error, setError] = useState(null);
  useEffect(() => {
    if (injected) { setState(injected); return; }
    fetch(src, { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error(`state.json okunamadı (${r.status})`); return r.json(); })
      .then(setState)
      .catch((e) => setError(e.message));
  }, [src, injected]);
  return { state, error };
}

function portfolioValue(s) {
  const pos = (s.positions || []).filter((p) => p.status === "open");
  const posVal = pos.reduce((a, p) => a + (p.current_price ?? p.entry_price) * p.shares, 0);
  return (s.cash_try || 0) + posVal;
}

function benchmark(s) {
  const perf = s.performance || [];
  if (perf.length < 2) return null;
  const first = perf[0], last = perf[perf.length - 1];
  const pr = first.portfolio_value_try ? (last.portfolio_value_try / first.portfolio_value_try - 1) * 100 : null;
  const xr = first.xu100 && last.xu100 ? (last.xu100 / first.xu100 - 1) * 100 : null;
  return { pr, xr, rel: pr !== null && xr !== null ? pr - xr : null, tufe: last.tufe_yoy };
}

const card = { background: "#fff", border: "1px solid #e6e6ef", borderRadius: 12, padding: 16, marginBottom: 16 };
const chip = (bg, fg) => ({ background: bg, color: fg, borderRadius: 6, padding: "2px 8px", fontSize: 12, fontWeight: 600 });

export default function FinansPanel({ src = "/state.json", state: injected }) {
  const { state, error } = useStateJson(src, injected);
  if (error) return <div style={{ color: "#b00", padding: 24 }}>Hata: {error}</div>;
  if (!state) return <div style={{ padding: 24, color: "#888" }}>Yükleniyor…</div>;

  const open = (state.positions || []).filter((p) => p.status === "open");
  const bench = benchmark(state);
  const pv = portfolioValue(state);

  return (
    <div style={{ fontFamily: "-apple-system,Segoe UI,Roboto,sans-serif", maxWidth: 900, margin: "0 auto", color: "#1a1a2e", padding: 16 }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Finans Ajanı Paneli</h1>
      <div style={{ color: "#888", fontSize: 13, marginBottom: 16 }}>
        Son tur: {state.meta?.last_run_at || "—"}
      </div>

      {/* Özet */}
      <div style={{ ...card, display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 12 }}>
        <Metric label="Portföy" value={`${fmt(pv)} ₺`} />
        <Metric label="Nakit" value={`${fmt(state.cash_try)} ₺`} />
        <Metric label="Gerçekleşen P&L" value={`${fmt(state.realized_pnl_try || 0)} ₺`}
          color={(state.realized_pnl_try || 0) >= 0 ? "#0a7d2c" : "#b00"} />
        <Metric label="Açık pozisyon" value={open.length} />
        <Metric label="Bu ay API" value={`$${fmt(state.budget?.spend_usd || 0)}`}
          color={state.budget?.throttled ? "#b00" : "#333"} />
      </div>

      {/* Kıyas (§2.6) */}
      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Kıyas (XU100 / TÜFE)</h3>
        {bench ? (
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", fontSize: 14 }}>
            <span>Portföy getirisi: <b>{pct(bench.pr)}</b></span>
            <span>XU100: <b>{pct(bench.xr)}</b></span>
            <span>Göreli: <b style={{ color: (bench.rel ?? 0) >= 0 ? "#0a7d2c" : "#b00" }}>{pct(bench.rel)}</b></span>
            <span>TÜFE (yıllık): <b>{pct(bench.tufe)}</b></span>
          </div>
        ) : <div style={{ color: "#888" }}>Kıyas için en az 2 performans noktası gerekir.</div>}
      </div>

      {/* Açık pozisyonlar */}
      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Açık Pozisyonlar</h3>
        {open.length === 0 ? <div style={{ color: "#888" }}>Açık pozisyon yok.</div> : (
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: "left", background: "#f3f3fb" }}>
                <th style={th}>Sembol</th><th style={th}>Giriş</th><th style={th}>Son</th>
                <th style={th}>P&L</th><th style={th}>Stop</th><th style={th}>Tez / Çürütücü</th>
              </tr>
            </thead>
            <tbody>
              {open.map((p) => {
                const mv = (p.current_price ?? p.entry_price) * p.shares;
                const pnl = mv - p.entry_price * p.shares;
                return (
                  <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={td}><b>{p.symbol}</b> <span style={{ color: "#999" }}>{p.market}</span></td>
                    <td style={td}>{fmt(p.entry_price)}</td>
                    <td style={td}>{p.current_price != null ? fmt(p.current_price) : "—"}</td>
                    <td style={{ ...td, color: pnl >= 0 ? "#0a7d2c" : "#b00" }}>{fmt(pnl, 0)} ₺</td>
                    <td style={td}>{fmt(p.stop)}</td>
                    <td style={td}>
                      <div>{p.thesis}</div>
                      <div style={{ color: "#b06", fontSize: 12 }}>↯ {p.refuter}</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Ajan günlüğü */}
      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Ajan Günlüğü</h3>
        <div style={{ maxHeight: 220, overflowY: "auto", fontSize: 13 }}>
          {(state.log || []).slice().reverse().map((l, i) => (
            <div key={i} style={{ padding: "4px 0", borderBottom: "1px solid #f2f2f2" }}>
              <span style={chip("#eef", "#446")}>{l.kind}</span>{" "}
              <span style={{ color: "#999", fontSize: 11 }}>{l.ts}</span>
              <div>{l.message}</div>
            </div>
          ))}
          {(state.log || []).length === 0 && <div style={{ color: "#888" }}>Henüz kayıt yok.</div>}
        </div>
      </div>

      {/* Kaynak karnesi (§4) */}
      <div style={card}>
        <h3 style={{ marginTop: 0 }}>Kaynak Karnesi</h3>
        {(state.sources || []).map((c) => {
          const scored = (c.claims || []).filter((x) => x.scored && (x.status === "hit" || x.status === "miss"));
          const hits = scored.filter((x) => x.status === "hit").length;
          const hr = scored.length ? Math.round((hits / scored.length) * 100) : null;
          return (
            <div key={c.name} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: 14 }}>
              <span>{c.name} <span style={chip("#eee", "#666")}>{c.trust}</span></span>
              <span>{(c.claims || []).length} iddia · isabet {hr === null ? "—" : `%${hr}`}</span>
            </div>
          );
        })}
        {(state.sources || []).length === 0 && <div style={{ color: "#888" }}>Kaynak yok.</div>}
      </div>

      <div style={{ color: "#aaa", fontSize: 12, textAlign: "center", marginTop: 8 }}>
        Bu bir modelin önerisidir, finansal danışmanlık değildir.
      </div>
    </div>
  );
}

function Metric({ label, value, color = "#1a1a2e" }) {
  return (
    <div>
      <div style={{ color: "#888", fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

const th = { padding: "8px 6px" };
const td = { padding: "8px 6px", verticalAlign: "top" };
