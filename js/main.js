/* ============================================================
   THE YARN NEST — Main JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---------- THEME TOGGLE ---------- */
  const themeToggle = document.getElementById('themeToggle');
  const savedTheme = localStorage.getItem('yarnTheme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';

  themeToggle.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('yarnTheme', next);
    themeToggle.textContent = next === 'dark' ? '☀️' : '🌙';
  });

  /* ---------- MOBILE MENU ---------- */
  const hamburger = document.getElementById('hamburger');
  const nav = document.getElementById('nav');
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    nav.classList.toggle('open');
  });
  nav.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      hamburger.classList.remove('open');
      nav.classList.remove('open');
    });
  });

  /* ---------- SEARCH BAR ---------- */
  const searchToggle = document.getElementById('searchToggle');
  const searchBar = document.getElementById('searchBar');
  const searchInput = document.getElementById('searchInput');
  const searchClose = document.getElementById('searchClose');

  searchToggle.addEventListener('click', () => {
    searchBar.classList.toggle('open');
    if (searchBar.classList.contains('open')) searchInput.focus();
  });
  searchClose.addEventListener('click', () => searchBar.classList.remove('open'));
  searchInput.addEventListener('input', e => {
    const q = e.target.value.toLowerCase().trim();
    renderDeals(currentCategory, q);
  });

  /* ---------- RENDER CATEGORIES ---------- */
  const categoriesGrid = document.getElementById('categoriesGrid');
  CATEGORIES.forEach(cat => {
    if (cat.id === 'all') return;
    const div = document.createElement('div');
    div.className = 'category-card';
    div.dataset.cat = cat.id;
    div.innerHTML = `
      <span class="cat-icon">${cat.icon}</span>
      <h3>${cat.name}</h3>
      <p>${cat.desc}</p>
    `;
    div.addEventListener('click', () => {
      setCategory(cat.id);
      document.getElementById('deals').scrollIntoView({ behavior: 'smooth' });
    });
    categoriesGrid.appendChild(div);
  });

  /* ---------- RENDER FILTERS ---------- */
  const filters = document.getElementById('filters');
  CATEGORIES.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn' + (cat.id === 'all' ? ' active' : '');
    btn.dataset.cat = cat.id;
    btn.textContent = `${cat.icon} ${cat.name}`;
    btn.addEventListener('click', () => setCategory(cat.id));
    filters.appendChild(btn);
  });

  /* ---------- DEALS RENDERING ---------- */
  const dealsGrid = document.getElementById('dealsGrid');
  const loadMoreBtn = document.getElementById('loadMore');
  let currentCategory = 'all';
  let visibleCount = 8;

  function setCategory(catId) {
    currentCategory = catId;
    visibleCount = 8;
    document.querySelectorAll('.filter-btn').forEach(b =>
      b.classList.toggle('active', b.dataset.cat === catId)
    );
    document.querySelectorAll('.category-card').forEach(c =>
      c.classList.toggle('active', c.dataset.cat === catId)
    );
    renderDeals(catId, searchInput.value.toLowerCase().trim());
  }

  function renderDeals(catId, query = '') {
    let list = DEALS;
    if (catId && catId !== 'all') list = list.filter(d => d.category === catId);
    if (query) {
      list = list.filter(d =>
        d.title.toLowerCase().includes(query) ||
        d.desc.toLowerCase().includes(query) ||
        d.store.toLowerCase().includes(query)
      );
    }

    const visible = list.slice(0, visibleCount);
    dealsGrid.innerHTML = '';

    if (visible.length === 0) {
      dealsGrid.innerHTML = `<p style="grid-column:1/-1;text-align:center;color:var(--muted);padding:40px;">No deals found. Try another search.</p>`;
      loadMoreBtn.style.display = 'none';
      return;
    }

    visible.forEach((d, i) => {
      const cat = CATEGORIES.find(c => c.id === d.category);
      const stars = '★'.repeat(Math.round(d.rating)) + '☆'.repeat(5 - Math.round(d.rating));
      const badgeHtml = d.badge ? `<span class="deal-tag ${d.badge}">${d.badge === 'hot' ? '🔥 Hot' : '✨ New'}</span>` : '';

      const card = document.createElement('article');
      card.className = 'deal-card';
      card.style.animationDelay = (i * 60) + 'ms';
      card.innerHTML = `
        <div class="deal-img">
          ${badgeHtml}
          <img src="${d.image}" alt="${d.title}" onerror="this.style.display='none';this.parentElement.textContent='${d.icon}'" />
        </div>
        <div class="deal-body">
          <span class="deal-cat">${cat ? cat.name : d.category}</span>
          <h3 class="deal-title">${d.title}</h3>
          <p class="deal-desc">${d.desc}</p>
          <div class="deal-rating">${stars} <span style="color:var(--muted);font-weight:400;">(${d.rating})</span></div>
          <div class="deal-footer">
            <div class="deal-price">
              ${d.oldPrice ? `<small>${d.oldPrice}</small>` : ''}${d.price}
            </div>
            <a href="${d.link}" class="btn-visit" target="_blank" rel="nofollow noopener sponsored">
              View Deal →
            </a>
          </div>
        </div>
      `;
      dealsGrid.appendChild(card);
    });

    loadMoreBtn.style.display = list.length > visibleCount ? 'inline-block' : 'none';
  }

  loadMoreBtn.addEventListener('click', () => {
    visibleCount += 4;
    renderDeals(currentCategory, searchInput.value.toLowerCase().trim());
  });

  renderDeals();

  /* ---------- NEWSLETTER ---------- */
  const newsletterForm = document.getElementById('newsletterForm');
  newsletterForm.addEventListener('submit', e => {
    e.preventDefault();
    const email = newsletterForm.querySelector('input').value;
    // یہاں اپنا Mailchimp / Formspree endpoint لگائیں
    console.log('Newsletter subscribe:', email);
    newsletterForm.innerHTML = `<p style="color:#fff;font-weight:600;padding:14px;">✅ Thanks! You're subscribed.</p>`;
  });

  /* ---------- BACK TO TOP ---------- */
  const backToTop = document.getElementById('backToTop');
  window.addEventListener('scroll', () => {
    backToTop.classList.toggle('show', window.scrollY > 500);
    // Active nav link highlighting
    const sections = ['home', 'deals', 'categories'];
    let current = '';
    sections.forEach(id => {
      const el = document.getElementById(id);
      if (el && window.scrollY >= el.offsetTop - 100) current = id;
    });
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === '#' + current);
    });
  });
  backToTop.addEventListener('click', () =>
    window.scrollTo({ top: 0, behavior: 'smooth' })
  );

  /* ---------- YEAR ---------- */
  document.getElementById('year').textContent = new Date().getFullYear();

  /* ---------- SMOOTH SCROLL for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});
