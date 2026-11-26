// The only script: opens and closes the menu sheet on small screens.
(function () {
  var btn = document.querySelector('.menu-btn');
  var sheet = document.getElementById('sheet');
  if (!btn || !sheet) return;
  function set(open) {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? 'Close' : 'Menu';
    sheet.hidden = !open;
  }
  btn.addEventListener('click', function () { set(sheet.hidden); });
  sheet.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  window.addEventListener('resize', function () { if (window.innerWidth >= 1024) set(false); });
})();
