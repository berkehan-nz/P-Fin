/* PAROLA EKRANI — yalnizca ARAYUZU gizler.
 *
 * Repo herkese acik: data/ altindaki JSON dosyalari
 * raw.githubusercontent.com uzerinden parolasiz okunabilir. Bu ekran
 * panoyu gelip gecen birinin gozunden saklar; veriyi korumaz. Veri de
 * korunacaksa: ozel repo + Cloudflare Access (README, "Parola").
 *
 * PAROLA KODDA YOK. Yalnizca PBKDF2-SHA-256 ozeti ve tuzu var. Repo acik
 * oldugu icin ozet de acik; bu yuzden duz SHA-256 yerine yavas bir
 * turetme (yuz binlerce tur) kullaniliyor: her tahmin tarayicida ~0,3 sn
 * surer, sozluk saldirisi pahalilasir. Yine de kisa/tahmin edilebilir bir
 * parola kirilir — en az 12 karakter, baska yerde kullanilmayan.
 *
 * AKIS
 *   - HASH bossa ekran kapali: pano dogrudan acilir.
 *   - Dogru parola -> sessionStorage'a ozet yazilir; sekme kapaninca silinir,
 *     yeni sekmede parola yeniden sorulur. Parola degisince eski oturumlar
 *     gecersiz olur (saklanan deger eski ozettir).
 *   - Parola dogrulanmadan data/ klasorune TEK ISTEK atilmaz: app.js
 *     baslamadan once Auth.gate() bekler.
 *   - Yeni parola ozeti: siteyi ?parola-olustur ile ac. Parola TARAYICIDA
 *     ozetlenir ve cihazdan cikmaz; cikan satir koda yazilir.
 */
window.Auth = (function () {
  'use strict';

  // Parola belirlenince bu uc deger doldurulur (?parola-olustur ciktisi).
  const CONFIG = {
    salt: '',
    hash: '',
    iterations: 600000,
  };

  const KEY = 'pfin.auth';
  const root = document.documentElement;

  function configured() { return Boolean(CONFIG.salt && CONFIG.hash); }

  function unlocked() {
    try { return sessionStorage.getItem(KEY) === CONFIG.hash; } catch (_) { return false; }
  }

  const hex = (buf) => [...new Uint8Array(buf)]
    .map((b) => b.toString(16).padStart(2, '0')).join('');

  async function derive(password, saltHex, iterations) {
    if (!(window.crypto && crypto.subtle)) {
      throw new Error('Bu tarayici sifreleme API\'sini desteklemiyor (https gerekli).');
    }
    const salt = new Uint8Array(saltHex.match(/../g).map((h) => parseInt(h, 16)));
    const key = await crypto.subtle.importKey(
      'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits(
      { name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, 256);
    return hex(bits);
  }

  // Kilitliyken icerik HIC cizilmesin (CSS: html.locked). Betik <head>'de
  // calistigi icin sayfa bir an bile acik gorunmez.
  const setupMode = /[?&]parola-olustur\b/.test(location.search);
  if (setupMode || (configured() && !unlocked())) root.classList.add('locked');

  function overlay(html) {
    const el = document.createElement('div');
    el.id = 'authGate';
    el.innerHTML = `<div class="auth-box">${html}</div>`;
    document.body.appendChild(el);
    return el;
  }

  /* Parola sorar; dogruysa cozulur. Yapilandirilmamissa hemen cozulur. */
  function gate() {
    if (setupMode) { renderSetup(); return new Promise(() => {}); }
    if (!configured() || unlocked()) { root.classList.remove('locked'); return Promise.resolve(); }

    return new Promise((resolve) => {
      const el = overlay(`
        <div class="brand" style="margin-bottom:14px">Berkehan <small>finansal takip</small></div>
        <form id="authForm" autocomplete="on">
          <label class="small muted" for="authPw">Parola</label>
          <input type="password" id="authPw" name="password" autocomplete="current-password"
                 required autofocus>
          <button class="primary" type="submit" id="authBtn">Ac</button>
          <p class="small c-red" id="authErr" role="alert" hidden></p>
        </form>
        <p class="tiny dim" style="margin:14px 0 0">Bu ekran yalnizca arayuzu gizler;
          repo herkese acik oldugu icin veri dosyalari yine okunabilir.</p>`);
      const form = el.querySelector('#authForm');
      const input = el.querySelector('#authPw');
      const btn = el.querySelector('#authBtn');
      const err = el.querySelector('#authErr');
      input.focus();

      form.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        btn.disabled = true; btn.textContent = 'Kontrol ediliyor...';
        err.hidden = true;
        try {
          const h = await derive(input.value, CONFIG.salt, CONFIG.iterations);
          if (h === CONFIG.hash) {
            try { sessionStorage.setItem(KEY, CONFIG.hash); } catch (_) { /* gizli sekme */ }
            el.remove();
            root.classList.remove('locked');
            resolve();
            return;
          }
          err.textContent = 'Parola yanlis.';
        } catch (e) {
          err.textContent = e.message || String(e);
        }
        err.hidden = false;
        input.value = '';
        input.focus();
        btn.disabled = false; btn.textContent = 'Ac';
      });
    });
  }

  /* Yeni parola ozeti uretir. Parola bu sayfadan disari cikmaz. */
  function renderSetup() {
    const el = overlay(`
      <div class="brand" style="margin-bottom:10px">Parola ozeti olustur</div>
      <p class="small muted" style="margin-top:0">Parola bu tarayicida ozetlenir ve hicbir
        yere gonderilmez. Cikan satiri Claude'a gonder; koda yalnizca ozet yazilir.
        En az 12 karakter, baska yerde kullanmadigin bir parola sec.</p>
      <form id="setupForm">
        <input type="password" id="pw1" placeholder="Yeni parola" autocomplete="new-password" required minlength="12">
        <input type="password" id="pw2" placeholder="Tekrar" autocomplete="new-password" required minlength="12">
        <button class="primary" type="submit">Ozeti olustur</button>
        <p class="small c-red" id="setupErr" role="alert" hidden></p>
      </form>
      <textarea id="setupOut" rows="3" readonly hidden></textarea>
      <button id="setupCopy" hidden>Kopyala</button>`);
    const $ = (id) => el.querySelector(`#${id}`);
    $('setupForm').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const err = $('setupErr');
      err.hidden = true;
      if ($('pw1').value !== $('pw2').value) {
        err.textContent = 'Iki parola ayni degil.'; err.hidden = false; return;
      }
      try {
        const salt = hex(crypto.getRandomValues(new Uint8Array(16)));
        const hash = await derive($('pw1').value, salt, CONFIG.iterations);
        $('pw1').value = ''; $('pw2').value = '';
        $('setupOut').value = `P-Fin parola ozeti: salt=${salt} hash=${hash} iterations=${CONFIG.iterations}`;
        $('setupOut').hidden = false; $('setupCopy').hidden = false;
      } catch (e) {
        err.textContent = e.message || String(e); err.hidden = false;
      }
    });
    $('setupCopy').addEventListener('click', () => {
      $('setupOut').select();
      try { navigator.clipboard.writeText($('setupOut').value); } catch (_) { document.execCommand('copy'); }
      $('setupCopy').textContent = 'Kopyalandi';
    });
  }

  /* Sekmeyi beklemeden kilitle (ust cubuktaki dugme). */
  function lock() {
    try { sessionStorage.removeItem(KEY); } catch (_) { /* yok say */ }
    location.reload();
  }

  return { gate, lock, configured, derive };
})();
