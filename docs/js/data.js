/* Veri katmani — data/*.json okuma, yol tespiti, onbellek.
 *
 * Dashboard bir JSON OKUYUCUDUR, veritabani degildir. localStorage'da
 * KALICI VERI TUTULMAZ; yalnizca gorunum tercihi (tema, aktif sekme)
 * saklanir. Tum durum repodaki dosyalarda yasar; boylece Claude da ayni
 * veriyi raw.githubusercontent.com uzerinden okuyabilir.
 */
window.DataLayer = (function () {
  'use strict';

  const REPO = 'berkehan-nz/P-Fin';
  const BRANCH = 'main';

  // Sirayla denenir. GitHub Pages'in kokten mi /docs'tan mi servis edildigi
  // depoya gore degisir; ayrica repoyu klonlayip yerel sunucuyla acmak da
  // calismali. Son care olarak raw.githubusercontent her durumda calisir.
  const BASES = [
    '../data',
    './data',
    `https://raw.githubusercontent.com/${REPO}/${BRANCH}/data`,
  ];

  let base = null;
  const cache = new Map();

  async function detectBase() {
    if (base) return base;
    for (const candidate of BASES) {
      try {
        const res = await fetch(`${candidate}/thresholds.json`, { cache: 'no-cache' });
        if (res.ok) { base = candidate; return base; }
      } catch (_) { /* sonrakini dene */ }
    }
    throw new Error(
      'data/ klasoru bulunamadi. Yerelde calistiriyorsan repo kokunde ' +
      '`python3 -m http.server` ile ac ve docs/ adresine git.'
    );
  }

  async function get(name, fallback) {
    if (cache.has(name)) return cache.get(name);
    const root = await detectBase();
    try {
      const res = await fetch(`${root}/${name}`, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`${res.status}`);
      const json = await res.json();
      cache.set(name, json);
      return json;
    } catch (err) {
      if (fallback !== undefined) { cache.set(name, fallback); return fallback; }
      throw new Error(`${name} okunamadi: ${err.message}`);
    }
  }

  function rawUrl(path) {
    return `https://raw.githubusercontent.com/${REPO}/${BRANCH}/${path}`;
  }

  function editUrl(path) {
    return `https://github.com/${REPO}/edit/${BRANCH}/${path}`;
  }

  // Gorunum tercihi — VERI DEGIL. Kaybolursa hicbir sey kaybolmaz.
  const prefs = {
    get(key, dflt) {
      try { const v = localStorage.getItem(`nx.${key}`); return v === null ? dflt : JSON.parse(v); }
      catch (_) { return dflt; }
    },
    set(key, value) {
      try { localStorage.setItem(`nx.${key}`, JSON.stringify(value)); } catch (_) { /* yok say */ }
    },
  };

  return {
    detectBase, rawUrl, editUrl, prefs,
    repo: REPO, branch: BRANCH,
    thresholds:    () => get('thresholds.json'),
    candidates:    () => get('candidates.json', { candidates: [], seed: [], manual: [], counts: {} }),
    universe:      () => get('universe.json', { log: { stages: [] }, sectors: {} }),
    funnelLog:     () => get('funnel_log.json', { runs: [] }),
    scanState:     () => get('scan_state.json', null),
    macro:         () => get('macro.json', { series: {} }),
    overview:      () => get('overview.json', { movers: [], news: [] }),
    portfolio:     () => get('portfolio_state.json', { positions: [], summary: {}, warnings: [] }),
    watchlist:     () => get('watchlist.json', { entries: [] }),
    card:          (t) => get(`cards/${String(t).toUpperCase()}.json`, null),
    cardRawUrl:    (t) => rawUrl(`data/cards/${String(t).toUpperCase()}.json`),
    clearCache:    () => cache.clear(),
  };
})();
