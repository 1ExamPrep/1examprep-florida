/* Exam Path motion, filters and the exam path picker. Every word of content is in the HTML;
   the picker reads /assets/finder.json, which build.py writes from the same Shopify data. */
(function () {
  var d = document, root = d.documentElement;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("js");

  d.addEventListener("DOMContentLoaded", function () {
    /* reveal on scroll, with a small stagger for cards in the same row */
    var els = [].slice.call(d.querySelectorAll(".reveal"));
    if (!("IntersectionObserver" in window) || reduce) {
      els.forEach(function (el) { el.classList.add("in"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        var i = 0;
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.style.transitionDelay = Math.min(i++ * 60, 360) + "ms";
            en.target.classList.add("in");
            io.unobserve(en.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      els.forEach(function (el) { io.observe(el); });
    }

    /* count-up numbers */
    var nums = [].slice.call(d.querySelectorAll("[data-count]"));
    function fmt(n, el) { return (el.dataset.prefix || "") + Math.round(n).toLocaleString("en-US") + (el.dataset.suffix || ""); }
    function run(el) {
      var end = +el.dataset.count, t0 = null, dur = 1400;
      function tick(t) {
        if (!t0) t0 = t;
        var p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(end * e, el);
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }
    if (!reduce && "IntersectionObserver" in window) {
      var co = new IntersectionObserver(function (en) {
        en.forEach(function (x) { if (x.isIntersecting) { run(x.target); co.unobserve(x.target); } });
      }, { threshold: 0.6 });
      nums.forEach(function (n) { co.observe(n); });
    }

    /* header shrink, hero parallax, timeline progress */
    var top = d.querySelector("[data-shrink]");
    var hero = d.querySelector("[data-parallax]");
    var tl = d.querySelector("[data-timeline]");
    var ticking = false;
    function onScroll() {
      var y = window.scrollY;
      if (top) top.classList.toggle("small", y > 40);
      if (hero && !reduce && y < 1000) hero.style.transform = "translate3d(0," + (y * 0.25).toFixed(1) + "px,0)";
      if (tl) {
        var r = tl.getBoundingClientRect(), vh = window.innerHeight;
        var p = Math.max(0, Math.min(1, (vh * 0.75 - r.top) / r.height));
        tl.style.setProperty("--p", p.toFixed(3));
      }
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
    }, { passive: true });
    onScroll();


    /* license finder on the home page */
    var input = d.getElementById("finder");
    if (input) {
      var cards = [].slice.call(d.querySelectorAll(".ccard"));
      var groups = [].slice.call(d.querySelectorAll("[data-group]"));
      var none = d.querySelector(".no-match");
      var q0 = new URLSearchParams(location.search).get("q");
      if (q0) input.value = q0;
      var filter = function () {
        var q = input.value.trim().toLowerCase(), shown = 0;
        cards.forEach(function (c) {
          var hit = !q || c.dataset.name.indexOf(q) > -1;
          c.classList.toggle("hide", !hit);
          if (hit) { shown++; c.classList.add("in"); }
        });
        groups.forEach(function (g) { g.classList.toggle("hide", !g.querySelector(".ccard:not(.hide)")); });
        if (none) none.hidden = shown > 0;
      };
      input.addEventListener("input", filter);
      input.form.addEventListener("submit", function (ev) {
        ev.preventDefault(); filter();
        var t = d.getElementById("find-your-license"); if (t) t.scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
      });
      if (q0) filter();
    }


    /* exam path picker (home hero): license type -> category -> recommendation */
    var form = d.getElementById("path-form");
    if (form) {
      var data = null, lic = form.dataset.start, choice = "books-course";
      var gsel = d.getElementById("path-group");
      var box = form.querySelector(".lchips");
      var lchipEls = [].slice.call(form.querySelectorAll(".lchip"));
      var segs = [].slice.call(form.querySelectorAll(".seg"));
      var out = form.querySelector(".p-result");
      var nameEl = form.querySelector("[data-licname]");
      var MORE = +(box.dataset.moreAt || 5);
      var money = function (x) {
        if (!x) return "Free";
        return "$" + (Math.round(x) === x ? x.toLocaleString("en-US") : x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
      };
      var esc = function (s) { var t = d.createElement("span"); t.textContent = s; return t.innerHTML; };
      var ICON_CHECK = '<svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';
      form.addEventListener("submit", function (ev) { ev.preventDefault(); });
      var load = function (cb) {
        if (data) return cb();
        fetch("/assets/finder.json").then(function (r) { return r.json(); }).then(function (j) { data = j; cb(); }).catch(function () {});
      };
      var find = function (id) { for (var i = 0; i < data.licenses.length; i++) if (data.licenses[i].id === id) return data.licenses[i]; return null; };
      var moreBtn = d.createElement("button");
      moreBtn.type = "button"; moreBtn.className = "lchip more"; moreBtn.textContent = "More";
      moreBtn.addEventListener("click", function () {
        lchipEls.forEach(function (c) { if (c.dataset.g === gsel.value) c.hidden = false; });
        moreBtn.hidden = true;
      });
      box.appendChild(moreBtn);
      var showGroup = function (g, keep) {
        var n = 0, inGroup = 0;
        lchipEls.forEach(function (c) {
          var mine = c.dataset.g === g;
          if (mine) inGroup++;
          c.hidden = !mine || (n >= MORE && !(keep && c.dataset.lic === lic));
          if (mine) n++;
        });
        moreBtn.hidden = inGroup <= MORE;
      };
      var render = function () {
        var L = find(lic);
        if (!L) return;
        nameEl.textContent = L.n;
        segs.forEach(function (s) { s.disabled = !L.ch[s.dataset.choice]; });
        if (!L.ch[choice]) {
          var order = ["books-course", "books", "course", "everything", "free"];
          for (var i = 0; i < order.length; i++) if (L.ch[order[i]]) { choice = order[i]; break; }
        }
        segs.forEach(function (s) { s.classList.toggle("on", s.dataset.choice === choice); });
        var pair = L.ch[choice];
        if (!pair) { out.innerHTML = '<p class="r-empty">No package for this license yet. Call (877) 775-9400.</p>'; return; }
        var p = data.products[pair[0]], a = pair[1] != null ? data.products[pair[1]] : null;
        var inc = (p.inc || []).slice(0, 3).concat(a ? [L.pn + " prep added"] : []);
        var img = p.i ? '<img src="' + esc(p.i) + '" alt="' + esc(p.t) + '" width="120" height="120" loading="lazy">' : "";
        var html = '<div class="r-body"><div class="r-img">' + img + '</div><ul class="r-list2">' +
          inc.map(function (x) { return "<li>" + ICON_CHECK + esc(x) + "</li>"; }).join("") + "</ul></div>";
        if (a) html += '<label class="r-add"><input type="checkbox" checked data-add> Include <a href="' + a.u + '">' + esc(a.t) + "</a> (+" + money(a.p) + ")</label>";
        html += '<div class="r-foot"><div><p class="r-name"><a href="' + p.u + '">' + esc(p.t) + '</a></p><p class="r-sub">' + esc(p.k) + (a ? " + " + esc(L.pn) : "") +
          '</p></div><p class="r-price" data-total></p></div><a class="btn go" data-buy rel="nofollow" href="#">Get my recommended package</a>';
        out.innerHTML = html;
        bind(p, a);
      };
      var bind = function (p, a) {
        var cb = out.querySelector("[data-add]"), buy = out.querySelector("[data-buy]"), tot = out.querySelector("[data-total]");
        var upd = function () {
          var withAdd = a && cb && cb.checked;
          tot.textContent = money(p.p + (withAdd ? a.p : 0));
          buy.href = "https://1examprep.com/cart/" + p.v + ":1" + (withAdd ? "," + a.v + ":1" : "");
        };
        if (cb) cb.addEventListener("change", upd);
        upd();
      };
      showGroup(gsel.value, true);
      /* first paint is server-rendered; swap in the live version (same markup) once the data arrives */
      load(render);
      gsel.addEventListener("change", function () {
        showGroup(gsel.value, false);
        var first = lchipEls.filter(function (c) { return c.dataset.g === gsel.value; })[0];
        if (first) first.click();
      });
      lchipEls.forEach(function (c) {
        c.addEventListener("click", function () {
          lic = c.dataset.lic;
          lchipEls.forEach(function (x) { x.classList.toggle("on", x === c); });
          load(render);
        });
      });
      segs.forEach(function (s) {
        s.addEventListener("click", function () { choice = s.dataset.choice; load(render); });
      });
      var go = d.querySelector("[data-focus-picker]");
      if (go) go.addEventListener("click", function () { setTimeout(function () { gsel.focus({ preventScroll: true }); }, 400); });
      var q1 = new URLSearchParams(location.search).get("license");
      if (q1) {
        load(function () {
          var L = find(q1);
          if (!L) return;
          gsel.value = L.g; showGroup(L.g, false);
          lchipEls.forEach(function (c) { if (c.dataset.lic === q1) { c.hidden = false; c.click(); } });
        });
      }
    }

    /* contact form: the iframe and its script are added here so the served HTML has no iframe or body script */
    var fe = d.querySelector(".form-embed");
    if (fe) {
      var id = fe.dataset.formId;
      var fr = d.createElement("iframe");
      fr.src = "https://app.1examprep.com/widget/form/" + id;
      fr.id = "inline-" + id;
      fr.title = fe.dataset.formName;
      fr.style.cssText = "width:100%;height:" + fe.dataset.height + "px;border:none;border-radius:8px";
      var attrs = {
        "data-layout": "{'id':'INLINE'}", "data-trigger-type": "alwaysShow", "data-trigger-value": "",
        "data-activation-type": "alwaysActivated", "data-activation-value": "",
        "data-deactivation-type": "neverDeactivate", "data-deactivation-value": "",
        "data-form-name": fe.dataset.formName, "data-height": fe.dataset.height,
        "data-layout-iframe-id": "inline-" + id, "data-form-id": id,
        "data-cookie-consent": "true", "data-cookie-consent-provider": "auto"
      };
      Object.keys(attrs).forEach(function (k) { fr.setAttribute(k, attrs[k]); });
      fr.addEventListener("load", function () { fe.classList.add("loaded"); });
      fe.appendChild(fr);
      var sc = d.createElement("script");
      sc.src = "https://app.1examprep.com/js/form_embed.js";
      sc.async = true;
      d.body.appendChild(sc);
    }

    /* hero photo wall: double each track for a seamless loop */
    [].slice.call(d.querySelectorAll(".wall-track")).forEach(function (t) { t.innerHTML += t.innerHTML; });

    /* package-type chips on license pages */
    var chips = [].slice.call(d.querySelectorAll(".chip"));
    chips.forEach(function (ch) {
      ch.addEventListener("click", function () {
        var f = ch.dataset.filter;
        chips.forEach(function (c) { c.classList.toggle("on", c === ch); });
        d.querySelectorAll(".pcard").forEach(function (p) {
          var hit = f === "all" || p.dataset.type === f;
          p.classList.toggle("hide", !hit);
          if (hit) p.classList.add("in");
        });
        d.querySelectorAll(".grid").forEach(function (g) {
          var sec = g.closest(".sec");
          if (sec && !sec.querySelector(".chips")) sec.hidden = !g.querySelector(".pcard:not(.hide)");
        });
      });
    });
  });
})();

/* reviews page widgets (Google reviews via app.1examprep.com and Shopper Approved).
   The iframes and scripts are added here so the served HTML has no iframe or body script. */
(function () {
  var d = document, boxes = d.querySelectorAll(".reviews-embed");
  if (!boxes.length) return;
  function addScript(src) {
    if (d.querySelector('script[src="' + src + '"]')) return;
    var s = d.createElement("script"); s.src = src; s.type = "text/javascript"; s.async = true;
    (d.head || d.body).appendChild(s);
  }
  var lcLoaded = false;
  for (var i = 0; i < boxes.length; i++) {
    var b = boxes[i], kind = b.getAttribute("data-kind");
    if (kind === "google") {
      var f = d.createElement("iframe");
      f.className = "lc_reviews_widget";
      f.src = b.getAttribute("data-src");
      f.title = b.getAttribute("data-title") || "Customer reviews";
      f.setAttribute("frameborder", "0");
      f.setAttribute("scrolling", "no");
      f.setAttribute("loading", "lazy");
      f.style.minWidth = "100%"; f.style.width = "100%"; f.style.border = "0";
      b.innerHTML = ""; b.appendChild(f);
      lcLoaded = true;
    } else if (kind === "shopperapproved") {
      var w = d.createElement("div");
      w.id = b.getAttribute("data-wrapper"); w.className = "SA__wrapper"; w.setAttribute("lang", "en");
      b.innerHTML = ""; b.appendChild(w);
      window.sa_interval = 5000;
      if (typeof window.shopper_first === "undefined") addScript(b.getAttribute("data-src"));
    }
  }
  if (lcLoaded) addScript("https://app.1examprep.com/reputation/assets/review-widget.js");
})();
