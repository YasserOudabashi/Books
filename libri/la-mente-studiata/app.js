// La mente studiata — comportamento del sito (impostazioni di lettura, indice laterale, avanzamento).
(function () {
  var root = document.documentElement;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // --- impostazioni di lettura (i valori salvati sono già applicati dallo script nell'<head>) ---
  // Ogni scelta è un attributo di <html> (data-theme, data-font, ...) e una chiave ms-* nel browser.
  var DEFAULTS = { theme: 'auto', font: 'serif', size: '2', leading: 'normal', width: 'normal' };
  function currentValue(key) { return root.getAttribute('data-' + key) || DEFAULTS[key]; }
  function applySetting(key, val) {
    if (val === DEFAULTS[key]) root.removeAttribute('data-' + key); else root.setAttribute('data-' + key, val);
    set('ms-' + key, val);
    markSettings();
  }
  function markSettings() {
    document.querySelectorAll('[data-set]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.value === currentValue(b.dataset.set)));
    });
  }
  document.querySelectorAll('[data-set]').forEach(function (b) {
    b.addEventListener('click', function () { applySetting(b.dataset.set, b.dataset.value); });
  });
  markSettings();

  // --- lingua: il pulsante IT/EN porta alla stessa pagina nell'altra lingua ---
  // Mantiene il capitolo (#cap-…, gli id sono uguali nelle due lingue) e ricorda
  // la scelta: chi ha scelto l'inglese, aprendo la copertina italiana, va a quella inglese.
  var lbtn = document.getElementById('lang-btn');
  if (lbtn) lbtn.addEventListener('click', function () {
    set('ms-lang', lbtn.getAttribute('hreflang'));
    var hash = location.hash;
    var current = document.querySelector('.sidebar li a.active');
    if (!hash && current) hash = '#' + current.dataset.target;
    if (hash) lbtn.href = lbtn.href.split('#')[0] + hash;
  });
  if (root.lang === 'it' && get('ms-lang') === 'en' && document.querySelector('.hero') && lbtn) {
    location.replace(lbtn.href);
  }

  // --- pannelli: indice a sinistra, impostazioni a destra ---
  var body = document.body;
  var mbtn = document.getElementById('menu-btn'), sbtn = document.getElementById('settings-btn');
  var sidebar = document.querySelector('.sidebar'), scrim = document.querySelector('.scrim');
  var hotzone = document.querySelector('.toc-hotzone');
  var openedByHover = false;

  function openMenu(byHover) {
    closeSettings();
    openedByHover = byHover;
    body.classList.add('menu-open');
    body.classList.toggle('menu-pinned', !byHover); // aperto col clic: sfondo scuro, resta aperto
    if (mbtn) mbtn.setAttribute('aria-expanded', 'true');
    centerActive();
  }
  // Porta in vista, dentro l'indice, il capitolo che si sta leggendo.
  function centerActive() {
    var a = sidebar && sidebar.querySelector('li a.active');
    if (a) sidebar.scrollTop = a.offsetTop - sidebar.clientHeight / 2;
  }
  function closeMenu() {
    openedByHover = false;
    body.classList.remove('menu-open', 'menu-pinned');
    if (mbtn) mbtn.setAttribute('aria-expanded', 'false');
  }
  function openSettings() {
    closeMenu();
    body.classList.add('settings-open');
    if (sbtn) sbtn.setAttribute('aria-expanded', 'true');
  }
  function closeSettings() {
    body.classList.remove('settings-open');
    if (sbtn) sbtn.setAttribute('aria-expanded', 'false');
  }

  if (mbtn) mbtn.addEventListener('click', function () {
    if (body.classList.contains('menu-pinned')) closeMenu(); else openMenu(false);
  });
  if (sbtn) sbtn.addEventListener('click', function () {
    if (body.classList.contains('settings-open')) closeSettings(); else openSettings();
  });
  var sclose = document.getElementById('settings-close');
  if (sclose) sclose.addEventListener('click', closeSettings);
  if (scrim) scrim.addEventListener('click', function () { closeMenu(); closeSettings(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeMenu(); closeSettings(); } });
  document.querySelectorAll('.sidebar a').forEach(function (a) { a.addEventListener('click', closeMenu); });

  // Apertura col mouse sul bordo sinistro, solo con un mouse vero: sui touch
  // screen un tocco sul bordo la aprirebbe per sbaglio (lì resta il pulsante ☰).
  // Si chiude quando il mouse si allontana dal pannello, non al "mouseleave":
  // se il mouse sfiora il bordo e scappa subito a destra, il pannello non
  // riceverebbe mai l'evento e resterebbe aperto sopra il testo.
  var finePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (hotzone && sidebar && finePointer) {
    hotzone.addEventListener('mouseenter', function () {
      if (!body.classList.contains('menu-open') && !body.classList.contains('settings-open')) openMenu(true);
    });
    document.addEventListener('mousemove', function (e) {
      if (openedByHover && e.clientX > sidebar.offsetWidth + 24) closeMenu();
    }, { passive: true });
  }

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
          if (body.classList.contains('menu-open')) centerActive();
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
