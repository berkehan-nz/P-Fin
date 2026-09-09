/* 5. HUNI — asama asama daralma, eleme sebepleri, esik simulasyonu. */
window.ViewFunnel = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  async function render() {
    const [uni, log, scan] = await Promise.all([
      DataLayer.universe(), DataLayer.funnelLog(), DataLayer.scanState(),
    ]);
    renderScan(scan);
    const runs = log.runs || [];
    const latest = runs.length ? runs[runs.length - 1] : null;
    const stages = (latest && latest.stages) || (uni.log && uni.log.stages) || [];

    $('funnelSubtitle').textContent = latest
      ? `Son kosu ${Fmt.date(latest.date)} · ${uni.total_evaluated || 0} sirket degerlendirildi · ${runs.length} kosu kaydi`
      : 'Huni henuz calismadi';

    renderStages(stages);
    renderKills((latest && latest.kill_reasons) || (uni.log && uni.log.kill_reasons) || {});
    renderSim(stages);
  }

  /* Kademeli tarama: evren bir kuyruktur, her saat bir parti islenir.
     Buradaki cubuk kuyrugun ne kadarinin eridigini gosterir. */
  function renderScan(scan) {
    const el = $('scanProgress');
    if (!scan || !scan.queue || !scan.queue.length) {
      el.innerHTML = `<div class="card muted small">Tarama turu henuz baslamadi.
        Saatlik <b>Scan</b> is akisi calistiginda ilerleme burada gorunur.</div>`;
      return;
    }
    const total = scan.queue.length;
    const done = Math.min(scan.cursor || 0, total);
    const pct = total ? (done / total) * 100 : 0;
    const survivors = scan.survivor_count || 0;
    const perHour = scan.batch_size || 120;
    const hoursLeft = perHour ? Math.ceil((total - done) / perHour) : null;

    el.innerHTML = `<div class="card">
      <div class="spread">
        <span><b>Tur ${scan.cycle}</b>
          <span class="tiny dim">${scan.cycle_started ? Fmt.date(scan.cycle_started) + ' tarihinde basladi' : ''}</span></span>
        <span class="num">${done} / ${total} <span class="dim">(%${Fmt.num(pct, 1)})</span></span>
      </div>
      <span class="bar green" style="display:block;height:8px;margin:10px 0">
        <i style="width:${pct}%"></i></span>
      <div class="grid g-summary" style="margin-top:12px">
        <div><div class="tiny dim">ASAMA 2'YI GECEN</div>
          <div class="num" style="font-size:18px">${survivors}</div></div>
        <div><div class="tiny dim">KALAN</div>
          <div class="num" style="font-size:18px">${total - done}</div></div>
        <div><div class="tiny dim">SAATLIK PARTI</div>
          <div class="num" style="font-size:18px">${perHour}</div></div>
        <div><div class="tiny dim">TAHMINI BITIS</div>
          <div class="num" style="font-size:18px">${hoursLeft !== null ? '~' + hoursLeft + ' saat' : '—'}</div></div>
      </div>
      <div class="tiny dim" style="margin-top:10px">
        Son parti: ${scan.last_batch_at ? Fmt.date(scan.last_batch_at) : '—'} ·
        Son tur sonu: ${scan.last_finalized ? Fmt.date(scan.last_finalized) : 'henuz yok'}
        ${(scan.failed || []).length ? ` · yuklenemeyen ${scan.failed.length}` : ''}
      </div>
      ${done < total ? `<p class="tiny dim" style="margin:8px 0 0">Asama 3-4 (goreli
        ucuzluk ve puanlama) kuyruk bitince calisir — yuzdelikler havuzun
        tamamini ister.</p>` : ''}
    </div>`;
  }

  function renderStages(stages) {
    if (!stages.length) {
      $('funnelStages').innerHTML = `<div class="empty-state">
        <h2>Huni henuz calismadi</h2>
        <p>Tam evren taramasi haftalik is akisinda calisir.</p>
        <p class="tiny">GitHub → Actions → <b>Weekly (huni)</b> → Run workflow<br>
          Yerelde: <code>python -m src.run_funnel</code></p></div>`;
      return;
    }
    const max = Math.max(...stages.map((s) => s.input), 1);
    $('funnelStages').innerHTML = stages.map((s) => {
      const dropped = s.input - s.output;
      const pct = (s.output / max) * 100;
      return `<div class="funnel-stage">
        <span class="funnel-label"><b>${s.stage}.</b> ${Fmt.esc(s.name)}</span>
        <div class="funnel-bar" style="width:${Math.max(pct, 4)}%">${s.output}</div>
        <span class="tiny dim">${s.input} girdi · ${dropped} elendi
          ${s.input ? `(%${Fmt.num(dropped / s.input * 100, 0)})` : ''}</span>
      </div>`;
    }).join('');
  }

  function renderKills(reasons) {
    const entries = Object.entries(reasons);
    if (!entries.length) {
      $('killReasons').innerHTML = '<div class="card muted small">Kayit yok.</div>';
      return;
    }
    entries.sort((a, b) => b[1] - a[1]);
    const total = entries.reduce((n, [, c]) => n + c, 0);
    $('killReasons').innerHTML = `<table>
      <thead><tr><th>Eleme sebebi</th><th>Sirket</th><th>Pay</th></tr></thead>
      <tbody>${entries.map(([reason, count]) => `<tr>
        <td style="white-space:normal">${Fmt.esc(reason)}</td>
        <td class="num">${count}</td>
        <td class="num">${Fmt.pct(count / total * 100, 0)}</td>
      </tr>`).join('')}</tbody></table>`;
  }

  /* Esik simulasyonu — SADECE GORSEL. Veriyi degistirmez; bir esigi
     gevsetmenin/sikilastirmanin kabaca kac sirketi etkileyecegini gosterir. */
  function renderSim(stages) {
    const th = App.thresholds || {};
    const s1 = th.stage1 || {};
    const controls = [
      ['gross_margin_min_pct', 'Brut marj alt siniri', 0, 70, 5, '%'],
      ['rev_growth_ttm_min_pct', 'Hasilat buyumesi alt siniri', 0, 40, 1, '%'],
      ['net_debt_to_ebitda_max', 'Net borc/FAVOK ust siniri', 0, 6, 0.5, 'x'],
      ['share_count_growth_max_pct', 'Hisse artisi ust siniri', 0, 15, 1, '%'],
      ['sbc_to_fcf_max', 'SBC/FCF ust siniri', 0, 3, 0.1, 'x'],
    ];

    const stage1 = stages.find((s) => s.stage === 1);
    const baseIn = stage1 ? stage1.input : 0;
    const baseOut = stage1 ? stage1.output : 0;

    $('thresholdSim').innerHTML = `
      <p class="small">Asama 1 su an <b>${baseIn}</b> sirketten
        <b>${baseOut}</b> tanesini geciriyor.</p>
      ${controls.map(([key, label, min, max, step, unit]) => {
        const cur = s1[key];
        return `<div style="margin-bottom:14px">
          <div class="spread"><span class="small">${Fmt.esc(label)}</span>
            <span class="num small" id="sim-${key}">${unit === '%' ? '%' : ''}${cur}${unit === 'x' ? 'x' : ''}</span></div>
          <input type="range" data-sim="${key}" data-base="${cur}" data-unit="${unit}"
                 min="${min}" max="${max}" step="${step}" value="${cur}" style="width:100%">
        </div>`;
      }).join('')}
      <div class="card" id="simResult" style="background:var(--bg-3)"></div>`;

    const update = () => {
      const changed = [...$('thresholdSim').querySelectorAll('[data-sim]')]
        .map((el) => {
          const base = parseFloat(el.dataset.base);
          const now = parseFloat(el.value);
          const unit = el.dataset.unit;
          $(`sim-${el.dataset.sim}`).textContent =
            `${unit === '%' ? '%' : ''}${now}${unit === 'x' ? 'x' : ''}`;
          if (now === base) return null;
          const looser = el.dataset.sim.includes('min') ? now < base : now > base;
          return { key: el.dataset.sim, base, now, looser };
        }).filter(Boolean);

      if (!changed.length) {
        $('simResult').innerHTML =
          '<p class="small muted" style="margin:0">Esikleri oynatinca tahmini etki burada gorunur.</p>';
        return;
      }
      const looserCount = changed.filter((c) => c.looser).length;
      const direction = looserCount > changed.length / 2 ? 'gevsetildi' : 'sikilastirildi';
      $('simResult').innerHTML = `
        <p class="small" style="margin:0 0 6px"><b>${changed.length} esik ${direction}.</b></p>
        <ul class="small" style="margin:0;padding-left:18px">
          ${changed.map((c) => `<li>${Fmt.esc(c.key)}: ${c.base} → ${c.now}
            <span class="${c.looser ? 'c-yellow' : 'c-green'}">
              (${c.looser ? 'daha fazla sirket gecer' : 'daha az sirket gecer'})</span></li>`).join('')}
        </ul>
        <p class="tiny dim" style="margin:8px 0 0">Bu bir TAHMINDIR — gercek etki
          icin <code>src/config.py</code> icindeki <code>STAGE1</code> degerlerini
          degistirip <code>python -m src.run_funnel</code> calistir.</p>`;
    };

    $('thresholdSim').querySelectorAll('[data-sim]').forEach((el) =>
      el.addEventListener('input', update));
    update();
  }

  return { render };
})();
