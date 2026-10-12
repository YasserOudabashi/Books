// La mente studiata — comportamento del sito (tema, dimensione testo, menu, avanzamento, indice).
(function () {
  var root = document.documentElement;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // --- tema e dimensione (il valore iniziale è già applicato da uno script nell'<head>) ---
  function applyTheme(t) {
    if (t === 'light' || t === 'dark' || t === 'base') root.setAttribute('data-theme', t);
    else root.removeAttribute('data-theme');
    set('ms-theme', t || 'auto');
    mark('[data-theme-btn]', 'themeBtn', t || 'auto');
  }
  function applySize(s) {
    if (s === 's' || s === 'l') root.setAttribute('data-size', s); else root.removeAttribute('data-size');
    set('ms-size', s || 'm');
    mark('[data-size-btn]', 'sizeBtn', s || 'm');
  }
  function mark(sel, key, val) {
    document.querySelectorAll(sel).forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset[key] === val)); });
  }
  document.querySelectorAll('[data-theme-btn]').forEach(function (b) {
    b.addEventListener('click', function () { applyTheme(b.dataset.themeBtn); });
  });
  document.querySelectorAll('[data-size-btn]').forEach(function (b) {
    b.addEventListener('click', function () { applySize(b.dataset.sizeBtn); });
  });
  mark('[data-theme-btn]', 'themeBtn', get('ms-theme') || 'auto');
  mark('[data-size-btn]', 'sizeBtn', get('ms-size') || 'm');

  // --- popover impostazioni ---
  var pop = document.getElementById('settings-pop'), sbtn = document.getElementById('settings-btn');
  if (pop && sbtn) {
    sbtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = pop.classList.toggle('open');
      sbtn.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', function (e) { if (!pop.contains(e.target)) { pop.classList.remove('open'); sbtn.setAttribute('aria-expanded', 'false'); } });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { pop.classList.remove('open'); document.body.classList.remove('menu-open'); } });
  }

  // --- menu laterale su schermi piccoli ---
  var mbtn = document.getElementById('menu-btn'), scrim = document.querySelector('.scrim');
  if (mbtn) mbtn.addEventListener('click', function () { document.body.classList.toggle('menu-open'); });
  if (scrim) scrim.addEventListener('click', function () { document.body.classList.remove('menu-open'); });
  document.querySelectorAll('.sidebar a').forEach(function (a) {
    a.addEventListener('click', function () { document.body.classList.remove('menu-open'); });
  });

  // --- barra di avanzamento e "torna su" ---
  var bar = document.querySelector('.progress'), top = document.getElementById('to-top');
  function onScroll() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    if (bar) bar.style.width = (h > 0 ? Math.min(100, (window.scrollY / h) * 100) : 0) + '%';
    if (top) top.classList.toggle('show', window.scrollY > 900);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (top) top.addEventListener('click', function () { window.scrollTo({ top: 0 }); });

  // --- capitolo corrente evidenziato nell'indice laterale ---
  var links = {};
  document.querySelectorAll('.sidebar li a[data-target]').forEach(function (a) { links[a.dataset.target] = a; });
  var heads = Array.prototype.slice.call(document.querySelectorAll('main h2[id]'));
  if (heads.length && 'IntersectionObserver' in window) {
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          var a = links[en.target.id];
          if (!a || a === current) return;
          if (current) current.classList.remove('active');
          a.classList.add('active'); current = a;
          var sb = document.querySelector('.sidebar');
          if (sb && window.innerWidth >= 1000) {
            var r = a.getBoundingClientRect(), sr = sb.getBoundingClientRect();
            if (r.top < sr.top + 60 || r.bottom > sr.bottom - 60) a.scrollIntoView({ block: 'center' });
          }
        }
      });
    }, { rootMargin: '-10% 0px -80% 0px' });
    heads.forEach(function (h) { io.observe(h); });
  }

  // --- filtro dei capitoli ---
  var f = document.getElementById('filter');
  if (f) f.addEventListener('input', function () {
    var q = f.value.trim().toLowerCase();
    document.querySelectorAll('.sb-part').forEach(function (p) {
      var any = false;
      p.querySelectorAll('li').forEach(function (li) {
        var ok = !q || li.textContent.toLowerCase().indexOf(q) !== -1;
        li.classList.toggle('hide', !ok); if (ok) any = true;
      });
      if (q) p.open = any;
      p.style.display = (q && !any) ? 'none' : '';
    });
  });
})();
