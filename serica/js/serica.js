/* =========================================================================
   SERICA — scroll engine
   Vanilla, no dependencies. Chapters are sticky scenes; the scroll position
   inside a chapter is the timeline that swaps feature panels, drifts the
   painting and lights the roman numeral. Copy comes from js/content.js.
   ========================================================================= */
(() => {
  'use strict';

  const DATA = window.SERICA;
  const chapters = DATA.chapters;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
  const pad2 = (n) => String(n).padStart(2, '0');
  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => [...r.querySelectorAll(s)];

  /* panels per chapter decide the chapter's scroll length */
  const chapterHeight = (n) => 100 + Math.min(n, 22) * 22; // vh

  /* ------------------------------------------------------------------ build */
  const host = qs('#chapters');
  const railOl = qs('#chapterRail ol');
  const mobileChapters = qs('#mobileChapters');
  const frag = document.createDocumentFragment();
  const railFrag = document.createDocumentFragment();
  const mobFrag = document.createDocumentFragment();

  chapters.forEach((ch, i) => {
    const active = chapters[0].id === ch.id;
    /* ---- hero rail entry (also repeated inside each chapter) */
    const railLi = document.createElement('li');
    railLi.innerHTML = `<a href="#ch-${ch.id}" data-jump="${ch.id}" class="${active ? 'is-active' : ''}">
        <span class="ch-name"></span><span class="rom">${ch.roman}</span></a>`;
    railLi.querySelector('.ch-name').textContent = ch.title;
    railFrag.appendChild(railLi);

    const mobA = document.createElement('a');
    mobA.href = `#ch-${ch.id}`;
    mobA.innerHTML = `<small>${ch.roman}</small>${ch.title}`;
    mobFrag.appendChild(mobA);

    /* ---- the chapter itself */
    const sec = document.createElement('section');
    sec.className = 'chapter';
    sec.id = `ch-${ch.id}`;
    sec.dataset.theme = 'dark';
    sec.dataset.chapter = String(i);
    sec.style.setProperty('--panel-span', chapterHeight(ch.features.length) + 'vh');

    sec.innerHTML = `
      <div class="stick">
      <div class="stage-media">
        <img class="stage-art" src="${ch.art}" alt="Chapter ${ch.roman}, ${ch.title}: a new Renaissance painting with ${ch.title.toLowerCase()} props." loading="${i < 2 ? 'eager' : 'lazy'}" decoding="async">
        <div class="stage-scrim"></div>
      </div>
      <div class="chapter-inner">
        <div class="chapter-view">
          <p class="mini-lockup" aria-hidden="true">The<br><span>La/</span>quer<br>Edition</p>
          <div class="panels" role="list"></div>
          <div class="chapter-titlewrap">
            <p class="chapter-kicker"><b>${ch.roman}</b> ${ch.kicker}</p>
            <h2 class="chapter-title">${ch.title.replace(/\//g, '<span class="slash">/</span>')}</h2>
            <p class="chapter-lead">${ch.lead}</p>
          </div>
          <nav class="chapter-rail-inline" aria-label="Chapters">
            <ol></ol>
          </nav>
          <div class="panel-count">
            <span class="pc-now">01</span>
            <span class="bar"><span></span></span>
            <span class="pc-all">${pad2(Math.max(ch.features.length, 1))}</span>
          </div>
        </div>
      </div>
      </div>`;

    const panelBox = qs('.panels', sec);
    ch.features.forEach((f, k) => {
      const p = document.createElement('article');
      p.className = 'panel' + (k === 0 ? ' is-on' : '');
      p.setAttribute('role', 'listitem');
      p.dataset.step = String(k);
      p.innerHTML = `
        <div class="panel-meta"><span>${ch.title} — ${pad2(k + 1)} / ${pad2(ch.features.length)}</span><b>New</b></div>
        <h3>${f.t}</h3>
        <p>${f.d}</p>
        ${f.cta ? `<a class="panel-cta" href="${f.cta}" target="_blank" rel="noopener">Read help doc <span aria-hidden="true">↗</span></a>` : ''}`;
      panelBox.appendChild(p);
    });
    /* the chapter's own copy of the rail, cloned after the rail exists */
    qs('.chapter-rail-inline ol', sec).appendChild(railFrag.cloneNode(true));

    const quote = document.createElement('div');
    quote.className = 'chapter-quote';
    quote.innerHTML = `<span class="quote-mark" aria-hidden="true">”</span>
      <p>${ch.lead}</p>
      <span class="quote-src">${ch.roman} · ${ch.kicker} · Serica Editions Winter ’26</span>`;

    frag.appendChild(sec);
    frag.appendChild(quote);
  });

  host.replaceChildren(frag);
  railOl.appendChild(railFrag);
  mobileChapters.appendChild(mobFrag);

  /* sync duplicated rails: clicking one numeral updates all copies */
  const allRailLinks = () =>
    qsa('.chapter-rail a, .chapter-rail-inline a, .mobile-nav a[href^="#ch-"]');

  const setActiveRail = (id) => {
    allRailLinks().forEach((a) => {
      const jump = a.dataset.jump || (a.hash || '').replace('#ch-', '');
      a.classList.toggle('is-active', jump === id);
    });
  };

  /* ------------------------------------------------------------------ hero fade */
  /* ------------------------------------------------------------- scrolling */
  const nav = qs('#nav');
  const progressBar = qs('#progressBar');
  const stageHero = qs('.stage-hero');
  const heroArt = qs('.stage-hero .stage-art');
  const sections = qsa('[data-chapter]');
  const chapterEls = chapters.map((ch) => qs(`#ch-${ch.id}`));
  const bands = qsa('.chapter-quote').concat([qs('.stage-outro')].filter(Boolean));

  let scrollY = window.scrollY;
  let targetY = scrollY;
  let current = 0;
  const state = { id: chapters[0].id, step: 0 };

  const onScroll = () => {
    targetY = window.scrollY;
    const doc = document.documentElement;
    const max = doc.scrollHeight - window.innerHeight;
    progressBar.style.width = `${clamp(max > 0 ? targetY / max : 0) * 100}%`;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);

  /* ------------------------------------------------------------- per frame */
  const render = () => {
    const smooth = reduced.matches ? 1 : 0.12;
    current = lerp(current, targetY, smooth);
    if (Math.abs(current - targetY) < 0.4) current = targetY;
    scrollY = current;
    const vh = window.innerHeight;

    /* hero parallax: painting drifts up and scales down as it leaves */
    if (heroArt && scrollY < vh * 1.4) {
      const p = clamp(scrollY / vh);
      heroArt.style.transform = `scale(${1.06 + p * 0.06}) translate3d(0, ${p * 8}%, 0)`;
      heroArt.style.opacity = String(1 - p * 0.35);
      if (stageHero) {
        const lockup = stageHero.querySelector('.hero-lockup');
        const rail = stageHero.querySelector('.chapter-rail');
        lockup.style.transform = `translate3d(0, ${p * -46}px, 0)`;
        lockup.style.opacity = String(clamp(1 - p * 1.6));
        rail.style.opacity = String(clamp(1 - p * 2));
      }
    }

    /* find which chapter is pinned in the viewport */
    let activeId = null;
    let activeStep = 0;
    let activeIndex = -1;

    chapterEls.forEach((sec, i) => {
      if (!sec) return;
      const rect = sec.getBoundingClientRect();
      /* the sticky media sits at viewport top while rect.top <= 0 <= rect.bottom */
      if (rect.top <= 1 && rect.bottom > vh) {
        activeId = chapters[i].id;
        activeIndex = i;
        const span = rect.height - vh;
        const p = span > 0 ? clamp(-rect.top / span) : 0;
        const n = Math.max(chapters[i].features.length, 1);
        activeStep = Math.min(n - 1, Math.floor(p * n));
        /* painting drift inside the scene */
        const art = sec.querySelector('.stage-art');
        if (art) {
          const drift = (p - 0.5) * 2; // -1 … 1
          art.style.transform = `scale(1.08) translate3d(${drift * -1.4}%, ${drift * 1.6}%, 0)`;
        }
      }
    });

    if (activeId) {
      if (activeId !== state.id) {
        setActiveRail(activeId);
        state.id = activeId;
        state.step = -1;
      }
      if (activeStep !== state.step) {
        const sec = chapterEls[activeIndex];
        const panels = qsa('.panel', sec);
        panels.forEach((p, k) => p.classList.toggle('is-on', k === activeStep));
        const now = qs('.pc-now', sec);
        const bar = qs('.panel-count .bar span', sec);
        if (now) now.textContent = pad2(activeStep + 1);
        if (bar) bar.style.width = `${((activeStep + 1) / panels.length) * 100}%`;
        state.step = activeStep;
      }
    }

    /* the bar flips to paper only while a light band sits under it */
    const barY = nav.offsetHeight * 0.5;
    const overLight = bands.some((el) => {
      const r = el.getBoundingClientRect();
      return r.top <= barY && r.bottom >= barY;
    });
    nav.classList.toggle('is-solid', overLight);

    /* outro art: gentle settle */
    const outro = qs('.stage-outro .stage-art');
    if (outro) {
      const r = outro.getBoundingClientRect();
      if (r.top < vh && r.bottom > 0) {
        const p = clamp(1 - (r.top + r.height) / (vh + r.height));
        outro.style.transform = `scale(${1.04 + p * 0.05}) translate3d(0, ${p * -3}%, 0)`;
      }
    }

    requestAnimationFrame(render);
  };

  /* ------------------------------------------------------- smooth anchors */
  const scrollToTarget = (el) => {
    if (!el) return;
    const top = el.getBoundingClientRect().top + window.scrollY;
    window.scrollTo({ top, behavior: reduced.matches ? 'auto' : 'smooth' });
  };

  document.addEventListener('click', (e) => {
    const jump = e.target.closest('[data-jump], .chapter-rail a, .chapter-rail-inline a, .mobile-nav a[href^="#ch-"], #searchResults a[href^="#"]');
    if (jump) {
      const id = jump.dataset.jump || (jump.getAttribute('href') || '').replace('#', '');
      const el = id === 'top' ? qs('#top') : qs(`#ch-${id}`) || document.getElementById(id);
      if (el) {
        e.preventDefault();
        closeSearch();
        closeMobile();
        closeEditions();
        scrollToTarget(el);
      }
    }
    const plain = e.target.closest('a[href^="#"]:not([data-jump])');
    if (plain && !plain.closest('.search, .mobile-nav, .chapter-rail, .chapter-rail-inline')) {
      const id = plain.getAttribute('href');
      if (id.length > 1) {
        const el = document.getElementById(id.slice(1));
        if (el) { e.preventDefault(); scrollToTarget(el); }
      }
    }
  });

  qs('#scrollCue')?.addEventListener('click', () => scrollToTarget(chapterEls[0]));

  /* ------------------------------------------------------------ editions */
  const editionsBtn = qs('#editionsBtn');
  const editionsPanel = qs('#editionsPanel');
  const openEditions = (on) => {
    editionsPanel.hidden = !on;
    editionsBtn.setAttribute('aria-expanded', String(on));
  };
  function closeEditions() { if (editionsPanel && !editionsPanel.hidden) openEditions(false); }
  editionsBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    openEditions(editionsPanel.hidden);
  });
  document.addEventListener('click', (e) => {
    if (editionsPanel && !editionsPanel.hidden && !e.target.closest('#editionsPanel, #editionsBtn')) closeEditions();
  });

  /* -------------------------------------------------------------- search */
  const search = qs('#search');
  const searchInput = qs('#searchInput');
  const searchResults = qs('#searchResults');
  const searchBtn = qs('#searchBtn');
  let activeResult = 0;
  let results = [];

  const index = [];
  chapters.forEach((ch) => {
    index.push({ no: ch.roman, title: ch.title, sub: ch.kicker, href: `#ch-${ch.id}`, text: [ch.title, ch.kicker, ch.lead].join(' ') });
    ch.features.forEach((f) => {
      index.push({ no: ch.roman, title: f.t, sub: ch.title, href: `#ch-${ch.id}`, text: `${f.t} ${f.d} ${ch.title}` });
    });
  });

  const renderResults = (q) => {
    const term = q.trim().toLowerCase();
    results = (term ? index.filter((r) => r.text.toLowerCase().includes(term)) : index).slice(0, 24);
    activeResult = 0;
    searchResults.innerHTML = results.length
      ? results.map((r, i) => `<li><a href="${r.href}" class="${i === 0 ? 'is-active' : ''}">
          <span class="sr-no">${r.no}</span>${r.title}<span class="sr-sub">${r.sub}</span></a></li>`).join('')
      : `<li class="none">Nothing matches “${q.replace(/</g, '&lt;')}”. Try a chapter name, “checkout”, “inventory”, “agents”.</li>`;
  };

  function openSearch() {
    search.hidden = false;
    document.body.classList.add('is-locked');
    renderResults('');
    setTimeout(() => searchInput.focus(), 40);
  }
  function closeSearch() {
    if (!search || search.hidden) return;
    search.hidden = true;
    document.body.classList.remove('is-locked');
  }
  searchBtn?.addEventListener('click', (e) => { e.preventDefault(); openSearch(); });
  search?.addEventListener('click', (e) => { if (e.target === search) closeSearch(); });
  searchInput?.addEventListener('input', (e) => renderResults(e.target.value));
  searchInput?.addEventListener('keydown', (e) => {
    const links = qsa('a', searchResults);
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!links.length) return;
      activeResult = clamp(activeResult + (e.key === 'ArrowDown' ? 1 : -1), 0, links.length - 1);
      links.forEach((a, i) => a.classList.toggle('is-active', i === activeResult));
      links[activeResult].scrollIntoView({ block: 'nearest' });
    }
    if (e.key === 'Enter' && links[activeResult]) {
      e.preventDefault();
      links[activeResult].click();
    }
  });

  const isMac = /Mac|iPhone|iPad/.test(navigator.platform);
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      search.hidden ? openSearch() : closeSearch();
    }
    if (e.key === '/' && !e.metaKey && !e.ctrlKey && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault(); openSearch();
    }
    if (e.key === 'Escape') { closeSearch(); closeMobile(); closeEditions(); }
  });

  /* ---------------------------------------------------------- mobile nav */
  const burger = qs('#burger');
  const mobileNav = qs('#mobileNav');
  const openMobile = (on) => {
    mobileNav.hidden = !on;
    burger.setAttribute('aria-expanded', String(on));
    document.body.classList.toggle('is-locked', on);
  };
  function closeMobile() { if (mobileNav && !mobileNav.hidden) openMobile(false); }
  burger?.addEventListener('click', () => openMobile(mobileNav.hidden));

  /* -------------------------------------------------------------- reveal */
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) {
        en.target.classList.add('is-in');
        io.unobserve(en.target);
      }
    });
  }, { threshold: 0.18 });
  qsa('.chapter-quote, .outro-inner > *').forEach((el) => {
    el.classList.add('will-reveal');
    io.observe(el);
  });

  /* keyboard tip in the search footer */
  const foot = qs('.search-foot');
  if (foot) foot.innerHTML = `↑ ↓ to move · ↵ to open · <kbd>${isMac ? '⌘K' : 'Ctrl K'}</kbd> to toggle`;

  /* ----------------------------------------------------------------- boot */
  onScroll();
  requestAnimationFrame(render);
  document.body.classList.remove('is-loading');
  setActiveRail(chapters[0].id);
})();
