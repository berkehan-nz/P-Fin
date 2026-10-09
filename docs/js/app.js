/* Uygulama kabuğu — yönlendirme, tema, modal, panoya kopyalama.
 *
 * localStorage yalnızca GÖRÜNÜM TERCİHİ tutar (tema, liste/kart, seçili
 * kıyas). Veri asla burada saklanmaz; tek doğru kaynak repodaki JSON'lardır.
 *
 * Rotalar: #/bugun · #/portfoy[/plan|pozisyonlar|islemler|haftalik] ·
 * #/adaylar · #/piyasa · #/huni · #/sirket/<SEMBOL>. Eski bağlantılar
 * (#/overview, #/company/X, #/weekly ...) aynı yere gider.
 */
window.App = (function () {
  'use strict';

  const ROUTES = {
    bugun:   { screen: 'today',      view: () => ViewToday.render() },
    portfoy: { screen: 'portfolio',  view: (arg) => ViewPortfolio.render(arg) },
    adaylar: { screen: 'candidates', view: () => ViewCandidates.render() },
    piyasa:  { screen: 'market',     view: () => ViewMarket.render() },
    huni:    { screen: 'funnel',     view: () => ViewFunnel.render() },
    sirket:  { screen: 'company',    view: (arg) => ViewCompany.render(String(arg || '').toUpperCase()) },
  };
  const ALIASES = {
    overview: ['bugun'], portfolio: ['portfoy'], candidates: ['adaylar'],
    funnel: ['huni'], market: ['piyasa'], weekly: ['portfoy', 'haftalik'], company: ['sirket'],
  };

  const api = { thresholds: {} };

  /* ------------------------------------------------------------- tema */
  function initTheme() {
    // Koyu tema varsayılan; açık tema bir anahtar. Seçim hatırlanır.
    const theme = DataLayer.prefs.get('theme', null) || 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('themeToggle').addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      DataLayer.prefs.set('theme', next);
      // Grafikler renkleri CSS değişkeninden alır; yeniden çizmeye gerek yok.
    });
  }

  /* ------------------------------------------------------- yönlendirme */
  function show(screen) {
    document.querySelectorAll('.screen').forEach((el) =>
      el.classList.toggle('active', el.id === `screen-${screen}`));
    document.querySelectorAll('#tabs a').forEach((a) =>
      a.classList.toggle('active', a.dataset.screen === screen));
  }

  function parse() {
    const hash = location.hash.replace(/^#/, '');
    // Sayfa içi çapa ('#metrikler') rota değildir.
    if (hash && hash[0] !== '/') return null;
    let [name, arg] = hash.replace(/^\//, '').split('/');
    if (ALIASES[name]) {
      const [n, a] = ALIASES[name];
      name = n;
      arg = arg || a;
    }
    if (!ROUTES[name]) name = 'bugun';
    return { name, arg };
  }

  let current = null;
  async function route() {
    const r = parse();
    if (!r) return;
    const key = `${r.name}/${r.arg || ''}`;
    const screenChanged = !current || current.split('/')[0] !== r.name;
    current = key;
    show(ROUTES[r.name].screen);
    document.getElementById('loadError').innerHTML = '';
    try { await ROUTES[r.name].view(r.arg); } catch (err) { fail(err); }
    if (screenChanged) window.scrollTo(0, 0);
  }

  function go(path) { location.hash = `#/${path}`; }

  function fail(err) {
    console.error(err);
    document.getElementById('loadError').innerHTML =
      `<div class="band bad"><span class="ico">!</span><span><b>Veri yüklenemedi.</b>
       ${Fmt.esc(err.message || err)}</span></div>`;
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
      toast(message || 'Kopyalandı');
    } catch (_) {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;opacity:0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast(message || 'Kopyalandı'); }
      catch (__) { toast('Kopyalanamadı — metni elle seç'); }
      ta.remove();
    }
  }

  function toast(message) {
    const root = document.getElementById('toastRoot');
    root.innerHTML = `<div class="toast">${Fmt.esc(message)}</div>`;
    setTimeout(() => { root.innerHTML = ''; }, 2600);
  }

  /* ------------------------------------------------------------ başlat */
  async function start() {
    initTheme();
    // Parola doğrulanmadan data/ klasörüne tek istek atılmaz.
    await Auth.gate();
    if (Auth.configured()) {
      const lock = document.getElementById('lockBtn');
      lock.hidden = false;
      lock.addEventListener('click', () => Auth.lock());
    }
    try {
      const th = await DataLayer.thresholds();
      api.thresholds = th;
      Fmt.setThresholds(th.thresholds);
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
  api.go = go;

  document.addEventListener('DOMContentLoaded', start);
  return api;
})();
