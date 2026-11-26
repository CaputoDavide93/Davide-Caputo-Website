/* davidecaputo.com: search palette, modals, keyboard shortcuts, theme. Vanilla, no dependencies. */
(function () {
  'use strict';
  var D = document, H = D.documentElement, B = D.body;
  var IDX = window.SEARCH_INDEX || [], DEF = window.SEARCH_DEFAULTS || [];
  var ROOT = B.getAttribute('data-root') || '';
  var ORDER = ['post', 'project', 'page', 'link'];
  var NAMES = { post: 'Posts', project: 'Projects', page: 'Pages', link: 'Links' };
  var page = D.getElementById('page');
  var modal = null, opener = null, goPending = false, goTimer = 0, palettes = [];

  function el(tag, cls, text) {
    var n = D.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  /* ---------- search ---------- */
  function tokens(q) { return q.toLowerCase().split(/\s+/).filter(Boolean); }

  function search(q) {
    var t = tokens(q), out = [];
    IDX.forEach(function (it, i) {
      var ti = it.title.toLowerCase(), tg = it.tags.join(' ').toLowerCase(),
          sb = it.sub.toLowerCase(), tx = (it.text || '').toLowerCase(), score = 0;
      for (var k = 0; k < t.length; k++) {
        var w = t[k], at = ti.indexOf(w), p;
        if (at === 0) p = 100;
        else if (at > 0) p = 60;
        else if (tg.indexOf(w) > -1) p = 30;
        else if (sb.indexOf(w) > -1) p = 15;
        else if (tx.indexOf(w) > -1) p = 5;
        else return;
        score += p;
      }
      out.push({ it: it, s: score, i: i });
    });
    out.sort(function (a, b) { return b.s - a.s || a.i - b.i; });
    out = out.slice(0, 12);
    return ORDER.map(function (ty) {
      return { name: NAMES[ty], items: out.filter(function (r) { return r.it.type === ty; }).map(function (r) { return r.it; }) };
    }).filter(function (g) { return g.items.length; });
  }

  function defaults(only) {
    return DEF.filter(function (g) { return !only || only.indexOf(g[0]) > -1; }).map(function (g) {
      return { name: g[0], items: g[1].map(function (i) { return IDX[i]; }) };
    });
  }

  function highlight(node, text, t) {
    var low = text.toLowerCase(), marks = [], pos = 0;
    t.forEach(function (w) {
      for (var at = low.indexOf(w); at > -1; at = low.indexOf(w, at + w.length)) marks.push([at, at + w.length]);
    });
    marks.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [];
    marks.forEach(function (m) {
      var last = merged[merged.length - 1];
      if (last && m[0] <= last[1]) last[1] = Math.max(last[1], m[1]); else merged.push(m);
    });
    merged.forEach(function (m) {
      if (m[0] > pos) node.appendChild(D.createTextNode(text.slice(pos, m[0])));
      node.appendChild(el('mark', null, text.slice(m[0], m[1])));
      pos = m[1];
    });
    if (pos < text.length) node.appendChild(D.createTextNode(text.slice(pos)));
  }

  function Palette(root) {
    var idp = root.getAttribute('data-idp'), overlay = root.hasAttribute('data-overlay');
    var input = root.querySelector('input'), list = root.querySelector('[role=listbox]'),
        empty = root.querySelector('[data-empty]'), live = root.querySelector('[data-live]'),
        only = root.querySelector('[data-defaults]'), rows = [], active = 0;
    only = only ? only.getAttribute('data-defaults').split(',') : null;
    var self = { input: input, root: root };

    function setActive(n, scroll) {
      if (!rows.length) { input.removeAttribute('aria-activedescendant'); return; }
      if (rows[active]) rows[active].setAttribute('aria-selected', 'false');
      active = Math.max(0, Math.min(rows.length - 1, n));
      rows[active].setAttribute('aria-selected', 'true');
      input.setAttribute('aria-activedescendant', rows[active].id);
      if (scroll) rows[active].scrollIntoView({ block: 'nearest' });
    }

    function render(groups, t) {
      list.textContent = '';
      var n = 0;
      groups.forEach(function (g, gi) {
        var box = el('div'), head = el('div', 'gh', g.name);
        box.setAttribute('role', 'group');
        head.id = idp + '-g' + gi;
        box.setAttribute('aria-labelledby', head.id);
        box.appendChild(head);
        g.items.forEach(function (it) {
          var a = el('a', 'row'), ic = el('i', 'ic', it.icon), tw = el('span', 't'), b = el('b'), s = el('span', 's');
          a.id = idp + '-r' + n++;
          a.href = it.ext ? it.url : ROOT + it.url;
          if (it.ext) a.rel = 'noopener';
          a.setAttribute('role', 'option');
          a.setAttribute('aria-selected', 'false');
          a.tabIndex = -1;
          ic.setAttribute('aria-hidden', 'true');
          highlight(b, it.title, t); highlight(s, it.sub, t);
          tw.appendChild(b); tw.appendChild(s);
          a.appendChild(ic); a.appendChild(tw); a.appendChild(el('kbd', 'kh', 'enter'));
          a.addEventListener('mousemove', function () {
            var i = rows.indexOf(a); if (i !== active) setActive(i, false);
          });
          box.appendChild(a);
        });
        list.appendChild(box);
      });
      rows = [].slice.call(list.querySelectorAll('.row'));
      active = 0;
      if (rows.length) setActive(0, false);
      list.scrollTop = 0;
      list.parentNode.scrollTop = 0;
    }

    function update() {
      var q = input.value.trim(), t = tokens(q);
      if (!t.length) {
        empty.hidden = true; list.hidden = false;
        render(defaults(only), []);
        live.textContent = '';
        return;
      }
      var groups = search(q), count = groups.reduce(function (a, g) { return a + g.items.length; }, 0);
      if (!count) {
        list.hidden = true; list.textContent = ''; rows = [];
        input.removeAttribute('aria-activedescendant');
        empty.textContent = 'No results for “' + q + '”. Try a tool name such as Jamf or AWS.';
        empty.hidden = false;
        live.textContent = 'No results for ' + q;
        return;
      }
      empty.hidden = true; list.hidden = false;
      render(groups, t);
      live.textContent = count + (count === 1 ? ' result' : ' results');
    }

    function clear() { input.value = ''; update(); }

    function open(newTab) {
      var a = rows[active];
      if (!a) return;
      if (newTab) window.open(a.href, '_blank', 'noopener'); else a.click();
    }

    input.addEventListener('input', update);
    input.addEventListener('keydown', function (ev) {
      var k = ev.key;
      if (k === 'ArrowDown') setActive(active + 1, true);
      else if (k === 'ArrowUp') setActive(active - 1, true);
      else if (k === 'PageDown') setActive(active + 5, true);
      else if (k === 'PageUp') setActive(active - 5, true);
      else if (k === 'Home') setActive(0, true);
      else if (k === 'End') setActive(rows.length - 1, true);
      else if (k === 'Enter') open(ev.metaKey || ev.ctrlKey);
      else if (k === 'Escape' && !overlay) { if (!input.value) return; clear(); }
      else return;
      ev.preventDefault();
    });
    root.querySelector('[data-clear]').addEventListener('click', function () { clear(); input.focus(); });
    self.reset = function () { input.value = ''; update(); };
    if (!rows.length) { rows = [].slice.call(list.querySelectorAll('.row')); }
    if (!overlay) {
      rows = [].slice.call(list.querySelectorAll('.row'));
      rows.forEach(function (a) { a.tabIndex = -1; a.addEventListener('mousemove', function () { setActive(rows.indexOf(a), false); }); });
    }
    return self;
  }

  /* ---------- modals ---------- */
  function openModal(m, focusEl) {
    if (modal) return;
    opener = D.activeElement; modal = m;
    m.hidden = false; page.inert = true; H.classList.add('lock');
    (focusEl || m.querySelector('input,button')).focus();
  }

  function closeModal() {
    if (!modal) return;
    var o = opener, m = modal;
    m.hidden = true; page.inert = false; H.classList.remove('lock');
    modal = null; opener = null;
    var back = o && o !== B && D.contains(o) ? o : (D.querySelector('[data-open-search]') || D.getElementById('main'));
    if (back) back.focus();
  }

  function trap(ev) {
    var f = [].slice.call(modal.querySelectorAll('button,[href],input,[tabindex]:not([tabindex="-1"])')).filter(function (n) {
      return n.tabIndex >= 0 && !n.disabled && n.offsetParent !== null;
    });
    if (!f.length) { ev.preventDefault(); return; }
    var first = f[0], last = f[f.length - 1], cur = D.activeElement;
    if (f.indexOf(cur) < 0) { ev.preventDefault(); (ev.shiftKey ? last : first).focus(); }
    else if (ev.shiftKey && cur === first) { ev.preventDefault(); last.focus(); }
    else if (!ev.shiftKey && cur === last) { ev.preventDefault(); first.focus(); }
  }

  function openSearch() {
    var ov = D.getElementById('search-ov');
    if (ov) {
      var p = palettes.filter(function (x) { return ov.contains(x.root); })[0];
      p.reset(); openModal(ov, p.input); return;
    }
    var home = palettes[0];
    if (home) { home.input.focus(); home.input.select(); }
  }

  function openHelp() { var h = D.getElementById('help-ov'); if (h && !modal) openModal(h, h.querySelector('button')); }

  /* ---------- theme ---------- */
  var MODES = ['system', 'light', 'dark'], LABEL = { system: 'System', light: 'Light', dark: 'Dark' };
  function mode() { var t = H.getAttribute('data-theme'); return t === 'light' || t === 'dark' ? t : 'system'; }
  function paintTheme() {
    var m = mode(), next = MODES[(MODES.indexOf(m) + 1) % 3];
    [].forEach.call(D.querySelectorAll('[data-theme-toggle]'), function (b) {
      b.setAttribute('data-mode', m);
      b.setAttribute('aria-label', 'Theme: ' + LABEL[m] + '. Switch to ' + LABEL[next] + '.');
      b.querySelector('[data-theme-label]').textContent = LABEL[m];
    });
  }
  function cycleTheme() {
    var m = MODES[(MODES.indexOf(mode()) + 1) % 3];
    if (m === 'system') H.removeAttribute('data-theme'); else H.setAttribute('data-theme', m);
    try { if (m === 'system') localStorage.removeItem('theme'); else localStorage.setItem('theme', m); } catch (e) { /* storage blocked */ }
    paintTheme();
  }

  /* ---------- wiring ---------- */
  [].forEach.call(D.querySelectorAll('[data-palette]'), function (r) { palettes.push(Palette(r)); });
  [].forEach.call(D.querySelectorAll('[data-open-search]'), function (b) { b.addEventListener('click', openSearch); });
  [].forEach.call(D.querySelectorAll('[data-open-help]'), function (b) { b.addEventListener('click', openHelp); });
  [].forEach.call(D.querySelectorAll('[data-theme-toggle]'), function (b) { b.addEventListener('click', cycleTheme); });
  [].forEach.call(D.querySelectorAll('[data-close]'), function (b) { b.addEventListener('click', closeModal); });
  [].forEach.call(D.querySelectorAll('.ov'), function (ov) {
    ov.addEventListener('mousedown', function (ev) { if (ev.target === ov) closeModal(); });
  });
  paintTheme();

  var GO = { w: 'work.html', a: 'about.html', b: 'blog/index.html', p: 'projects.html' };
  function typing(t) { return t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable); }

  D.addEventListener('keydown', function (ev) {
    var k = ev.key;
    if (modal) {
      if (k === 'Tab') trap(ev);
      else if (k === 'Escape') {
        ev.preventDefault();
        var p = palettes.filter(function (x) { return modal.contains(x.root); })[0];
        if (p) p.reset();
        closeModal();
      }
      return;
    }
    if ((ev.metaKey || ev.ctrlKey) && !ev.altKey && k.toLowerCase() === 'k') { ev.preventDefault(); openSearch(); return; }
    if (ev.metaKey || ev.ctrlKey || ev.altKey || typing(ev.target) || ev.defaultPrevented) return;
    if (goPending) {
      goPending = false; clearTimeout(goTimer);
      var dest = GO[k.toLowerCase()];
      if (dest) { ev.preventDefault(); window.location.href = ROOT + dest; return; }
    }
    if (k === '/') { ev.preventDefault(); openSearch(); }
    else if (k === '?') { ev.preventDefault(); openHelp(); }
    else if (k === 't') { cycleTheme(); }
    else if (k === 'g') { goPending = true; goTimer = setTimeout(function () { goPending = false; }, 1500); }
  });

  if (palettes[0] && B.classList.contains('is-home') && !palettes[0].root.hasAttribute('data-notfound') &&
      window.matchMedia && window.matchMedia('(pointer:fine)').matches) {
    palettes[0].input.focus();
  }
})();
