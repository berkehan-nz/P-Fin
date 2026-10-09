/* Biçimlendirme — panodaki her sayının TEK kaynağı.
 *
 * Hiçbir görünüm dosyası kendi sayı biçimini yazmaz. Aynı getiri bir
 * ekranda "+%1,4", diğerinde "+%1,31" görünüyordu; sebep her ekranın
 * kendi yuvarlamasını yapmasıydı.
 *
 *   money(2421.68)     → "$2.421,68"     (≥ 100.000 → "$123,4K")
 *   moneyTry(119489)   → "₺119.489"
 *   pct(1.31)          → "+%1,31"         (değişim: işaretli, 2 ondalık)
 *   share(22.4)        → "%22,4"          (pay/ağırlık: işaretsiz)
 *   delta(31.33, 1.31) → "+$31,33 · +%1,31"
 *   date("2026-10-09") → "9 Eki"          (başka yıl → "9 Eki 2025")
 *   days(21)           → "21 gün" / "yarın" / "bugün" / "3 gün önce"
 *   changeClass(-0.09) → ""               (|%| < 0,5 → renk yok)
 *
 * Eksi işareti gerçek eksi (U+2212): kısa çizgi rakamlara yapışık
 * okunuyor ve sütunlarda hizayı bozuyordu.
 *
 * Metrik renk eşikleri koda gömülü değildir — data/thresholds.json'dan gelir.
 */
window.Fmt = (function () {
  'use strict';

  const MINUS = '−';
  // Günlük hareketin bu eşiğin altında kalanı "gürültü" sayılır ve renk almaz.
  // 2 dolarlık bir gün kırmızı alarm gibi parlıyordu.
  const NOISE_PCT = 0.5;

  let TH = {};
  function setThresholds(t) { TH = t || {}; }
  function spec(metric) { return TH[metric] || null; }

  const isNum = (v) => v !== null && v !== undefined && typeof v === 'number' && isFinite(v);

  function num(v, digits = 2) {
    if (!isNum(v)) return '';
    const s = Math.abs(v).toLocaleString('tr-TR', { minimumFractionDigits: digits,
                                                    maximumFractionDigits: digits });
    return v < 0 && Number(s.replace(/\./g, '').replace(',', '.')) !== 0 ? MINUS + s : s;
  }

  function int(v) { return isNum(v) ? num(Math.round(v), 0) : ''; }

  function sign(v) {
    if (!isNum(v)) return '';
    const r = Math.round(v * 100) / 100;
    return r > 0 ? '+' : r < 0 ? MINUS : '';
  }

  /* Para. Varsayılan 2 ondalık. musd: milyon $ cinsinden gelen kart değerleri. */
  function money(v, { musd = false, digits = 2 } = {}) {
    if (!isNum(v)) return '';
    const neg = v < 0 ? MINUS : '';
    const a = Math.abs(v);
    if (musd) {
      if (a >= 1000) return `${neg}$${num(a / 1000, 1)} mr`;
      return `${neg}$${num(a, 0)} mn`;
    }
    if (a >= 100000) return `${neg}$${num(a / 1000, 1)}K`;
    const s = num(a, digits);
    return Number(s.replace(/\./g, '').replace(',', '.')) === 0 ? `$${s}` : `${neg}$${s}`;
  }

  function moneyTry(v) {
    if (!isNum(v)) return '';
    return `${v < 0 ? MINUS : ''}₺${num(Math.abs(v), 0)}`;
  }

  function signedMoney(v, digits = 2) {
    if (!isNum(v)) return '';
    const r = Math.abs(v) < 0.5 * Math.pow(10, -digits) ? 0 : v;
    return `${digits === 0 ? (Math.round(r) > 0 ? '+' : Math.round(r) < 0 ? MINUS : '') : sign(r)}${money(Math.abs(r), { digits })}`;
  }

  /* Değişim yüzdesi: işaret önde, yüzde işareti sayıdan önce. */
  function pct(v, digits = 2) {
    if (!isNum(v)) return '';
    return `${sign(v)}%${num(Math.abs(v), digits)}`;
  }

  /* Pay / ağırlık: işaretsiz. */
  function share(v, digits = 1) {
    if (!isNum(v)) return '';
    return `${v < 0 ? MINUS : ''}%${num(Math.abs(v), digits)}`;
  }

  function delta(usd, p) {
    const parts = [signedMoney(usd), pct(p)].filter(Boolean);
    return parts.join(' · ');
  }

  function changeClass(p) {
    if (!isNum(p) || Math.abs(p) < NOISE_PCT) return '';
    return p > 0 ? 'up' : 'down';
  }

  /* K/Z rengi tutar için: yüzde biliniyorsa onun eşiği kullanılır. */
  function pnlClass(p) { return changeClass(p); }

  function parseDay(d) {
    if (!d) return null;
    const s = String(d);
    const x = new Date(s.length <= 10 ? `${s}T12:00:00` : s);
    return isNaN(x) ? null : x;
  }

  function date(d) {
    const x = parseDay(d);
    if (!x) return '';
    const same = x.getFullYear() === new Date().getFullYear();
    return x.toLocaleDateString('tr-TR', same
      ? { day: 'numeric', month: 'short' }
      : { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function dateTime(iso) {
    const x = parseDay(iso);
    if (!x) return '';
    return `${date(iso)} ${x.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}`;
  }

  function daysUntil(d) {
    const x = parseDay(d);
    if (!x) return null;
    const t = new Date(); t.setHours(12, 0, 0, 0);
    x.setHours(12, 0, 0, 0);
    return Math.round((x - t) / 86400000);
  }

  function days(n) {
    if (!isNum(n)) return '';
    if (n === 0) return 'bugün';
    if (n === 1) return 'yarın';
    if (n === -1) return 'dün';
    if (n < 0) return `${Math.abs(n)} gün önce`;
    return `${n} gün`;
  }

  function hoursSince(iso) {
    const x = parseDay(iso);
    return x ? (Date.now() - x.getTime()) / 36e5 : null;
  }

  function sinceLabel(iso) {
    const h = hoursSince(iso);
    if (h === null) return '';
    if (h < 1) return `${Math.max(1, Math.round(h * 60))} dakika önce`;
    if (h < 24) return `${Math.round(h)} saat önce`;
    return `${Math.round(h / 24)} gün önce`;
  }

  /* VERİDEN GELEN METİN. Python tarafı (sistem ayarları ve mesajlar) henüz
     Türkçe karakter kullanmıyor ("çekirdek" yerine c ile, "toplantısı"
     yerine ı'sız). Kalıcı çözüm orada; bu sözlük yalnızca panoda sık görünen
     kelimeleri düzeltir. Sözlük doğru yazımdan TÜRETİLİR (aksanlar atılarak),
     bilinmeyen kelimeye dokunulmaz — yanlış düzeltmektense olduğu gibi bırakır. */
  const DEACCENT = { ç: 'c', ğ: 'g', ı: 'i', İ: 'I', ö: 'o', ş: 's', ü: 'u', â: 'a',
                     Ç: 'C', Ğ: 'G', Ö: 'O', Ş: 'S', Ü: 'U' };
  const plainOf = (w) => w.replace(/[çğıİöşüâÇĞÖŞÜ]/g, (c) => DEACCENT[c]);
  const TR_WORDS = (
    'Altın Bilanço Borç Brüt Büyük Büyüme Cari Değerleme Düşük Elendi FAVÖK FVÖK Faaliyet'
    + ' '
    + 'Faiz GEÇTİ Göreli Hasılat Kalite Katalizör Kayıt Kazanç Kuralı Kâr Kârlılık Küçük'
    + ' '
    + 'Nakit Net Perakende Piyasa Sanayi Sağlamlık Serbest Sert Seyrelme Tuzak TÜFE Ucuzluk'
    + ' '
    + 'Yüksek Yıllık akışı altı altında alım alımlar alımı aralıkta artışı açılan ağırlık'
    + ' '
    + 'ağırlığı başa başlangıç başlıyor bilanço bilgi borç brüt büyüme büyümesi değeri'
    + ' '
    + 'değerleme doğru doğrudan dönüşüm dönüşümü düşük eksik eleme endeksi getirisi geçirme'
    + ' '
    + 'geçti giriş göreli görünür gözden gün günde günü hasılat hazırlık hesabına hisse için'
    + ' '
    + 'işgücü işletme kararı karşılama kazanç kesinleşmemiş kuralı kâr kârlı kârlılığı küçük'
    + ' '
    + 'kırıcı kırıcılar marj marjı mevduat olarak oran pahalı parça parçası planlı sapma'
    + ' '
    + 'satışlar satışları sağlamlık sermaye seçim seçimi tahvil tarihi toplantısı ucuz ve'
    + ' '
    + 'verimi yenileme yüksek yıllık Çekirdek Önemli Özkaynak çapası çeyrekte önce üretim'
    + ' '
    + 'üretimi üstü üstünde İstihdam İşletme İşsizlik Şirket Şirketin şirket şirketin'
    + ' '
    + 'şirketler'
  ).split(/\s+/).filter(Boolean);
  const WORDS = {};
  TR_WORDS.forEach((w) => { WORDS[plainOf(w)] = w; });
  WORDS.URFE = 'ÜFE';
  const PHRASES = {};
  [
    'Basım ve yayın',
    'Diğer iş hizmetleri',
    'Eğitim',
    'Gıda ve tütün',
    'Kauçuk, plastik, cam',
    'Kimya ve ilaç',
    'Makine ve bilgisayar donanımı',
    'Motor (tek hisse)',
    'Mühendislik ve araştırma',
    'Nakit (USD)',
    'SGOV (nakit çapası)',
    'Sağlık hizmetleri',
    'Ulaştırma',
    'Ulaşım ekipmanı',
    'Veri işleme ve sistem entegrasyonu',
    'Yazılım ve programlama',
    'Çeşitli imalat',
    'Ölçüm ve tıbbi cihaz',
    'İletişim',
    'İş hizmetleri'
  ].forEach((t) => { PHRASES[plainOf(t)] = t; });
  function tr(s) {
    if (s === null || s === undefined) return '';
    const str = String(s);
    if (PHRASES[str]) return PHRASES[str];
    return str.replace(/[A-Za-z]+/g, (w) => (Object.prototype.hasOwnProperty.call(WORDS, w) ? WORDS[w] : w));
  }

  /* Dilim ve faz adları: anahtardan, veriden bağımsız. */
  const SLICE = {
    motor: 'Motor (tek hisse)', cekirdek_etf: 'Çekirdek ETF', sgov: 'SGOV',
    tl: 'TL mevduat', nakit: 'Nakit',
  };
  function sliceLabel(key, fallback) { return SLICE[key] || tr(fallback || key); }

  const PHASE = { faz0: 'Faz 0 · hazırlık', faz1: 'Faz 1 · ilk hisseler', faz2: 'Faz 2 · tam motor' };
  function phaseLabel(ph) { return (ph && PHASE[ph.key]) || tr((ph && ph.label) || ''); }

  /* ---------------------------------------------------------- metrikler */
  function pctText(v, digits = 1) {
    return `${v < 0 ? MINUS : ''}%${num(Math.abs(v), digits)}`;
  }

  function metricValue(metric, v) {
    if (!isNum(v)) return '';
    const s = spec(metric);
    const unit = s ? s.unit : '';
    if (unit === '%') return pctText(v, 1);
    if (unit === 'x') return `${num(v, Math.abs(v) >= 100 ? 0 : 1)}x`;
    if (unit === '/9') return `${Math.round(v)}/9`;
    return num(v, Math.abs(v) >= 100 ? 0 : 2);
  }

  function colorFor(metric, v) {
    if (!isNum(v)) return 'na';
    const s = spec(metric);
    if (!s) return 'na';
    if (s.direction === 'low_good') {
      if (v <= s.green_max) return 'good';
      if (v <= s.yellow_max) return 'warn';
      return 'bad';
    }
    if (v >= s.green_min) return 'good';
    if (v >= s.yellow_min) return 'warn';
    return 'bad';
  }

  /* Kartlardaki renk adları (green/yellow/red/gray) → anlam adları. */
  function status(color) {
    return { green: 'good', yellow: 'warn', red: 'bad', gray: 'na' }[color] || color || 'na';
  }

  function statusText(st) {
    return { good: 'iyi', warn: 'sınırda', bad: 'zayıf', na: '' }[st] || '';
  }

  function label(metric) {
    const s = spec(metric);
    return tr(s ? s.label : metric);
  }

  function plain(metric) {
    const s = spec(metric);
    return s && s.plain ? tr(s.plain) : '';
  }

  function sentence(metric, v) {
    const s = spec(metric);
    if (!s || !s.sentence || !isNum(v)) return '';
    const unit = s.unit;
    const shown = (unit === '%' || (v < 0 && s.sentence_neg))
                ? num(Math.abs(v), unit === '%' ? 1 : 2)
                : unit === '/9' ? String(Math.round(v))
                : num(v, Math.abs(v) >= 100 ? 0 : 2);
    if (v < 0) {
      if (s.sentence_neg) return tr(s.sentence_neg.replace('{v}', shown));
      return tr(s.sentence.replace('{v}', unit === '%' ? num(v, 1) : shown));
    }
    return tr(s.sentence.replace('{v}', shown));
  }

  const VALUATION_METRICS = ['ev_ebit', 'ev_ebitda', 'ev_gross_profit', 'ev_sales',
                             'pe', 'peg', 'implied_growth', 'implied_vs_actual_growth'];

  function percentileSentence(metric, p, basis) {
    if (!isNum(p)) return '';
    const s = spec(metric);
    const where = basis === 'universe' ? 'tüm şirketler içinde' : 'sektöründe';
    const rank = Math.round(p);
    const lowIsGood = s && s.direction === 'low_good';
    if (lowIsGood && VALUATION_METRICS.indexOf(metric) !== -1) {
      if (rank <= 25) return `${where} en ucuz %${rank}`;
      if (rank <= 50) return `${where} ortalamadan ucuz`;
      if (rank <= 75) return `${where} ortalamadan pahalı`;
      return `${where} en pahalı %${100 - rank}`;
    }
    if (lowIsGood) {
      if (rank <= 25) return `${where} en iyi %${rank}`;
      if (rank <= 50) return `${where} ortalamadan iyi`;
      if (rank <= 75) return `${where} ortalamadan zayıf`;
      return `${where} en zayıf %${100 - rank}`;
    }
    if (rank >= 75) return `${where} en iyi %${100 - rank}`;
    if (rank >= 50) return `${where} ortalamadan iyi`;
    if (rank >= 25) return `${where} ortalamadan zayıf`;
    return `${where} en zayıf %${rank}`;
  }

  function ownHistorySentence(metric, p) {
    if (!isNum(p)) return '';
    const s = spec(metric);
    const lowIsGood = s && s.direction === 'low_good';
    const rank = Math.round(p);
    if (lowIsGood && VALUATION_METRICS.indexOf(metric) !== -1) {
      if (rank <= 20) return `son 5 yılının en ucuz %${rank}'inde`;
      if (rank <= 45) return 'kendi geçmişine göre ucuz';
      if (rank <= 55) return '5 yıllık ortalaması civarında';
      if (rank <= 80) return 'kendi geçmişine göre pahalı';
      return `son 5 yılının en pahalı %${100 - rank}'inde`;
    }
    if (rank >= 80) return `son 5 yılının en iyi %${100 - rank}'inde`;
    if (rank >= 55) return 'kendi geçmişine göre iyi';
    if (rank >= 45) return '5 yıllık ortalaması civarında';
    if (rank >= 20) return 'kendi geçmişine göre zayıf';
    return `son 5 yılının en zayıf %${rank}'inde`;
  }

  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* Rozetler — tek stil, gri. Renk yalnızca uyarı (warn/bad). */
  function badge(text, kind) {
    return `<span class="badge${kind ? ' ' + kind : ''}">${esc(text)}</span>`;
  }

  function decisionBadge(action) {
    if (!action) return '';
    return badge(action, 'decision');
  }

  function trackLabel(track) {
    return { A: 'Kârlı', B: 'Büyüyen', both: 'Kârlı ve büyüyen' }[track] || '';
  }

  return {
    MINUS, NOISE_PCT, setThresholds, spec, isNum, num, int, money, moneyTry, signedMoney,
    pct, share, delta, changeClass, pnlClass, date, dateTime, days, daysUntil, hoursSince,
    sinceLabel, tr, sliceLabel, phaseLabel, pctText, metricValue, colorFor, status,
    statusText, label, plain, sentence, percentileSentence, ownHistorySentence, esc, badge,
    decisionBadge, trackLabel,
  };
})();
