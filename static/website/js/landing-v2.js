/* Fidelio Pro Landing V2 mobile navigation.
   Usage: include with <script src="js/landing-v2.js" defer>; it toggles body.nav-open from the [data-nav-toggle] button and closes the menu after anchor clicks or Escape. No SEO text depends on this script. */
(function () {
  var toggle = document.querySelector('[data-nav-toggle]');
  var nav = document.querySelector('[data-main-nav]');
  if (!toggle || !nav) return;

  function setOpen(open) {
    document.body.classList.toggle('nav-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
  }

  toggle.addEventListener('click', function () {
    setOpen(!document.body.classList.contains('nav-open'));
  });

  nav.addEventListener('click', function (event) {
    if (event.target && event.target.tagName === 'A') setOpen(false);
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') setOpen(false);
  });
})();
