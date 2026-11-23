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


    /* exam path picker on the home page */
    var form = d.getElementById("path-form");
    if (form) {
      var data = null, lic = null, choice = null;
      var sel = d.getElementById("path-license");
      var steps = [].slice.call(form.querySelectorAll(".p-step"));
      var qchips = [].slice.call(form.querySelectorAll(".qchip"));
      var opts = [].slice.call(form.querySelectorAll(".opt"));
      var out = form.querySelector(".p-result");
      var money = function (x) {
        if (!x) return "Free";
        return "$" + (Math.round(x) === x ? x.toLocaleString("en-US") : x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
      };
      var esc = function (s) { var t = d.createElement("span"); t.textContent = s; return t.innerHTML; };
      steps[1].classList.add("wait"); steps[2].classList.add("wait");
      form.addEventListener("submit", function (ev) { ev.preventDefault(); });
      var load = function (cb) {
        if (data) return cb();
        fetch("/assets/finder.json").then(function (r) { return r.json(); }).then(function (j) { data = j; cb(); })
          .catch(function () { out.innerHTML = '<p class="p-empty">The picker could not load. Use the license list below, or call (877) 775-9400.</p>'; });
      };
      var find = function (id) { for (var i = 0; i < data.licenses.length; i++) if (data.licenses[i].id === id) return data.licenses[i]; return null; };
      var row = function (p, check) {
        var img = p.i ? '<img src="' + esc(p.i) + '" alt="" width="64" height="64" loading="lazy">' : '<span></span>';
        var title = '<a href="' + p.u + '">' + esc(p.t) + '</a><small>' + esc(p.k) + " · " + money(p.p) + "</small>";
        if (check) title = '<label><input type="checkbox" checked data-add>' + '<span>' + title + "</span></label>";
        return '<div class="pr">' + img + "<div>" + title + "</div></div>";
      };
      var render = function () {
        var L = find(lic);
        if (!L || !choice || !L.ch[choice]) return;
        var pair = L.ch[choice], main = data.products[pair[0]], add = pair[1] != null ? data.products[pair[1]] : null;
        var html = '<p class="p-exams">' + esc(L.n) + ": " + L.x.map(esc).join(" + ") + "</p>" + row(main, false);
        if (add) html += row(add, true);
        html += '<div class="p-total"><span><span class="sr">Total </span><b data-total></b></span><a class="btn" data-buy rel="nofollow" href="#">Buy now</a></div>';
        html += '<a class="p-more" href="' + L.u + '">Compare all ' + L.count + " " + esc(L.n) + " packages</a>";
        out.innerHTML = html;
        var cb = out.querySelector("[data-add]"), buy = out.querySelector("[data-buy]"), tot = out.querySelector("[data-total]");
        var upd = function () {
          var withAdd = add && cb && cb.checked, sum = main.p + (withAdd ? add.p : 0);
          tot.textContent = money(sum);
          buy.textContent = main.p === 0 && !withAdd ? "Get the free demo" : (withAdd ? "Buy both exams" : "Buy now");
          buy.href = "https://1examprep.com/cart/" + main.v + ":1" + (withAdd ? "," + add.v + ":1" : "");
        };
        if (cb) cb.addEventListener("change", upd);
        upd();
        steps[2].classList.remove("wait"); steps[2].classList.add("ok");
      };
      var setLic = function (id) {
        load(function () {
          var L = find(id);
          if (!L) return;
          lic = id;
          sel.value = id;
          qchips.forEach(function (q) { q.classList.toggle("on", q.dataset.lic === id); });
          steps[0].classList.add("ok"); steps[1].classList.remove("wait");
          var first = null;
          opts.forEach(function (o) {
            var ok = !!L.ch[o.dataset.choice];
            o.disabled = !ok;
            if (ok && !first) first = o.dataset.choice;
          });
          if (!choice || !L.ch[choice]) {
            choice = L.ch["books-course"] ? "books-course" : first;
          }
          opts.forEach(function (o) { o.classList.toggle("on", o.dataset.choice === choice); });
          if (choice) { steps[1].classList.add("ok"); render(); }
        });
      };
      qchips.forEach(function (q) { q.addEventListener("click", function () { setLic(q.dataset.lic); }); });
      sel.addEventListener("change", function () { if (sel.value) setLic(sel.value); });
      opts.forEach(function (o) {
        o.addEventListener("click", function () {
          choice = o.dataset.choice;
          opts.forEach(function (x) { x.classList.toggle("on", x === o); });
          steps[1].classList.add("ok");
          render();
        });
      });
      var q1 = new URLSearchParams(location.search).get("license");
      if (q1) setLic(q1);
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
