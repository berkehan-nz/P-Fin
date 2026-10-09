/* PAROLA EKRANI — yalnızca ARAYÜZÜ gizler.
 *
 * Repo herkese açık: data/ altındaki JSON dosyaları
 * raw.githubusercontent.com üzerinden parolasız okunabilir. Bu ekran
 * panoyu gelip geçen birinin gözünden saklar; veriyi korumaz. Veri de
 * korunacaksa: özel repo + Cloudflare Access (README, "Parola").
 *
 * PAROLA KODDA YOK. Yalnızca PBKDF2-SHA-256 özeti ve tuzu var. Repo açık
 * olduğu için özet de açık; bu yüzden düz SHA-256 yerine yavaş bir
 * türetme (yüz binlerce tur) kullanılıyor: her tahmin tarayıcıda ~0,3 sn
 * sürer, sözlük saldırısı pahalılaşır. Yine de kısa/tahmin edilebilir bir
 * parola kırılır — en az 12 karakter, başka yerde kullanılmayan.
 *
 * AKIŞ
 *   - Özet boşsa ekran kapalı: pano doğrudan açılır.
 *   - Doğru parola → sessionStorage'a özet yazılır; sekme kapanınca silinir,
 *     yeni sekmede parola yeniden sorulur. Parola değişince eski oturumlar
 *     geçersiz olur (saklanan değer eski özettir).
 *   - Parola doğrulanmadan data/ klasörüne TEK İSTEK atılmaz: app.js
 *     başlamadan önce Auth.gate() bekler.
 *   - Yeni parola özeti: siteyi ?parola-olustur ile aç. Parola TARAYICIDA
 *     özetlenir ve cihazdan çıkmaz; çıkan satır koda yazılır.
 */
window.Auth = (function () {
  'use strict';

  // Parola belirlenince bu üç değer doldurulur (?parola-olustur çıktısı).
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
      throw new Error('Bu tarayıcı şifreleme API\'sini desteklemiyor (https gerekli).');
    }
    const salt = new Uint8Array(saltHex.match(/../g).map((h) => parseInt(h, 16)));
    const key = await crypto.subtle.importKey(
      'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits(
      { name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, 256);
    return hex(bits);
  }

  // Kilitliyken içerik HİÇ çizilmesin (CSS: html.locked). Betik <head>'de
  // çalıştığı için sayfa bir an bile açık görünmez.
  const setupMode = /[?&]parola-olustur\b/.test(location.search);
  if (setupMode || (configured() && !unlocked())) root.classList.add('locked');

  function overlay(html) {
    const el = document.createElement('div');
    el.id = 'authGate';
    el.innerHTML = `<div class="auth-box">${html}</div>`;
    document.body.appendChild(el);
    return el;
  }

  /* Parola sorar; doğruysa çözülür. Yapılandırılmamışsa hemen çözülür. */
  function gate() {
    if (setupMode) { renderSetup(); return new Promise(() => {}); }
    if (!configured() || unlocked()) { root.classList.remove('locked'); return Promise.resolve(); }

    return new Promise((resolve) => {
      const el = overlay(`
        <div class="brand" style="margin-bottom:14px">P-Fin</div>
        <form id="authForm" autocomplete="on">
          <label class="small muted" for="authPw">Parola</label>
          <input type="password" id="authPw" name="password" autocomplete="current-password"
                 required autofocus>
          <button class="primary" type="submit" id="authBtn">Aç</button>
          <p class="small bad-text" id="authErr" role="alert" hidden></p>
        </form>
        <p class="small dim" style="margin:14px 0 0">Bu ekran yalnızca arayüzü gizler;
          repo herkese açık olduğu için veri dosyaları yine okunabilir.</p>`);
      const form = el.querySelector('#authForm');
      const input = el.querySelector('#authPw');
      const btn = el.querySelector('#authBtn');
      const err = el.querySelector('#authErr');
      input.focus();

      form.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        btn.disabled = true; btn.textContent = 'Kontrol ediliyor…';
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
          err.textContent = 'Parola yanlış.';
        } catch (e) {
          err.textContent = e.message || String(e);
        }
        err.hidden = false;
        input.value = '';
        input.focus();
        btn.disabled = false; btn.textContent = 'Aç';
      });
    });
  }

  /* Yeni parola özeti üretir. Parola bu sayfadan dışarı çıkmaz. */
  function renderSetup() {
    const el = overlay(`
      <div class="brand" style="margin-bottom:10px">Parola özeti oluştur</div>
      <p class="small muted" style="margin-top:0">Parola bu tarayıcıda özetlenir ve hiçbir
        yere gönderilmez. Çıkan satırı Claude'a gönder; koda yalnızca özet yazılır.
        En az 12 karakter, başka yerde kullanmadığın bir parola seç.</p>
      <form id="setupForm">
        <input type="password" id="pw1" placeholder="Yeni parola" autocomplete="new-password" required minlength="12">
        <input type="password" id="pw2" placeholder="Tekrar" autocomplete="new-password" required minlength="12">
        <button class="primary" type="submit">Özeti oluştur</button>
        <p class="small bad-text" id="setupErr" role="alert" hidden></p>
      </form>
      <textarea id="setupOut" rows="3" readonly hidden></textarea>
      <button id="setupCopy" hidden>Kopyala</button>`);
    const $ = (id) => el.querySelector(`#${id}`);
    $('setupForm').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const err = $('setupErr');
      err.hidden = true;
      if ($('pw1').value !== $('pw2').value) {
        err.textContent = 'İki parola aynı değil.'; err.hidden = false; return;
      }
      try {
        const salt = hex(crypto.getRandomValues(new Uint8Array(16)));
        const hash = await derive($('pw1').value, salt, CONFIG.iterations);
        $('pw1').value = ''; $('pw2').value = '';
        $('setupOut').value = `P-Fin parola özeti: salt=${salt} hash=${hash} iterations=${CONFIG.iterations}`;
        $('setupOut').hidden = false; $('setupCopy').hidden = false;
      } catch (e) {
        err.textContent = e.message || String(e); err.hidden = false;
      }
    });
    $('setupCopy').addEventListener('click', () => {
      $('setupOut').select();
      try { navigator.clipboard.writeText($('setupOut').value); } catch (_) { document.execCommand('copy'); }
      $('setupCopy').textContent = 'Kopyalandı';
    });
  }

  /* Sekmeyi beklemeden kilitle (üst çubuktaki düğme). */
  function lock() {
    try { sessionStorage.removeItem(KEY); } catch (_) { /* yok say */ }
    location.reload();
  }

  return { gate, lock, configured, derive };
})();
