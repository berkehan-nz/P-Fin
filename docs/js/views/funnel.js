/* 5. HUNI — 3831 sirketten 50'ye giden yolun tamami.
 *
 * VERI KAYNAGI: canli tarama durumu (scan_state.json). Onceki surum
 * universe.json ve funnel_log.json'a bakiyordu; onlari yalnizca TAM huni
 * kosusu (run_funnel) yaziyor ve o hic calismadi. Sonuc: 1500 sirket
 * islenmis, 1400'u elenmisken sayfa "Huni henuz calismadi" diyordu.
 * Kademeli tarama calisiyorsa sayfa onu gosterir; tam kosu varsa onu tercih eder.
 */
window.ViewFunnel = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  let survivors = [];
  let killGroups = [];

  async function render() {
    const [uni, log, scan, surv, cand] = await Promise.all([
      DataLayer.universe(), DataLayer.funnelLog(), DataLayer.scanState(),
      DataLayer.survivors(), DataLayer.candidates(),
    ]);

    survivors = (surv && surv.survivors) || [];
    killGroups = (App.thresholds.kill_reason_groups || []).map((g) => ({
      ...g, re: new RegExp(g.pattern),
    }));

    const runs = log.runs || [];
    const latest = runs.length ? runs[runs.length - 1] : null;

    // Tam kosu varsa onu, yoksa canli taramayi kaynak al.
    const fromFullRun = latest && (latest.stages || []).length;
    const stages = fromFullRun ? latest.stages : stagesFromScan(scan);
    const kills = fromFullRun ? (latest.kill_reasons || {})
                              : ((scan && scan.kill_counts) || {});

    $('funnelSubtitle').innerHTML = subtitle(scan, fromFullRun, latest, uni);

    renderScan(scan);
    renderPipeline(stages, kills, scan, cand);
    renderKindSplit(fromFullRun ? latest : scan);
    renderKills(kills);
    renderSurvivors();
    renderSim(stages);
  }

  function subtitle(scan, fromFullRun, latest, uni) {
    if (fromFullRun && latest.partial) {
      return `Tur ${latest.cycle || '?'} devam ediyor · ${latest.scanned || 0} sirket tarandi · `
        + `asama 3-4 sayilari su anki havuza gore, tur sonunda degisebilir`;
    }
    if (fromFullRun) {
      return `Tam evren taramasi · ${Fmt.date(latest.date)} · `
        + `${uni.total_evaluated || 0} sirket degerlendirildi`;
    }
    if (!scan || !scan.queue) return 'Tarama henuz baslamadi.';
    const done = Math.min(scan.cursor || 0, scan.queue.length);
    return `Kademeli tarama · Tur ${scan.cycle} · ${done} / ${scan.queue.length} sirket islendi`
      + ` · <b>${scan.survivor_count || 0}</b> tanesi Asama 2'yi gecti`;
  }

  /* scan_state'teki sayaclari huni asamalari bicimine cevirir. */
  function stagesFromScan(scan) {
    const sc = (scan && scan.stage_counts) || {};
    const info = App.thresholds.stage_info || {};
    const out = [];
    for (const n of [0, 1, 2]) {
      const c = sc[String(n)];
      if (!c) continue;
      out.push({
        stage: n, name: (info[n] || {}).name || `Asama ${n}`,
        input: c.in, output: c.out,
      });
    }
    return out;
  }

  /* Kademeli tarama: evren bir kuyruktur, her parti bir dilim isler. */
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
    const perBatch = scan.batch_size || 120;

    el.innerHTML = `<div class="card">
      <div class="spread">
        <span><b>Tur ${scan.cycle}</b>
          <span class="tiny dim">${scan.cycle_started ? Fmt.date(scan.cycle_started) + ' tarihinde basladi' : ''}</span></span>
        <span class="num">${done} / ${total} <span class="dim">(%${Fmt.num(pct, 1)})</span></span>
      </div>
      <span class="bar green" style="display:block;height:8px;margin:10px 0">
        <i style="width:${pct}%"></i></span>
      <div class="grid g-summary" style="margin-top:12px">
        ${miniStat("ASAMA 2'YI GECEN", scan.survivor_count || 0)}
        ${miniStat('KALAN', total - done)}
        ${miniStat('PARTI BOYU', perBatch)}
        ${miniStat('KALAN PARTI', Math.ceil((total - done) / perBatch))}
      </div>
      <div class="tiny dim" style="margin-top:10px">
        Son parti: ${scan.last_batch_at ? Fmt.date(scan.last_batch_at) : '—'} ·
        Son tur sonu: ${scan.last_finalized ? Fmt.date(scan.last_finalized) : 'henuz yok'}
        ${(scan.failed || []).length ? ` · yuklenemeyen ${scan.failed.length}` : ''}
      </div>
      ${done < total ? `<p class="tiny dim" style="margin:8px 0 0">
        Parti sayisi saate esit DEGILDIR: is akisi saatlik kurulu ama GitHub
        zamanlanmis kosulari yogunlukta atliyor; pratikte birkac saatte bir
        calisiyor.</p>` : ''}
    </div>`;
  }

  function miniStat(label, value) {
    return `<div><div class="tiny dim">${Fmt.esc(label)}</div>
      <div class="num" style="font-size:18px">${value}</div></div>`;
  }

  /* -------------------------------------------------------- huni akisi */
  /* Sayfanin kalbi: 3831 -> 50 yolunun her adimi, ne kadar daraldigi ve
     NEDEN daraldigi tek gorunumde. */
  function renderPipeline(stages, kills, scan, cand) {
    const info = App.thresholds.stage_info || {};
    const grouped = groupKills(kills);
    const byStage = {};
    grouped.forEach((g) => { (byStage[g.stage] = byStage[g.stage] || []).push(g); });

    const queueTotal = (scan && scan.queue) ? scan.queue.length : null;
    const maxIn = Math.max(...stages.map((s) => s.input), 1);
    const interimCount = ((cand && cand.candidates) || []).length;
    const finalized = scan && scan.last_finalized;

    const rows = [0, 1, 2, 3, 4].map((n) => {
      const st = stages.find((s) => s.stage === n);
      const meta = info[n] || {};
      const reasons = (byStage[n] || []).sort((a, b) => b.count - a.count);

      // Asama 3-4 tur sonunda calisir; tur bitmeden sayisi YOKTUR.
      if (!st) {
        const pending = n >= 3;
        return stageRow({
          n, name: meta.name, plain: meta.plain, pending,
          note: pending
            ? (finalized
                ? 'Tur sonunda calisti'
                : `Tur bitince calisir${interimCount ? ` · su an ${interimCount} gecici aday var` : ''}`)
            : 'Bu turda veri yok',
          reasons,
        });
      }
      return stageRow({
        n, name: meta.name, plain: meta.plain,
        input: st.input, output: st.output, maxIn, reasons,
      });
    });

    $('funnelStages').innerHTML = `
      <p class="small muted" style="margin:-4px 0 12px">
        ${queueTotal ? `Bu turda <b>${queueTotal}</b> sirketlik kuyruk taraniyor. ` : ''}
        Her asama bir oncekinden gelenleri suzer; asagidaki her cubuk
        <b>o asamadan GECEN</b> sirket sayisidir.</p>
      <div class="pipeline">${rows.join('')}</div>`;

    $('funnelStages').querySelectorAll('.stage-toggle').forEach((btn) => {
      btn.addEventListener('click', () => {
        const box = document.getElementById(`why-${btn.dataset.stage}`);
        if (!box) return;
        const open = box.hidden;
        box.hidden = !open;
        btn.setAttribute('aria-expanded', String(open));
        btn.textContent = open ? 'gizle' : 'neden elendiler?';
      });
    });
  }

  function stageRow({ n, name, plain, input, output, maxIn, pending, note, reasons }) {
    const dropped = (input != null && output != null) ? input - output : null;
    const width = (output != null && maxIn) ? Math.max((output / maxIn) * 100, 2) : 0;
    const dropPct = (dropped != null && input) ? (dropped / input) * 100 : null;

    return `<div class="stage ${pending ? 'stage-pending' : ''}">
      <div class="stage-head">
        <span class="stage-no">${n}</span>
        <div style="min-width:0">
          <div class="stage-name">${Fmt.esc(name || '')}</div>
          <div class="tiny dim" style="white-space:normal;line-height:1.4">${Fmt.esc(plain || '')}</div>
        </div>
        <div class="stage-count">
          ${output != null
            ? `<span class="num">${output}</span><span class="tiny dim">gecti</span>`
            : `<span class="tiny dim" style="text-align:right">${Fmt.esc(note || '')}</span>`}
        </div>
      </div>
      ${output != null ? `
        <div class="stage-bar"><i style="width:${width}%"></i></div>
        <div class="stage-foot">
          <span class="tiny dim">${input} girdi · <b class="c-red">${dropped} elendi</b>
            ${dropPct != null ? `(%${Fmt.num(dropPct, 0)})` : ''}</span>
          ${reasons.length ? `<button class="ghost tiny stage-toggle" data-stage="${n}"
            aria-expanded="false">neden elendiler?</button>` : ''}
        </div>
        ${reasons.length ? `<div class="stage-why" id="why-${n}" hidden>
          ${reasons.map((g) => `<div class="why-row">
            <span class="why-bar"><i style="width:${Math.max((g.count / reasons[0].count) * 100, 3)}%"></i></span>
            <span class="why-label">${Fmt.esc(g.label)}</span>
            <span class="num tiny">${g.count}</span>
            <span class="tiny dim why-plain">${Fmt.esc(g.plain)}</span>
          </div>`).join('')}
        </div>` : ''}
      ` : ''}
    </div>`;
  }

  /* Ham eleme metinleri esik degerlerini iceriyor ("Brut marj %20.3 <= %30"),
     bu yuzden yuzlerce farkli metin olusuyor. Gruplama kurallari config.py'de
     tanimli ve thresholds.json ile geliyor — kural bilgisi burada yok. */
  function groupKills(kills) {
    const acc = {};
    Object.entries(kills || {}).forEach(([reason, count]) => {
      const g = killGroups.find((x) => x.re.test(reason));
      const key = g ? g.label : 'Siniflandirilmamis';
      if (!acc[key]) {
        acc[key] = { label: key, stage: g ? g.stage : 9,
                     plain: g ? g.plain : '', count: 0, raw: [] };
      }
      acc[key].count += count;
      acc[key].raw.push([reason, count]);
    });
    return Object.values(acc);
  }

  /* ELENDI ile VERI_YOK ayrimi.

     Bu ikisi eskiden ayni sepetteydi ve tehlikeliydi: "FCF negatif ve yuksek
     buyume istisnasi saglanmadi (buyume bilinmiyor; brut marj bilinmiyor)"
     diyen 175 sirket, kotu olduklari icin degil BAKAMADIGIMIZ icin listeden
     dusuyordu. Sessizce kaybolan aday, elenmis adaydan farklidir; ayri
     gosterilmeli ki tekrar denendigi gorunsun. */
  function renderKindSplit(src) {
    const el = $('funnelKindSplit');
    if (!el) return;
    const kinds = (src && src.kill_kinds) || {};
    const elendi = kinds.ELENDI || 0;
    const veriYok = kinds.VERI_YOK || 0;
    if (!elendi && !veriYok) { el.innerHTML = ''; return; }

    const kuyruk = (src && (src.retry_queue_size ?? src.retry_queue)) || 0;
    const kuyrukN = typeof kuyruk === 'number' ? kuyruk : (kuyruk.length || 0);
    const toplam = elendi + veriYok;
    const pay = (n) => toplam ? Math.round((n / toplam) * 100) : 0;

    el.innerHTML = `
      <div class="card">
        <h3>Listeden dusenler neden dustu?</h3>
        <div class="split-row">
          <div class="split-cell">
            <div class="split-num">${elendi.toLocaleString('tr-TR')}</div>
            <div class="split-label"><b>Elendi</b> — bir kurali ihlal etti</div>
            <div class="split-bar"><span style="width:${pay(elendi)}%"></span></div>
            <div class="muted">Piyasa degeri cok kucuk, marj dusuk, borc yuksek gibi
              BILINEN ve kotu bir deger yuzunden.</div>
          </div>
          <div class="split-cell warn">
            <div class="split-num">${veriYok.toLocaleString('tr-TR')}</div>
            <div class="split-label"><b>Veri yok</b> — karar verilemedi</div>
            <div class="split-bar warn"><span style="width:${pay(veriYok)}%"></span></div>
            <div class="muted">Sirket kotu oldugu icin degil, gerekli sayiyi
              hesaplayamadigimiz icin dustu. <b>Eleme sayilmaz.</b>
              ${kuyrukN ? `${kuyrukN} tanesi onumuzdeki turda onbellek atlanarak
                yeniden denenecek.` : ''}</div>
          </div>
        </div>
      </div>`;
  }

  function renderKills(kills) {
    const grouped = groupKills(kills).sort((a, b) => b.count - a.count);
    if (!grouped.length) {
      $('killReasons').innerHTML = '<div class="card muted small">Henuz eleme kaydi yok.</div>';
      return;
    }
    const total = grouped.reduce((n, g) => n + g.count, 0);
    const info = App.thresholds.stage_info || {};
    $('killReasons').innerHTML = `<table>
      <thead><tr>
        <th style="min-width:180px">Sebep</th><th>Asama</th><th>Sirket</th><th>Pay</th>
        <th style="min-width:280px;text-align:left">Ne demek</th>
      </tr></thead>
      <tbody>${grouped.map((g) => `<tr>
        <td><b>${Fmt.esc(g.label)}</b></td>
        <td class="tiny dim">${g.stage === 9 ? '—' : `${g.stage}. ${Fmt.esc((info[g.stage] || {}).name || '')}`}</td>
        <td class="num">${g.count}</td>
        <td class="num">${Fmt.pct(g.count / total * 100, 0)}</td>
        <td style="text-align:left;white-space:normal;line-height:1.45">${Fmt.esc(g.plain)}</td>
      </tr>`).join('')}</tbody></table>
      <div class="tiny dim" style="padding:8px 10px">Toplam ${total} eleme.
        Ayni sirket birden fazla kurala takilsa bile ILK takildigi yerde durur.</div>`;
  }

  /* --------------------------------------------- Asama 2'yi gecenler */
  function renderSurvivors() {
    const el = $('survivorList');
    if (!el) return;
    if (!survivors.length) {
      el.innerHTML = `<div class="card muted small">Bu turda henuz Asama 2'yi
        gecen sirket yok.</div>`;
      return;
    }

    const sectors = [...new Set(survivors.map((s) => s.sector).filter(Boolean))].sort();
    el.innerHTML = `
      <div class="card" style="margin-bottom:12px">
        <div class="row">
          <label class="tiny dim">Sektor
            <select id="svSector"><option value="">Hepsi (${survivors.length})</option>
              ${sectors.map((s) => `<option value="${Fmt.esc(s)}">${Fmt.esc(s)}</option>`).join('')}
            </select></label>
          <label class="tiny dim">Kol
            <select id="svTrack"><option value="">Hepsi</option>
              <option value="A">Kol A (karli)</option>
              <option value="B">Kol B (buyume)</option></select></label>
          <label class="tiny dim">Sirala
            <select id="svSort">
              <option value="ticker">Sembol</option>
              <option value="growth">Buyume</option>
              <option value="fcf">FCF verimi</option>
              <option value="mcap">Piyasa degeri</option>
            </select></label>
        </div>
      </div>
      <div id="svTable" class="table-wrap"></div>`;

    ['svSector', 'svTrack', 'svSort'].forEach((id) =>
      $(id).addEventListener('input', drawSurvivors));
    drawSurvivors();
  }

  function drawSurvivors() {
    const sector = $('svSector').value;
    const track = $('svTrack').value;
    const sort = $('svSort').value;
    const mv = (r, k) => {
      const v = (r.metrics || {})[k];
      return Fmt.isNum(v) ? v : -Infinity;
    };

    let rows = survivors.filter((r) =>
      (!sector || r.sector === sector) && (!track || r.track === track));
    rows.sort(({
      ticker: (a, b) => String(a.ticker).localeCompare(String(b.ticker)),
      growth: (a, b) => mv(b, 'rev_growth_ttm') - mv(a, 'rev_growth_ttm'),
      fcf: (a, b) => mv(b, 'fcf_yield_ev') - mv(a, 'fcf_yield_ev'),
      mcap: (a, b) => (b.market_cap_musd || 0) - (a.market_cap_musd || 0),
    })[sort]);

    const cols = [['rev_growth_ttm', 'Buyume'], ['gross_margin', 'Brut marj'],
                  ['fcf_yield_ev', 'FCF verimi'], ['ev_ebit', 'EV/FVOK'],
                  ['roic', 'ROIC'], ['rule_of_40', '40 Kurali'],
                  ['piotroski_f', 'Piotroski']];

    $('svTable').innerHTML = `<table>
      <thead><tr><th>Sembol</th><th>Kol</th><th>Sektor</th><th>Piyasa degeri</th>
        ${cols.map(([k, l]) => `<th title="${Fmt.esc((Fmt.spec(k) || {}).plain || '')}">${Fmt.esc(l)}</th>`).join('')}
      </tr></thead>
      <tbody>${rows.map((r) => `<tr data-ticker="${Fmt.esc(r.ticker)}" style="cursor:pointer">
        <td><b>${Fmt.esc(r.ticker)}</b>
          <div class="tiny dim">${Fmt.esc((r.name || '').slice(0, 24))}</div></td>
        <td>${Fmt.trackBadge(r.track)}</td>
        <td class="tiny">${Fmt.esc(r.sector || '')}</td>
        <td class="num">${Fmt.money(r.market_cap_musd, { musd: true })}</td>
        ${cols.map(([k]) => {
          const v = (r.metrics || {})[k];
          return `<td class="num ${Fmt.isNum(v) ? 'c-' + Fmt.colorFor(k, v) : 'c-gray'}">${
            Fmt.isNum(v) ? Fmt.esc(Fmt.metricValue(k, v)) : '<span class="dim">·</span>'}</td>`;
        }).join('')}
      </tr>`).join('')}</tbody></table>
      <div class="tiny dim" style="padding:8px 10px">
        ${rows.length} sirket. <b>Bu sirketlerin PUANI YOKTUR</b> — puanlama
        (Asama 4) sektor yuzdeligi ister, o da havuzun tamami bitmeden
        hesaplanamaz. Buradaki sayilar ham metriklerdir.
        Karti uretilmis olanlara tiklayip detayina gecebilirsin.</div>`;

    $('svTable').querySelectorAll('[data-ticker]').forEach((el) =>
      el.addEventListener('click', () => {
        location.hash = `#/company/${el.dataset.ticker}`;
      }));
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
          degistirip taramayi yeniden calistir.</p>`;
    };

    $('thresholdSim').querySelectorAll('[data-sim]')
      .forEach((el) => el.addEventListener('input', update));
    update();
  }

  return { render };
})();
