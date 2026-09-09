/* Uygulama kabugu — yonlendirme, tema, modal, panoya kopyalama.
 *
 * localStorage yalnizca GORUNUM TERCIHI tutar (tema, izgara/tablo).
 * Veri asla burada saklanmaz; tek dogru kaynak repodaki JSON dosyalaridir.
 */
window.App = (function () {
  'use strict';

  const ROUTES = {
    '/overview':   { screen: 'overview',   view: () => ViewOverview.render() },
    '/candidates': { screen: 'candidates', view: () => ViewCandidates.render() },
    '/portfolio':  { screen: 'portfolio',  view: () => ViewPortfolio.render() },
    '/funnel':     { screen: 'funnel',     view: () => ViewFunnel.render() },
  };

  const api = { thresholds: {} };

  /* ------------------------------------------------------------- tema */
  function initTheme() {
    // Sartname: koyu tema VARSAYILAN, acik tema bir anahtar.
    // Sistem tercihi varsayilani ezmez; kullanici acikca sectiyse o kalir.
    const theme = DataLayer.prefs.get('theme', null) || 'dark';
    document.documentElement.setAttribute('data-theme', theme);

    document.getElementById('themeToggle').addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'dark'
        ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      DataLayer.prefs.set('theme', next);
    });
  }

  /* ------------------------------------------------------- yonlendirme */
  function show(screenId) {
    document.querySelectorAll('.screen').forEach((el) =>
      el.classList.toggle('active', el.id === `screen-${screenId}`));
    document.querySelectorAll('#tabs a').forEach((a) =>
      a.classList.toggle('active', a.getAttribute('href') === `#/${screenId}`));
  }

  async function route() {
    const hash = location.hash.replace(/^#/, '') || '/overview';

    const company = hash.match(/^\/company\/([A-Za-z0-9.\-]+)$/);
    if (company) {
      show('company');
      document.querySelectorAll('#tabs a').forEach((a) => a.classList.remove('active'));
      try { await ViewCompany.render(company[1].toUpperCase()); }
      catch (err) { fail(err); }
      window.scrollTo(0, 0);
      return;
    }

    const route = ROUTES[hash] || ROUTES['/overview'];
    show(route.screen);
    try { await route.view(); } catch (err) { fail(err); }
  }

  function fail(err) {
    console.error(err);
    document.getElementById('loadError').innerHTML =
      `<div class="banner"><b>Veri yuklenemedi.</b> ${Fmt.esc(err.message || err)}</div>`;
  }

  /* ------------------------------------------------------------ modal */
  function modal(html, onMount) {
    closeModal();
    const back = document.createElement('div');
    back.className = 'modal-backdrop';
    back.innerHTML = `<div class="modal" role="dialog" aria-modal="true">${html}</div>`;
    back.addEventListener('click', (e) => { if (e.target === back) closeModal(); });
    document.getElementById('modalRoot').appendChild(back);
    document.addEventListener('keydown', escClose);
    if (onMount) onMount(back.querySelector('.modal'));
    const first = back.querySelector('input, select, textarea, button');
    if (first) first.focus();
  }

  function escClose(e) { if (e.key === 'Escape') closeModal(); }

  function closeModal() {
    document.getElementById('modalRoot').innerHTML = '';
    document.removeEventListener('keydown', escClose);
  }

  /* ------------------------------------------------------------ kopya */
  async function copy(text, message) {
    try {
      await navigator.clipboard.writeText(text);
      toast(message || 'Kopyalandi');
    } catch (_) {
      // Clipboard API kapaliysa (http, izin yok) elle secim yolu
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast(message || 'Kopyalandi'); }
      catch (__) { toast('Kopyalanamadi — metni elle sec'); }
      ta.remove();
    }
  }

  function toast(message) {
    const root = document.getElementById('toastRoot');
    root.innerHTML = `<div class="toast">${Fmt.esc(message)}</div>`;
    setTimeout(() => { root.innerHTML = ''; }, 2600);
  }

  /* ------------------------------------------------------------ baslat */
  async function start() {
    initTheme();
    try {
      const th = await DataLayer.thresholds();
      api.thresholds = th;
      Fmt.setThresholds(th.thresholds);
      const stamp = th.as_of ? `esikler ${Fmt.date(th.as_of)}` : '';
      document.getElementById('asOf').textContent = stamp;
    } catch (err) {
      fail(err);
      return;
    }
    window.addEventListener('hashchange', route);
    await route();
  }

  api.modal = modal;
  api.closeModal = closeModal;
  api.copy = copy;
  api.toast = toast;
  api.route = route;

  document.addEventListener('DOMContentLoaded', start);
  return api;
})();
