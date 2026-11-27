/* The Yarn Nest: accessible mobile navigation.
   Keep this file intentionally small so pages without a mobile menu do not
   produce null-element errors in the browser console. */
document.addEventListener('DOMContentLoaded', function () {
  const hamburger = document.getElementById('hamburger');
  const nav = document.getElementById('nav');

  if (!hamburger || !nav) return;

  hamburger.setAttribute('aria-controls', 'nav');
  hamburger.setAttribute('aria-expanded', 'false');
  if (!hamburger.hasAttribute('aria-label')) {
    hamburger.setAttribute('aria-label', 'Open navigation menu');
  }

  hamburger.addEventListener('click', function () {
    const isOpen = hamburger.classList.toggle('open');
    nav.classList.toggle('open', isOpen);
    hamburger.setAttribute('aria-expanded', String(isOpen));
    hamburger.setAttribute('aria-label', isOpen ? 'Close navigation menu' : 'Open navigation menu');
  });

  nav.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      hamburger.classList.remove('open');
      nav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      hamburger.setAttribute('aria-label', 'Open navigation menu');
    });
  });
});
