/* 6. NASIL OKUNUR — sistemin mantigi ve terim sozlugu.
 *
 * Sozluk data/thresholds.json'dan uretilir; yani config.py'yi degistirince
 * bu sayfa da kendiliginden guncellenir. Elle yazilmis ikinci bir liste
 * tutmuyoruz — bayatlar.
 */
window.ViewGuide = (function () {
  'use strict';

  function render() {
    const th = App.thresholds || {};
    const T = th.thresholds || {};
    const blocks = th.metric_blocks || {};
    const scores = th.score_plain || {};
    const s1 = th.stage1 || {};

    document.getElementById('guideBody').innerHTML = `
      ${howItWorks()}
      ${scoreGuide(scores)}
      ${colorGuide()}
      ${percentileGuide()}
      ${glossary(T, blocks)}
      ${funnelGuide(s1)}
    `;
  }

  function howItWorks() {
    return `<h2>Sistem ne yapiyor</h2>
      <div class="card">
        <p>Amac: <b>1-2 yil icinde yeniden fiyatlanabilecek</b> ABD hisselerini
          bulmak. Yani bugun ucuz duran ama isi aslinda iyi olan sirketleri.</p>
        <ol style="line-height:1.9;padding-left:20px">
          <li><b>Evren:</b> ABD borsalarindaki binlerce sirket. Finans,
            gayrimenkul ve hasilatsiz biyoteknoloji disarida.</li>
          <li><b>Sert filtreler:</b> marji dusuk, buyumeyen, cok borclu ya da
            hisse sayisini hizla artiran sirketler elenir.</li>
          <li><b>Tuzak eleme:</b> muhasebesi supheli, iflas riski tasiyan ya da
            kari nakde donmeyen sirketler elenir. <b>Ucuz olmak yetmez —
            ucuz olmasinin bir sebebi olabilir.</b></li>
          <li><b>Goreli ucuzluk:</b> kalanlar hem kendi sektorune hem kendi
            gecmisine gore ucuz mu diye bakilir.</li>
          <li><b>Puanlama:</b> ilk 50 sirket puanlanir ve karta donusur.</li>
        </ol>
        <p class="small muted">Sistem <b>karar vermez</b>, aday uretir. Karari
          sen verirsin; sirket sayfasindaki karar kutusu bunu kaydeder.</p>
      </div>`;
  }

  function scoreGuide(scores) {
    const order = ['total', 'value', 'quality', 'safety', 'momentum',
                   'earnings_quality', 'catalyst'];
    return `<h2>Puanlar</h2>
      <div class="card">
        <p class="small">Butun puanlar <b>0-100</b> arasidir ve <b>ayni sektordeki
          diger sirketlere gore</b> hesaplanir. 70 puan "mutlak olarak iyi"
          degil, <b>"sektorun en iyi %30'unda"</b> demektir. Yazilimda %70 brut
          marj normalken perakendede olaganustudur; bu yuzden mutlak esik
          kullanmiyoruz.</p>
        <div class="table-wrap" style="margin-top:10px"><table>
          <thead><tr><th>Puan</th><th style="text-align:left">Ne olcuyor</th></tr></thead>
          <tbody>${order.filter((k) => scores[k]).map((k) => `<tr>
            <td><b>${Fmt.esc(scores[k][0])}</b></td>
            <td style="text-align:left;white-space:normal;line-height:1.5">
              ${Fmt.esc(scores[k][1])}</td></tr>`).join('')}</tbody>
        </table></div>
        <p class="tiny dim" style="margin-top:8px">Bir puan hesaplanamazsa
          sifir sayilmaz — agirlik havuzundan cikarilir ve kalanlar yeniden
          dengelenir. Kartta "puanin yuzde kaci hesaplanabildi" yazar.</p>
      </div>`;
  }

  function colorGuide() {
    return `<h2>Renkler</h2>
      <div class="card">
        <div class="row" style="gap:10px;margin-bottom:8px">
          <span class="chip green"><span class="arrow">▲</span> yesil</span> iyi
          <span class="chip yellow"><span class="arrow">◆</span> sari</span> sinirda
          <span class="chip red"><span class="arrow">▼</span> kirmizi</span> kotu
          <span class="chip gray">gri</span> veri yok
        </div>
        <p class="small">Renk korlugu icin her hucre renge <b>ek olarak</b> bir
          yon oku ve ince bir doluluk cubugu tasir; bilgi yalnizca renkle
          tasinmaz.</p>
        <p class="small"><b>Ok degerin YERINI gosterir, iyi/kotu oldugunu degil:</b>
          ▲ deger yuksek, ▼ deger dusuk. Iyi mi kotu mu oldugunu RENK soyler.
          Ornek: EV/FVOK'ta <span class="chip red"><span class="arrow">▲</span>28,9x</span>
          "carpan yuksek, bu kotu" demek; brut marjda
          <span class="chip green"><span class="arrow">▲</span>%79</span>
          "marj yuksek, bu iyi" demek. Ayni ok, zit anlam — cunku birinde
          dusuk, digerinde yuksek olmak iyidir.</p>
        <p class="small"><b>Gri kirmizi degildir.</b> Veri yoklugu kotu haber
          anlamina gelmez; o kalem SEC dosyasinda bulunamamis demektir.</p>
      </div>`;
  }

  function percentileGuide() {
    return `<h2>"Sektorde nerede" ve "Kendi gecmisine gore"</h2>
      <div class="card">
        <p class="small">Bir carpanin tek basina anlami yoktur. 15x pahali mi
          ucuz mu? Cevap iki referansa bagli:</p>
        <p class="small"><b>Sektorde nerede:</b> ayni SIC sektor grubundaki diger
          sirketlere gore siralamasi. "En ucuz %20'lik dilimde" demek,
          sektordeki her 5 sirketten 4'u bundan pahali demek.</p>
        <p class="small"><b>Kendi gecmisine gore:</b> bu sirketin <b>son 5 yildaki
          kendi</b> degerlerine gore bugun nerede durdugu. Her ceyrek sonu icin
          o gunku fiyatla carpan yeniden hesaplanir ve bugunku deger bu
          dagilimda siralanir.</p>
        <div class="warn medium" style="margin-top:10px"><span>💡</span><span>
          <b>Ikisi birlikte okunur.</b> Sektorde ucuz ama kendi gecmisine gore
          pahaliysa, muhtemelen sektorun tamami ucuzlamistir — sirkete ozel bir
          firsat yoktur. Tersi de dogru: kendi gecmisine gore cok ucuz ama
          sektorde ortalamaysa, sirkete ozel bir sey olmus demektir.</span></div>
        <p class="tiny dim" style="margin-top:8px">Yildizli (*) yuzdelikler,
          sektorde yeterli sirket olmadigi icin tum evrene gore hesaplanmistir.</p>
      </div>`;
  }

  function glossary(T, blocks) {
    const order = ['Degerleme', 'Buyume', 'Kalite', 'Saglamlik ve Tuzak'];
    return `<h2>Terim sozlugu</h2>
      <p class="small muted">Panodaki her metrik. Esikler
        <code>src/config.py</code> dosyasindan gelir.</p>
      ${order.filter((b) => blocks[b]).map((block) => `
        <h3>${Fmt.esc(block)}</h3>
        <div class="table-wrap"><table>
          <thead><tr>
            <th style="min-width:150px">Terim</th>
            <th style="text-align:left;min-width:260px">Ne demek</th>
            <th style="text-align:left;min-width:200px">Formul</th>
            <th style="text-align:left;min-width:200px">Esikler</th>
          </tr></thead>
          <tbody>${blocks[block].map((k) => {
            const s = T[k] || {};
            const esik = s.direction === 'low_good'
              ? `yesil ≤ ${s.green_max} · sari ≤ ${s.yellow_max} · ustu kirmizi`
              : `yesil ≥ ${s.green_min} · sari ≥ ${s.yellow_min} · alti kirmizi`;
            return `<tr>
              <td><b>${Fmt.esc(s.label || k)}</b>
                <div class="tiny dim">${Fmt.esc(s.unit_name || '')}</div></td>
              <td style="text-align:left;white-space:normal;line-height:1.5">
                ${Fmt.esc(s.plain || '')}
                <div class="tiny dim" style="margin-top:4px">${Fmt.esc(s.help || '')}</div></td>
              <td style="text-align:left;white-space:normal">
                <code class="tiny">${Fmt.esc(s.formula || '')}</code></td>
              <td style="text-align:left;white-space:normal" class="tiny">
                ${Fmt.esc(esik)}</td></tr>`; }).join('')}
          </tbody></table></div>`).join('')}`;
  }

  function funnelGuide(s1) {
    return `<h2>Filtre esikleri</h2>
      <div class="card">
        <p class="small">Bir sirketin elenmesi icin bu esiklerden <b>birini bile</b>
          gecememesi yeterli:</p>
        <ul class="small" style="line-height:1.8;padding-left:20px">
          <li>Brut marj <b>%${s1.gross_margin_min_pct}</b> ustunde olmali —
            altinda fiyatlama gucu yok demektir</li>
          <li>Satis buyumesi <b>%${s1.rev_growth_ttm_min_pct}</b> ustunde olmali</li>
          <li>Serbest nakit pozitif olmali <i>veya</i> buyume
            <b>%${s1.high_growth_exemption_growth_pct}</b> ustunde <b>ve</b>
            40 Kurali <b>${s1.high_growth_exemption_rule40_min}</b> ustunde olmali</li>
          <li>Net borc, FAVOK'un <b>${s1.net_debt_to_ebitda_max}</b> katindan az olmali</li>
          <li>Hisse sayisi artisi <b>%${s1.share_count_growth_max_pct}</b> altinda olmali —
            uzerinde seyrelme, senin payini buyumeden hizli eritir</li>
          <li>Calisana verilen hisse, uretilen nakdin <b>${s1.sbc_to_fcf_max}</b>
            katini gecmemeli — gecerse uretilen tum nakit calisana gidiyor demektir</li>
        </ul>
        <div class="warn low" style="margin-top:10px"><span>ℹ</span><span>
          <b>Veri yoklugu eleme sebebi degildir.</b> Bir kalem SEC dosyasinda
          bulunamazsa sirket elenmez, isaretlenir. Muhasebe etiketleme bicimine
          gore eleme yapmak gorunmez bir yanlilik yaratirdi.</span></div>
      </div>`;
  }

  return { render };
})();
