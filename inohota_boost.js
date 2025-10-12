
// inohota_boost.js
// - 「本日の注目章」自動表示
// - 追従ミニ商品カード（最小化/閉じる/フッター退避/日内抑止）

(function(){
  // ===== 設定（必要に応じて編集） =====
  const COVER_SRC = "../lib/inohotanaze_front_cover_small.jpg"; // 書影（フォールバック）
  const AMAZON_URL = "https://amzn.to/4nmDn6Y";
  const RAKUTEN_URL = "https://books.rakuten.co.jp/rb/18326943/";
  const SHOW_THRESHOLD = 0.30; // 30% スクロールで表示
  const STORAGE_KEY_CLOSED = "fp_closed_date";

  // ===== 日付ユーティリティ =====
  function todayKeyDate(){
    const d = new Date();
    d.setHours(0,0,0,0);
    return d;
  }

  // ====== 「本日の注目章」 ======
  function pickIndex(len){
    // UTC基準で安定日替わり
    const epoch = Date.UTC(2025,0,1);
    const now = new Date();
    const todayUTC = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    const days = Math.floor((todayUTC - epoch) / 86400000);
    return ((days % len) + len) % len;
  }

  function ensureTodaysPick(){
    // 既にセクションがない場合は作る
    let section = document.getElementById("todays-pick");
    if (!section){
      section = document.createElement("section");
      section.id = "todays-pick";
      section.className = "section card";
      section.innerHTML = '<h2 style="text-align:center;">本日の注目章</h2><div id="todays-pick-card" class="topic-card" style="max-width:680px;margin:0 auto;"></div>';
      // #about の前か、.containerの最上部に差し込み
      const about = document.getElementById("about");
      if (about && about.parentNode){
        about.parentNode.insertBefore(section, about);
      } else {
        const main = document.querySelector("main.container") || document.querySelector(".container");
        if (main) main.prepend(section);
      }
    }

    const host = document.getElementById("todays-pick-card");
    if (!host) return;

    const allCards = Array.from(document.querySelectorAll(".topics-grid .topic-card"));
    if (!allCards.length) return;

    const idx = pickIndex(allCards.length);
    const pick = allCards[idx].cloneNode(true);
    const h3 = pick.querySelector("h3");
    if (h3) h3.style.fontSize = "1.25rem";

    host.innerHTML = "";
    host.appendChild(pick);
  }

  // ===== 追従ミニ商品カード =====
  function buildFollowCard(){
    if (document.getElementById("followProduct")) return; // 二重生成防止
    const div = document.createElement("div");
    div.id = "followProduct";
    div.className = "follow-product";
    div.setAttribute("aria-live", "polite");
    div.innerHTML = `
      <div class="follow-product__controls">
        <button class="follow-product__iconbtn" id="fpMinBtn" title="最小化">—</button>
        <button class="follow-product__iconbtn" id="fpCloseBtn" title="非表示">×</button>
      </div>

      <div class="follow-product__header">
        <img src="${COVER_SRC}" alt="書影" class="follow-product__thumb">
        <div class="follow-product__title">言語学でスッキリ解決！英語の「なぜ？」（ナツメ社）</div>
      </div>

      <div class="follow-product__actions">
        <a href="${AMAZON_URL}" target="_blank" class="follow-product__btn follow-product__btn--amazon">Amazonで見る</a>
        <a href="${RAKUTEN_URL}" target="_blank" class="follow-product__btn follow-product__btn--rakuten">楽天で見る</a>
      </div>

      <div class="follow-product__meta">スクロールで自動表示。×で今日だけ非表示にできます。</div>
    `;
    document.body.appendChild(div);
    return div;
  }

  function followCardController(el){
    if (!el) return;
    const today = todayKeyDate();
    const closed = localStorage.getItem(STORAGE_KEY_CLOSED);
    if (closed && new Date(closed).getTime() === today.getTime()) {
      // 今日閉じている
      return;
    }

    let isMin = false;
    const minBtn = el.querySelector("#fpMinBtn");
    const closeBtn = el.querySelector("#fpCloseBtn");
    minBtn.addEventListener("click", () => {
      isMin = !isMin;
      el.classList.toggle("follow-product--min", isMin);
    });
    closeBtn.addEventListener("click", () => {
      el.style.display = "none";
      localStorage.setItem(STORAGE_KEY_CLOSED, today.toISOString()); // 今日だけ抑止
      window.removeEventListener("scroll", onScroll, { passive: true });
    });

    // 30%スクロールで表示
    function maybeShow() {
      const scrolled = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;
      if (scrolled > SHOW_THRESHOLD) {
        el.style.display = "block";
        window.removeEventListener("scroll", onScroll);
      }
    }
    function onScroll(){
      if (onScroll._t) return;
      onScroll._t = requestAnimationFrame(() => {
        maybeShow();
        onScroll._t = null;
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });

    // フッター干渉回避
    const footer = document.querySelector("footer");
    if (footer && "IntersectionObserver" in window) {
      const obs = new IntersectionObserver(entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            el.style.bottom = "160px";
          } else {
            el.style.bottom = "100px";
          }
        });
      }, {rootMargin: "0px", threshold: 0.01});
      obs.observe(footer);
    }
  }

  // ===== 実行 =====
  document.addEventListener("DOMContentLoaded", function(){
    try { ensureTodaysPick(); } catch(e){ console.warn(e); }
    try { followCardController(buildFollowCard()); } catch(e){ console.warn(e); }
  });
})();
