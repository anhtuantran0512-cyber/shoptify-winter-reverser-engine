/* =========================================================================
   SERICA — the motion engine
   A single rAF clock drives everything: inertial scrolling, scene entrances,
   scroll-timeline panels, pointer parallax, the ticker and the rail playhead.
   Reduced motion is respected at the root: everything becomes a cut.
   ========================================================================= */
(() => {
  'use strict';

  const DATA = window.SERICA;
  if (!DATA) return;
  const chapters = DATA.chapters;

  const qs = (s, r = document) => r.querySelector(s);
  const qsa = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const pad2 = (n) => String(n).padStart(2, '0');

  const mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mqTouch = window.matchMedia('(hover: none), (pointer: coarse)');
  const motionOK = () => !mqReduce.matches;
  const smoothOK = () => motionOK() && !mqTouch.matches;
  const body = document.body;

  /* =======================================================================
     0 · PRELOADER — counter, then two lacquer curtains split and the hero
     unmasks. (The reference page does the same "lights up" entrance.)
     ===================================================================== */
  const preloader = qs('#preloader');
  const preCount = qs('#preCount');
  const intro = { started: false, done: false };

  const runIntro = () => {
    if (intro.started) return;
    intro.started = true;
    if (!preloader || !motionOK()) {
      preloader?.classList.add('is-done', 'is-gone');
      body.classList.remove('is-loading');
      intro.done = true;
      playHeroIn();
      return;
    }
    let n = 0;
    const tick = () => {
      n = Math.min(100, n + Math.random() * 9 + 3);
      if (preCount) preCount.textContent = String(Math.round(n)).padStart(3, '0');
      if (n < 100) {
        setTimeout(tick, 90 + Math.random() * 70);
      } else {
        setTimeout(() => {
          preloader.classList.add('is-done');
          setTimeout(() => preloader.classList.add('is-gone'), 1150);
          body.classList.remove('is-loading');
          intro.done = true;
          playHeroIn();
        }, 260);
      }
    };
    tick();
  };

  /* =======================================================================
     1 · SMOOTH SCROLL — Lenis-style: wheel input is accumulated, the frame
     loop eases the real scroll position toward it, and every scene reads the
     eased value. Keyboard, scrollbar and touch stay native.
     ===================================================================== */
  const sc = { y: window.scrollY, ty: window.scrollY, lastWrite: window.scrollY, vel: 0, smoothedVel: 0 };
  const maxY = () => Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
  const locked = () => body.classList.contains('is-locked');

  const syncFromNative = () => {
    if (Math.abs(window.scrollY - sc.lastWrite) > 3) {
      sc.y = sc.ty = window.scrollY;
    }
  };
  window.addEventListener('scroll', syncFromNative, { passive: true });

  /* Wheel input stays native. Writing scrollTo every frame makes Chromium
     re-rasterise sticky scenes late, which shows as black bands mid-scroll, so
     the smoothness here comes from easing every scene value toward the page
     scroll instead of easing the scroll itself. */

  /* Anchor jumps use a view-transition style cut: the magenta band covers the
     screen, the page is repositioned while it is covered, then it retracts.
     This is what the reference does instead of a long animated scroll. */
  const jumpTo = (el) => {
    if (!el) return;
    const top = Math.round(Math.min(maxY(), Math.max(0, el.getBoundingClientRect().top + window.scrollY)));
    const wipe = qs('#wipe');
    const apply = () => {
      window.scrollTo({ top, behavior: 'auto' });
      sc.y = sc.ty = top;
      sc.lastReal = top;
      lastY = -1;               /* force the frame loop to re-read every scene */
      sc.smoothedVel = 0;
    };
    if (!motionOK() || !wipe) { apply(); return; }
    wipe.classList.remove('is-run');
    void wipe.offsetWidth;
    wipe.classList.add('is-run');
    setTimeout(apply, 330);
  };

  /* =======================================================================
     2 · DOM BUILD
     ===================================================================== */
  const host = qs('#chapters');
  const railOl = qs('#chapterRail ol');
  const mobileChapters = qs('#mobileChapters');
  const frag = document.createDocumentFragment();
  const railFrag = document.createDocumentFragment();
  const mobFrag = document.createDocumentFragment();
  const chapterHeight = (n) => 118 + Math.min(n, 22) * 24; // vh of scroll per chapter

  const railItem = (ch, cls = '') => {
    const li = document.createElement('li');
    li.innerHTML = `<a href="#ch-${ch.id}" data-jump="${ch.id}" class="${cls}">
        <span class="ch-name"></span><span class="rom">${ch.roman}</span></a>`;
    li.querySelector('.ch-name').textContent = ch.title;
    return li;
  };

  chapters.forEach((ch, i) => {
    railFrag.appendChild(railItem(ch, i === 0 ? 'is-active' : ''));

    const mobA = document.createElement('a');
    mobA.href = `#ch-${ch.id}`;
    mobA.innerHTML = `<small>${ch.roman}</small>${ch.title}`;
    mobFrag.appendChild(mobA);

    const sec = document.createElement('section');
    sec.className = 'chapter';
    sec.id = `ch-${ch.id}`;
    sec.dataset.theme = 'dark';
    sec.dataset.chapter = String(i);
    sec.dataset.tone = ch.tone || 'night';
    sec.style.setProperty('--panel-span', chapterHeight(ch.features.length) + 'vh');

    sec.innerHTML = `
      <div class="stick">
        <div class="stage-media">
          <img class="stage-art" src="${ch.art}" alt="Chapter ${ch.roman}, ${ch.title}: a new Renaissance painting. ${ch.alt || ''}" loading="${i < 2 ? 'eager' : 'lazy'}" decoding="async">
          <div class="stage-light" aria-hidden="true"></div>
          <div class="stage-scrim"></div>
        </div>
        <div class="chapter-inner">
          <div class="chapter-view">
            <p class="mini-lockup" aria-hidden="true">The<br><span>La/</span>quer<br>Edition</p>
            <div class="panels" role="list"></div>
            <div class="chapter-titlewrap">
              <p class="chapter-kicker"><b>${ch.roman}</b> ${ch.kicker}</p>
              <h2 class="chapter-title"><span class="mask"><span class="mask-inner">${ch.title}</span></span></h2>
              <p class="chapter-lead" data-words></p>
            </div>
            <nav class="chapter-rail-inline" aria-label="Chapters"><ol></ol></nav>
            <div class="panel-count">
              <span class="pc-now">01</span>
              <span class="bar"><span></span></span>
              <span class="pc-all">${pad2(Math.max(ch.features.length, 1))}</span>
            </div>
          </div>
        </div>
      </div>`;

    /* lead copy is split into words so it can rise in sequence */
    const lead = qs('.chapter-lead', sec);
    lead.innerHTML = ch.lead
      .split(' ')
      .map((w, k) => `<span class="w" style="--d:${k * 22}ms">${w}</span>`)
      .join(' ');

    const panelBox = qs('.panels', sec);
    ch.features.forEach((f) => {
      const p = document.createElement('article');
      p.className = 'panel';
      p.setAttribute('role', 'listitem');
      p.innerHTML = `
        <div class="panel-meta" style="--i:0"><span>${ch.title} — ${pad2(ch.features.indexOf(f) + 1)} / ${pad2(ch.features.length)}</span><b>New</b></div>
        <h3 style="--i:1">${f.t}</h3>
        <p style="--i:2">${f.d}</p>
        ${f.cta ? `<a class="panel-cta" style="--i:3" href="${f.cta}" target="_blank" rel="noopener">Read help doc <span aria-hidden="true">↗</span></a>` : ''}`;
      panelBox.appendChild(p);
    });

    qs('.chapter-rail-inline ol', sec).appendChild(railFrag.cloneNode(true));

    const quote = document.createElement('div');
    quote.className = 'chapter-quote';
    quote.dataset.tone = ch.tone || 'night';
    quote.innerHTML = `
      <div class="quote-inner">
        <span class="quote-mark" aria-hidden="true">”</span>
        <p>${ch.lead}</p>
        <span class="quote-src">${ch.roman} · ${ch.kicker} · Serica Editions Winter ’26</span>
      </div>
      <div class="quote-ticker" aria-hidden="true"><div class="ticker-track"></div></div>`;

    frag.appendChild(sec);
    frag.appendChild(quote);
  });

  host.replaceChildren(frag);
  railOl.appendChild(railFrag);
  mobileChapters.appendChild(mobFrag);

  /* ticker content: one long line, repeated */
  const tickerWords = ['Serica Editions', 'Winter ’26', 'The Lacquer Edition', '150+ product updates', 'Paper · Ink · Magenta'];
  const tickerHTML = Array.from({ length: 4 }, () => tickerWords
    .map((w) => `<span>${w}</span><i aria-hidden="true">✦</i>`).join(''))
    .join('');
  qsa('.ticker-track').forEach((t) => { t.innerHTML = tickerHTML; });
  const heroTicker = qs('#heroTicker .ticker-track');
  if (heroTicker) heroTicker.innerHTML = tickerHTML;

  const allRailLinks = () => qsa('.chapter-rail a, .chapter-rail-inline a');

  /* =======================================================================
     3 · SCENE REGISTRY
     ===================================================================== */
  const nav = qs('#nav');
  const progressBar = qs('#progressBar');
  const hero = qs('.stage-hero');
  const heroArt = qs('.stage-hero .stage-art');
  const heroLockup = qs('.hero-lockup');
  const heroRail = qs('.chapter-rail');
  const outro = qs('.stage-outro');
  const outroArt = qs('.stage-outro .stage-art');
  const bands = qsa('.chapter-quote').concat(outro ? [outro] : []);

  const scenes = chapters.map((ch, i) => {
    const sec = qs(`#ch-${ch.id}`);
    return {
      ch, i, sec,
      art: qs('.stage-art', sec),
      light: qs('.stage-light', sec),
      scrim: qs('.stage-scrim', sec),
      view: qs('.chapter-view', sec),
      title: qs('.chapter-title', sec),
      titleInner: qs('.chapter-title .mask-inner', sec),
      lead: qs('.chapter-lead', sec),
      rail: qs('.chapter-rail-inline', sec),
      panels: qsa('.panel', sec),
      counter: qs('.pc-now', sec),
      counterBar: qs('.panel-count .bar span', sec),
      step: -1,
      on: false,
      mouse: { x: 0, y: 0, tx: 0, ty: 0 },
    };
  });

  /* who owns the rail, the HUD, the panel timeline */
  let active = scenes[0];
  let activeIndex = 0;

  /* =======================================================================
     4 · POINTER — parallax + magnetic buttons + the cursor ring
     ===================================================================== */
  const pointer = {
    x: window.innerWidth / 2, y: window.innerHeight / 2,
    tx: window.innerWidth / 2, ty: window.innerHeight / 2,
    nx: 0, ny: 0,
  };
  const cursor = qs('#cursor');
  const cursorDot = qs('#cursorDot');

  if (!mqTouch.matches) {
    window.addEventListener('pointermove', (e) => {
      pointer.tx = e.clientX;
      pointer.ty = e.clientY;
      pointer.nx = (e.clientX / window.innerWidth) * 2 - 1;
      pointer.ny = (e.clientY / window.innerHeight) * 2 - 1;
      if (cursorDot) {
        cursorDot.style.setProperty('--cx', `${e.clientX}px`);
        cursorDot.style.setProperty('--cy', `${e.clientY}px`);
      }
      /* each scene eases its own parallax toward the pointer */
      scenes.forEach((s) => { s.mouse.tx = pointer.nx; s.mouse.ty = pointer.ny; });
    }, { passive: true });

    document.addEventListener('pointerover', (e) => {
      const hot = e.target.closest('a, button, .panel, .chapter-rail a, .editions-panel a');
      cursor?.classList.toggle('is-hot', !!hot);
    });

    /* magnetic buttons: pull toward the pointer when it is near */
    qsa('.btn-pill, .btn-line, .nav-button').forEach((btn) => {
      btn.addEventListener('pointermove', (e) => {
        if (!motionOK()) return;
        const r = btn.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2);
        const dy = e.clientY - (r.top + r.height / 2);
        btn.style.transform = `translate3d(${dx * 0.16}px, ${dy * 0.22}px, 0)`;
      });
      btn.addEventListener('pointerleave', () => { btn.style.transform = ''; });
    });
  }

  /* =======================================================================
     5 · REVEALS — anything with [data-reveal] enters once it is in view
     ===================================================================== */
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) {
        en.target.classList.add('is-in');
        io.unobserve(en.target);
      }
    });
  }, { threshold: 0.16, rootMargin: '0px 0px -8% 0px' });
  qsa('[data-reveal], .chapter-quote .quote-inner, .outro-inner > *').forEach((el) => io.observe(el));

  /* =======================================================================
     6 · HERO — title masks, art settle, pointer depth, scroll parallax
     ===================================================================== */
  const splitHeroTitle = () => {
    const h1 = qs('.hero-title');
    if (!h1 || h1.dataset.split) return;
    h1.dataset.split = '1';
    const parts = h1.innerHTML.split(/<br\s*\/?>/i);
    h1.innerHTML = parts
      .map((p, i) => `<span class="mask"><span class="mask-inner" style="--d:${120 + i * 110}ms">${p}</span></span>`)
      .join('');
  };
  splitHeroTitle();

  const playHeroIn = () => {
    if (!hero) return;
    hero.classList.add('is-in');
    qsa('.hero-title .mask-inner', hero).forEach((el) => el.classList.add('is-in'));
    setTimeout(() => qsa('.hero-lockup [data-hero]', hero).forEach((el) => el.classList.add('is-in')), 220);
  };

  /* =======================================================================
     7 · THE FRAME LOOP
     ===================================================================== */

  const setActive = (scene) => {
    if (!scene || scene.on) return;
    /* leave the previous scene: panels fade, the wordmark drops back */
    if (active && active !== scene) {
      active.on = false;
      active.view.classList.remove('is-on');
      active.rail.classList.remove('is-on');
      active.panels.forEach((p) => p.classList.remove('is-on'));
      active.step = -1;
      setActiveRail('', active);
    }
    active = scene;
    active.on = true;
    active.view.classList.add('is-on');
    active.rail.classList.add('is-on');
    /* every copy of the numeral rail follows */
    allRailLinks().forEach((a) => {
      const id = a.dataset.jump || a.getAttribute('href')?.replace('#ch-', '');
      a.classList.toggle('is-active', id === scene.ch.id);
    });
  };

  const setActiveRail = (id, scene) => {
    allRailLinks().forEach((a) => {
      const linkId = a.dataset.jump || a.getAttribute('href')?.replace('#ch-', '');
      a.classList.toggle('is-active', !!id && linkId === id);
      if (!id) a.style.removeProperty('--p');
    });
    if (scene) {
      const p = scene.progress ?? 0;
      qsa(`.chapter-rail-inline a[data-jump="${scene.ch.id}"]`).forEach((a) => a.style.setProperty('--p', p.toFixed(3)));
      const hero = qs(`.chapter-rail a[data-jump="${scene.ch.id}"]`);
      hero?.style.setProperty('--p', p.toFixed(3));
    }
  };

  /* =======================================================================
     7b · THE FRAME LOOP (scene-driven)
     The scroll is native; the loop only reacts when the page moves. Every
     full-screen transform is applied once per scene change — never per frame —
     so sticky scenes stay on their own compositor layer and paint cleanly.
     ===================================================================== */
  let lastY = -1;
  let tickerX = 0;
  let lastT = performance.now();
  let introProgress = 0;

  const enterScene = (s) => {
    if (!s || s.entered) return;
    s.entered = true;
    s.sec.classList.add('is-entered');
    s.view.classList.add('is-on');
    s.rail.classList.add('is-on');
    allRailLinks().forEach((a) => {
      const id = a.dataset.jump || (a.getAttribute('href') || '').replace('#ch-', '');
      a.classList.toggle('is-active', id === s.ch.id);
    });
  };

  const leaveScene = (s) => {
    if (!s || !s.entered) return;
    s.entered = false;
    s.view.classList.remove('is-on');
    s.rail.classList.remove('is-on');
    s.sec.classList.remove('is-entered');
  };

  /* per-chapter scroll work: only the pinned chapter, only on real movement */
  const readChapters = () => {
    let pinned = null;
    let pinnedIndex = -1;
    scenes.forEach((s, i) => {
      const rect = s.sec.getBoundingClientRect();
      /* the section enters the viewport: mount the scene once */
      if (rect.top < window.innerHeight * 1.05 && rect.bottom > 0) enterScene(s);
      if (rect.top <= 1 && rect.bottom > window.innerHeight) { pinned = s; pinnedIndex = i; }
    });
    if (!pinned) return;

    const rect = pinned.sec.getBoundingClientRect();
    const span = rect.height - window.innerHeight;
    const p = span > 0 ? clamp(-rect.top / span) : 0;

    /* panel timeline */
    const n = pinned.panels.length;
    const step = Math.min(n - 1, Math.floor(clamp((p - 0.015) / 0.955) * n));
    if (step !== pinned.step) {
      pinned.panels.forEach((el, k) => {
        el.classList.toggle('is-on', k === step);
        el.classList.toggle('is-out', k < step);
      });
      pinned.counter.textContent = pad2(step + 1);
      pinned.counterBar.style.width = `${((step + 1) / n) * 100}%`;
      pinned.step = step;
    }

    /* the wordmark tightens and drifts as the pinned scene is consumed */
    pinned.title.style.transform = `translate3d(0, ${(-26 * p).toFixed(1)}px, 0)`;
    pinned.title.style.letterSpacing = `${(-0.055 + p * 0.012).toFixed(4)}em`;
    pinned.rail.style.opacity = String(clamp(1 - p * 1.15, 0.15, 1));

    /* the active scene tracks the run of its own numerals */
    if (pinned !== active) active = pinned;
    activeIndex = pinnedIndex;
  };

  const frame = (now) => {
    const dt = Math.min(50, now - lastT) || 16;
    lastT = now;
    const vh = window.innerHeight;
    const y = window.scrollY;
    const moved = Math.abs(y - lastY) > 0.5;
    const smooth = smoothOK();

    /* tickers run on their own clock; the scroll only nudges their speed */
    const speed = 0.5 + Math.min(2.2, Math.abs(sc.smoothedVel) * 0.35);
    tickerX -= speed * (dt / 16.67);
    qsa('.ticker-track').forEach((t) => {
      const w = t.scrollWidth / 2 || 1;
      if (-tickerX > w) tickerX += w;
      t.style.transform = `translate3d(${tickerX.toFixed(2)}px, 0, 0)`;
    });

    if (moved) {
      lastY = y;
      sc.vel = y - (sc.lastReal ?? y);
      sc.lastReal = y;
      sc.smoothedVel = lerp(sc.smoothedVel, sc.vel, 0.2);

      /* progress hairline */
      const max = Math.max(1, maxY());
      progressBar.style.transform = `scaleX(${clamp(y / max).toFixed(5)})`;

      /* nav hides on the way down, returns on the way up */
      nav.classList.toggle('is-hidden', y > vh * 0.9 && sc.smoothedVel > 3);
      nav.classList.toggle('is-top', y < 40);

      /* hero: native parallax, applied once per change */
      if (hero) {
        const p = clamp(y / (vh * 1.05));
        if (heroLockup) {
          heroLockup.style.transform = `translate3d(0, ${(p * -72).toFixed(1)}px, 0)`;
          heroLockup.style.opacity = String(clamp(1 - p * 1.45));
        }
        if (heroArt) heroArt.style.transform = `translate3d(0, ${(p * 9).toFixed(2)}%, 0) scale(${(1.1 + p * 0.07).toFixed(3)})`;
        if (heroRail) {
          heroRail.style.transform = `translate3d(${(p * 44).toFixed(1)}px, -50%, 0)`;
          heroRail.style.opacity = String(clamp(1 - p * 1.5));
        }
      }

      readChapters();

      /* light bands flip the bar to ink-on-paper */
      const barY = nav.offsetHeight * 0.5;
      nav.classList.toggle('is-solid', bands.some((el) => {
        const r = el.getBoundingClientRect();
        return r.top <= barY && r.bottom >= barY;
      }));

      /* quote bands drift a little slower than the page */
      qsa('.chapter-quote').forEach((q) => {
        const r = q.getBoundingClientRect();
        if (r.top > vh || r.bottom < 0) return;
        const inner = q.querySelector('.quote-inner');
        if (inner) inner.style.transform = `translate3d(0, ${(((r.top + r.height / 2) - vh / 2) / vh * -26).toFixed(1)}px, 0)`;
      });

      /* outro settles in */
      if (outro) {
        const r = outro.getBoundingClientRect();
        if (r.top < vh && r.bottom > 0) {
          const p = clamp(1 - (r.top + r.height) / (vh + r.height));
          if (outroArt) outroArt.style.transform = `translate3d(0, ${(p * -3).toFixed(2)}%, 0) scale(${(1.03 + p * 0.05).toFixed(3)})`;
        }
      }
    }

    /* the cursor ring trails the pointer independently of scrolling */
    if (smooth) {
      pointer.x = lerp(pointer.x, pointer.tx, 0.16);
      pointer.y = lerp(pointer.y, pointer.ty, 0.16);
      if (cursor) {
        cursor.style.setProperty('--cx', `${pointer.x.toFixed(1)}px`);
        cursor.style.setProperty('--cy', `${pointer.y.toFixed(1)}px`);
      }
      if (heroArt) {
        const p = clamp(lastY / (vh * 1.05));
        heroArt.style.transform = `translate3d(${(pointer.nx * 1.2).toFixed(2)}%, ${(pointer.ny * 1 + p * 9).toFixed(2)}%, 0) scale(${(1.1 + p * 0.07).toFixed(3)})`;
      }
    }

    requestAnimationFrame(frame);
  };


  /* =======================================================================
     8 · LINKS — anchors, rails, ticker jumps
     ===================================================================== */
  const closeAll = () => { closeSearch(); closeMobile(); closeEditions(); };

  document.addEventListener('click', (e) => {
    const jump = e.target.closest('[data-jump], .chapter-rail a, .chapter-rail-inline a, .mobile-nav a[href^="#ch-"], #searchResults a[href^="#"]');
    if (jump) {
      const id = jump.dataset.jump || (jump.getAttribute('href') || '').replace('#', '').replace('ch-', '');
      const target = id === 'top' ? qs('#top') : qs(`#ch-${id}`);
      if (target) { e.preventDefault(); closeAll(); jumpTo(target); return; }
    }
    const plain = e.target.closest('a[href^="#"]');
    if (plain && !plain.closest('.search, .mobile-nav')) {
      const id = plain.getAttribute('href');
      if (id.length > 1) {
        const el = document.getElementById(id.slice(1));
        if (el) { e.preventDefault(); closeAll(); jumpTo(el); }
      }
    }
  });

  qs('#scrollCue')?.addEventListener('click', () => jumpTo(scenes[0].sec));

  /* =======================================================================
     9 · NAV — editions dropdown, search palette, mobile sheet
     ===================================================================== */
  const editionsBtn = qs('#editionsBtn');
  const editionsPanel = qs('#editionsPanel');
  const openEditions = (on) => {
    editionsPanel.hidden = !on;
    editionsBtn.setAttribute('aria-expanded', String(on));
  };
  function closeEditions() { if (editionsPanel && !editionsPanel.hidden) openEditions(false); }
  editionsBtn?.addEventListener('click', (e) => { e.stopPropagation(); openEditions(editionsPanel.hidden); });
  document.addEventListener('click', (e) => {
    if (editionsPanel && !editionsPanel.hidden && !e.target.closest('#editionsPanel, #editionsBtn')) closeEditions();
  });

  const search = qs('#search');
  const searchInput = qs('#searchInput');
  const searchResults = qs('#searchResults');
  const searchBtn = qs('#searchBtn');
  let activeResult = 0;
  let results = [];

  const index = [];
  chapters.forEach((ch) => {
    index.push({ no: ch.roman, title: ch.title, sub: ch.kicker, href: `#ch-${ch.id}`, text: [ch.title, ch.kicker, ch.lead].join(' ') });
    ch.features.forEach((f) => index.push({ no: ch.roman, title: f.t, sub: ch.title, href: `#ch-${ch.id}`, text: `${f.t} ${f.d} ${ch.title}` }));
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
    body.classList.add('is-locked');
    renderResults('');
    setTimeout(() => searchInput.focus(), 60);
  }
  function closeSearch() {
    if (!search || search.hidden) return;
    search.hidden = true;
    body.classList.remove('is-locked');
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
    if (e.key === 'Enter' && links[activeResult]) { e.preventDefault(); links[activeResult].click(); }
  });

  const burger = qs('#burger');
  const mobileNav = qs('#mobileNav');
  const openMobile = (on) => {
    mobileNav.hidden = !on;
    burger.setAttribute('aria-expanded', String(on));
    nav.classList.toggle('is-raised', on);
    body.classList.toggle('is-locked', on);
  };
  function closeMobile() { if (mobileNav && !mobileNav.hidden) openMobile(false); }
  burger?.addEventListener('click', () => openMobile(mobileNav.hidden));

  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      search.hidden ? openSearch() : closeSearch();
    }
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') { e.preventDefault(); openSearch(); }
    if (e.key === 'Escape') closeAll();
  });

  /* =======================================================================
     10 · BOOT
     ===================================================================== */
  window.addEventListener('resize', () => { sc.y = window.scrollY; });

  setActiveRail(scenes[0].ch.id, scenes[0]);
  requestAnimationFrame((t) => { lastT = t; frame(t); });

  /* the preloader runs on load, with a hard fallback so it can never trap */
  if (document.readyState === 'complete') runIntro();
  else window.addEventListener('load', runIntro);
  setTimeout(runIntro, 2600);
})();
