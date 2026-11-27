/* The Yarn Nest - automatic social share buttons (Facebook, X/Twitter, Pinterest, Instagram).
   Add <script src="js/share.js" defer></script> to a page and the buttons appear by themselves.
   No per-page setup: the URL, title and image are read from the page's own meta tags. */
(function () {
  'use strict';

  // Pages that should not get share buttons.
  var SKIP = ['privacy', 'contact', 'download'];
  var path = location.pathname.replace(/\.html$/, '').replace(/\/+$/, '').split('/').pop().toLowerCase();
  if (SKIP.indexOf(path) !== -1) return;
  if (document.querySelector('.yn-share')) return;

  function meta(sel) {
    var el = document.querySelector(sel);
    return el ? (el.getAttribute('content') || el.getAttribute('href') || '').trim() : '';
  }

  function pageData() {
    var url = meta('link[rel="canonical"]') || meta('meta[property="og:url"]') || (location.origin + location.pathname);
    try { url = new URL(url, location.href).href; } catch (e) {}
    var h1 = document.querySelector('h1');
    var title = meta('meta[property="og:title"]') || (h1 && h1.textContent.trim()) || document.title;
    var image = meta('meta[property="og:image"]');
    if (!image) {
      var img = document.querySelector('article img, figure img, main img, .container img');
      if (img && img.src) image = img.src;
    }
    try { if (image) image = new URL(image, location.href).href; } catch (e) {}
    return { url: url, title: title, image: image };
  }

  var ICONS = {
    facebook: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M13.5 22v-8.2h2.8l.4-3.3h-3.2V8.4c0-.9.3-1.6 1.6-1.6h1.7V3.9c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.4H7.3v3.3h2.8V22h3.4z"/></svg>',
    x: '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M18.2 2.5h3.3l-7.2 8.3 8.5 11.2h-6.7l-5.2-6.8-6 6.8H1.6l7.7-8.8L1.2 2.5H8l4.7 6.2 5.5-6.2zm-1.2 17.5h1.8L7 4.4H5.1L17 20z"/></svg>',
    pinterest: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true"><path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.162-.105-.949-.199-2.403.041-3.439.219-.937 1.406-5.957 1.406-5.957s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.099.12.112.225.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.401.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.354-.629-2.758-1.379l-.749 2.848c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12.017 24c6.624 0 11.99-5.367 11.99-11.988C24.007 5.367 18.641.001 12.017.001z"/></svg>',
    instagram: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg>'
  };

  var CSS =
    '.yn-share{margin:40px 0 20px;padding:20px;background:#fff;border:1px solid #e8e0d5;border-radius:12px;text-align:center;clear:both}' +
    '.yn-share-title{font-family:Poppins,sans-serif;font-size:16px;font-weight:600;margin:0 0 14px;color:#332d2a}' +
    '.yn-share-row{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}' +
    '.yn-share a,.yn-share button{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-width:44px;height:44px;padding:0 16px;border:0;border-radius:999px;color:#fff;font:600 14px Poppins,sans-serif;cursor:pointer;text-decoration:none;transition:transform .15s,opacity .15s}' +
    '.yn-share a:hover,.yn-share button:hover{transform:translateY(-2px);opacity:.9}' +
    '.yn-fb{background:#1877f2}.yn-x{background:#000}.yn-pin{background:#e60023}' +
    '.yn-ig{background:linear-gradient(45deg,#f09433,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888)}' +
    '.yn-share-msg{min-height:20px;margin:10px 0 0;font-size:13px;color:#7a6f68}' +
    '@media(max-width:480px){.yn-share-lbl{display:none}.yn-share a,.yn-share button{padding:0;width:44px}}';

  function enc(s) { return encodeURIComponent(s); }

  function build(d) {
    var box = document.createElement('div');
    box.className = 'yn-share';
    box.setAttribute('data-share', 'auto');

    var links = {
      fb: 'https://www.facebook.com/sharer/sharer.php?u=' + enc(d.url),
      x: 'https://twitter.com/intent/tweet?url=' + enc(d.url) + '&text=' + enc(d.title),
      pin: 'https://www.pinterest.com/pin/create/button/?url=' + enc(d.url) +
           (d.image ? '&media=' + enc(d.image) : '') + '&description=' + enc(d.title)
    };

    box.innerHTML =
      '<p class="yn-share-title">Enjoyed this? Share it!</p>' +
      '<div class="yn-share-row">' +
        '<a class="yn-fb" href="' + links.fb + '" target="_blank" rel="noopener noreferrer" aria-label="Share on Facebook">' + ICONS.facebook + '<span class="yn-share-lbl">Facebook</span></a>' +
        '<a class="yn-x" href="' + links.x + '" target="_blank" rel="noopener noreferrer" aria-label="Share on X (Twitter)">' + ICONS.x + '<span class="yn-share-lbl">X</span></a>' +
        '<a class="yn-pin" href="' + links.pin + '" target="_blank" rel="noopener noreferrer" aria-label="Save to Pinterest">' + ICONS.pinterest + '<span class="yn-share-lbl">Pinterest</span></a>' +
        '<button type="button" class="yn-ig" aria-label="Share on Instagram">' + ICONS.instagram + '<span class="yn-share-lbl">Instagram</span></button>' +
      '</div>' +
      '<p class="yn-share-msg" role="status" aria-live="polite"></p>';

    var msg = box.querySelector('.yn-share-msg');

    // Instagram has no web share URL, so: use the phone's share sheet if available,
    // otherwise copy the link and open Instagram so it can be pasted in a story/bio/DM.
    box.querySelector('.yn-ig').addEventListener('click', function () {
      if (navigator.share) {
        navigator.share({ title: d.title, url: d.url }).catch(function () {});
        return;
      }
      function opened() {
        msg.textContent = 'Link copied! Paste it in your Instagram story, bio or message.';
        window.open('https://www.instagram.com/', '_blank', 'noopener');
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(d.url).then(opened, function () { window.prompt('Copy this link:', d.url); });
      } else {
        window.prompt('Copy this link:', d.url);
      }
    });
    return box;
  }

  function place(box) {
    var articles = document.querySelectorAll('article:not(.blog-card)');
    if (articles.length) {
      var last = articles[articles.length - 1];
      last.parentNode.insertBefore(box, last.nextSibling);
      return;
    }
    var main = document.querySelector('main');
    if (main) { main.appendChild(box); return; }
    var footer = document.querySelector('footer');
    if (footer) { footer.parentNode.insertBefore(box, footer); return; }
    document.body.appendChild(box);
  }

  function init() {
    // Replace older hand-made share blocks so there are never two sets of buttons.
    var old = document.querySelectorAll('.share-section');
    for (var i = 0; i < old.length; i++) old[i].parentNode.removeChild(old[i]);

    var style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);
    place(build(pageData()));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
