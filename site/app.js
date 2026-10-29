/* Shoptify vault — rendering + interaction. No framework, no network. */
(() => {
  const D = window.SHOPTIFY;
  if (!D) return;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const bytes = (n) => (n > 1048576 ? (n / 1048576).toFixed(1) + ' MB' : n > 1024 ? Math.round(n / 1024) + ' KB' : n + ' B');

  /* ------------------------------------------------------------- ledger -- */
  const ledger = [
    ['Files captured', D.stats.files, 'public front-end resources'],
    ['Payload', D.stats.size, 'CSS, JS, fonts, Rive, media'],
    ['Product updates', D.stats.features, 'across twelve chapters'],
    ['Page height', D.stats.pageHeight.toLocaleString('en-US') + ' px', 'one scroll-driven narrative'],
    ['Chapters', D.stats.chapters, 'Sidekick → Developer'],
  ];
  $('#ledger').innerHTML = ledger
    .map(([k, v, sub]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}<small>${esc(sub)}</small></dd></div>`)
    .join('');

  $$('[data-bind]').forEach((el) => {
    const path = el.dataset.bind.split('.');
    const val = path.reduce((o, k) => (o ? o[k] : ''), D);
    if (val) el.textContent = val;
  });
  $$('[data-bind-src]').forEach((el) => {
    const val = D[el.dataset.bindSrc];
    if (val) el.src = val;
  });

  /* --------------------------------------------------------------- rail -- */
  const navItems = [
    ['overview', 'Overview'],
    ['stack', 'Stack'],
    ['design', 'Design'],
    ['chapters', 'Chapters'],
    ['assets', 'Assets'],
    ['code', 'Code'],
    ['notes', 'Notes'],
  ];
  $('#railNav').innerHTML = navItems
    .map(([id, label]) => `<a class="rail-link" href="#${id}" data-rail="${id}">${esc(label)}</a>`)
    .join('');

  /* -------------------------------------------------------------- stack -- */
  $('#stackGrid').innerHTML = D.tokens.stack
    .map(
      (s, i) => `<article class="stack-card">
        <span class="tag">0${i + 1}</span>
        <h3>${esc(s.name)}</h3>
        <p>${esc(s.detail)}</p>
      </article>`
    )
    .join('');

  const maxBundle = Math.max(...D.bundles.map((b) => b.bytes));
  $('#bundleList').innerHTML = D.bundles
    .map(
      (b) => `<li class="bar-row">
        <span class="bar-name" title="${esc(b.name)}">${esc(b.name)}</span>
        <span class="bar-size">${bytes(b.bytes)}</span>
        <span class="bar-track"><span class="bar-fill" style="width:${Math.max(2, (b.bytes / maxBundle) * 100)}%"></span></span>
      </li>`
    )
    .join('');

  $('#routeCount').textContent = D.routes.length + ' routes';
  $('#routeList').innerHTML = D.routes
    .map(
      (r) => `<li><code>${esc(r.path || '/')}</code><span>${r.hasLoader ? 'loader' : 'static'}</span></li>`
    )
    .join('');

  /* ------------------------------------------------------------- design -- */
  $('#paletteRow').innerHTML = D.tokens.colors
    .map(
      (c) => `<div class="swatch">
        <i style="background:${esc(c.hex)}"></i>
        <b>${esc(c.name)}</b>
        <code>${esc(c.hex)}</code>
        <em>${esc(c.use)}</em>
      </div>`
    )
    .join('');

  const specimenClass = (name) =>
    name.startsWith('Neue') ? 's-headline' : name.startsWith('HW') ? 's-serif' : name.startsWith('Imperial') ? 's-script' : 's-ui';
  const specimenSize = (name, cls) =>
    name.startsWith('Neue') ? (cls === 'headline-1' ? 'clamp(3rem, 8vw, 7.2rem)' : 'clamp(1.8rem, 4vw, 3.2rem)')
      : name.startsWith('HW') ? 'clamp(1.8rem, 4.4vw, 3.4rem)'
      : name.startsWith('Imperial') ? 'clamp(2.6rem, 7vw, 5.4rem)'
      : '1.5rem';

  $('#typeSpecimens').innerHTML = D.tokens.type
    .map(
      (t) => `<div class="specimen">
        <div class="specimen-sample ${specimenClass(t.name)}" style="font-size:${specimenSize(t.name, t.class)}">${esc(t.sample)}</div>
        <div class="specimen-meta">
          <b>${esc(t.name)}</b>
          ${esc(t.font)}<br>
          <code>${esc(t.class)}</code> · ${esc(t.size)}<br>
          lh ${esc(t.lh)} · ls ${esc(t.ls)}
        </div>
      </div>`
    )
    .join('');

  $('#layoutList').innerHTML = D.tokens.layout
    .map((r) => `<dt>${esc(r.k)}</dt><dd>${esc(r.v)}</dd>`)
    .join('');

  const bezierPath = (c) => {
    const m = c.match(/cubic-bezier\(([^)]+)\)/);
    if (!m) return 'M2 24 C 30 24, 44 2, 72 2';
    const [x1, y1, x2, y2] = m[1].split(',').map((n) => parseFloat(n));
    const X = (v) => 2 + v * 68;
    const Y = (v) => 24 - v * 22;
    return `M2 24 C ${X(x1).toFixed(1)} ${Y(y1).toFixed(1)}, ${X(x2).toFixed(1)} ${Y(y2).toFixed(1)}, 70 2`;
  };
  $('#motionList').innerHTML = D.tokens.motion
    .map(
      (m) => `<li>
        <svg viewBox="0 0 72 26" aria-hidden="true"><path d="${bezierPath(m.curve)}" fill="none" stroke="currentColor" stroke-width="1.4"/><circle cx="70" cy="2" r="2" fill="#ea1360"/></svg>
        <div><b>${esc(m.name)}</b><span>${esc(m.curve)}</span></div>
        <em>${esc(m.dur)}<br>${esc(m.use)}</em>
      </li>`
    )
    .join('');

  /* ----------------------------------------------------------- chapters -- */
  const list = $('#chapterList');
  const detail = $('#chapterDetail');
  let activeChapter = 0;

  list.innerHTML = D.chapters
    .map(
      (c, i) => `<li><button class="chapter-btn${i === 0 ? ' is-active' : ''}" data-chapter="${i}" type="button">
        <span class="no">${c.roman}</span>
        <span class="name">${esc(c.title)}</span>
        <span class="count">${c.featureCount} updates</span>
      </button></li>`
    )
    .join('');

  const renderChapter = (i) => {
    const c = D.chapters[i];
    activeChapter = i;
    $$('.chapter-btn').forEach((b) => b.classList.toggle('is-active', Number(b.dataset.chapter) === i));
    detail.innerHTML = `
      <figure>
        <img src="${esc(c.shot)}" alt="Reference frame for the ${esc(c.title)} chapter" loading="lazy">
        <figcaption><span>Chapter ${c.roman} — ${esc(c.title)}</span><span>${c.heightPx.toLocaleString('en-US')} px of scroll</span></figcaption>
      </figure>
      <p class="detail-lead">${esc(c.lead)}</p>
      <p class="detail-note">${esc(c.note)}</p>
      <ul class="feature-list">
        ${c.features
          .map(
            (f, n) => `<li><span>${String(n + 1).padStart(2, '0')}</span><div><b>${esc(f.title)}</b><p>${esc(f.description)}</p></div></li>`
          )
          .join('')}
      </ul>
      <div class="detail-foot">
        <span class="pill pill-accent">${c.featureCount} updates</span>
        <span class="pill">${c.links.length} links</span>
        <span class="pill">${c.images.length} media refs</span>
        ${c.groups.slice(0, 3).map((g) => `<span class="pill">${esc(g)}</span>`).join('')}
      </div>`;
  };
  renderChapter(0);
  list.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-chapter]');
    if (btn) renderChapter(Number(btn.dataset.chapter));
  });

  /* ------------------------------------------------------------- assets -- */
  const kinds = [
    ['all', 'All'],
    ['chapters', 'Chapter frames'],
    ['images', 'Images'],
    ['rive', 'Rive'],
    ['fonts', 'Fonts'],
    ['video', 'Video'],
    ['code', 'Code'],
  ];
  let kind = 'images';
  let query = '';
  let shown = 0;
  const PAGE = 48;

  $('#assetTabs').innerHTML = kinds
    .map(([k, label], i) => `<button class="chip${i === 2 ? ' is-active' : ''}" data-kind="${k}" type="button" role="tab" aria-selected="${i === 2}">${label}</button>`)
    .join('');

  const itemsFor = () => {
    const q = query.toLowerCase();
    let items = [];
    if (kind === 'chapters' || kind === 'all') {
      items.push(...D.shotList.map((s) => ({ type: 'image', src: s.path, name: s.stem + '.webp', label: 'Chapter frame' })));
    }
    if (kind === 'images' || kind === 'all') {
      items.push(...D.assets.images.files.map((n) => ({ type: 'image', src: '../assets/images/' + encodeURIComponent(n), name: n, label: 'Image' })));
    }
    if (kind === 'rive' || kind === 'all') {
      items.push(...D.assets.rive.files.map((n) => ({ type: 'file', src: '../assets/rive/' + encodeURIComponent(n), name: n, label: 'Rive animation', glyph: '◈' })));
    }
    if (kind === 'fonts' || kind === 'all') {
      items.push(...D.assets.fonts.files.map((n) => ({ type: 'file', src: '../assets/fonts/' + encodeURIComponent(n), name: n, label: 'Font file', glyph: 'Aa' })));
    }
    if (kind === 'video' || kind === 'all') {
      items.push(...D.assets.video.files.map((n) => ({ type: 'video', src: '../assets/video/' + encodeURIComponent(n), name: n, label: 'Film loop' })));
    }
    if (kind === 'code' || kind === 'all') {
      items.push(...D.bundles.map((b) => ({ type: 'file', src: '../assets/js/' + encodeURIComponent(b.name), name: b.name, label: bytes(b.bytes) + ' bundle', glyph: '{}' })));
    }
    return q ? items.filter((i) => i.name.toLowerCase().includes(q)) : items;
  };

  const tile = (it) => {
    if (it.type === 'image') {
      return `<figure class="asset-card" data-img="${esc(it.src)}" data-name="${esc(it.name)}">
        <img src="${esc(it.src)}" alt="${esc(it.name)}" loading="lazy" decoding="async">
        <figcaption><span>${esc(it.name.length > 34 ? it.name.slice(0, 31) + '…' : it.name)}</span><span>${esc(it.label)}</span></figcaption>
      </figure>`;
    }
    if (it.type === 'video') {
      return `<figure class="asset-card asset-card--file">
        <video src="${esc(it.src)}" muted loop playsinline preload="none" controls></video>
        <figcaption><span>${esc(it.name.length > 30 ? it.name.slice(0, 27) + '…' : it.name)}</span><span>${esc(it.label)}</span></figcaption>
      </figure>`;
    }
    return `<article class="asset-card asset-card--file">
      <div><span class="file-glyph">${esc(it.glyph || '·')}</span><h4>${esc(it.name)}</h4><p>${esc(it.label)}</p></div>
      <a class="file-link" href="${esc(it.src)}" target="_blank" rel="noopener" download>Open local file ↗</a>
    </article>`;
  };

  const renderAssets = (reset = false) => {
    const items = itemsFor();
    if (reset) shown = 0;
    const slice = items.slice(0, shown + PAGE);
    shown = slice.length;
    $('#assetGrid').innerHTML = slice.map(tile).join('');
    $('#assetCount').textContent = `${items.length} file${items.length === 1 ? '' : 's'} · showing ${slice.length}${items.length ? '' : ' — empty'}`;
    $('#assetEmpty').hidden = items.length !== 0;
    $('#loadMore').hidden = shown >= items.length;
    $('#assetGrid').hidden = items.length === 0;
  };
  renderAssets(true);

  $('#assetTabs').addEventListener('click', (e) => {
    const chip = e.target.closest('[data-kind]');
    if (!chip) return;
    kind = chip.dataset.kind;
    $$('#assetTabs .chip').forEach((c) => {
      c.classList.toggle('is-active', c === chip);
      c.setAttribute('aria-selected', c === chip);
    });
    renderAssets(true);
  });
  $('#assetSearch').addEventListener('input', (e) => {
    query = e.target.value.trim();
    renderAssets(true);
  });
  $('#assetReset').addEventListener('click', () => {
    query = '';
    kind = 'images';
    $('#assetSearch').value = '';
    $$('#assetTabs .chip').forEach((c) => c.classList.toggle('is-active', c.dataset.kind === 'images'));
    renderAssets(true);
  });
  $('#loadMore').addEventListener('click', () => renderAssets(false));

  const lightbox = $('#lightbox');
  const openLightbox = (src, name) => {
    $('#lightboxImg').src = src;
    $('#lightboxImg').alt = name;
    $('#lightboxCap').textContent = name + ' — local capture';
    lightbox.hidden = false;
  };
  $('#assetGrid').addEventListener('click', (e) => {
    const fig = e.target.closest('[data-img]');
    if (fig) openLightbox(fig.dataset.img, fig.dataset.name);
  });
  $('#assetGrid').addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG') {
      e.target.closest('.asset-card')?.classList.add('is-broken');
      e.target.replaceWith(Object.assign(document.createElement('div'), {
        className: 'asset-broken',
        textContent: 'preview unavailable',
      }));
    }
  }, true);
  $('#lightboxClose').addEventListener('click', () => (lightbox.hidden = true));
  lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) lightbox.hidden = true;
  });

  /* --------------------------------------------------------------- code -- */
  $('#replay').innerHTML = `<span class="c"># 1. open the page in Camoufox</span>
<span class="p">$</span> camofox open "https://www.shopify.com/editions/winter2026"

<span class="c"># 2. read the live DOM + performance entries</span>
<span class="p">$</span> python3 scripts/extract_page.py &lt;tabId&gt;

<span class="c"># 3. build the asset inventory from the SSR snapshot</span>
<span class="p">$</span> python3 scripts/build_inventory.py

<span class="c"># 4. download what the browser was served</span>
<span class="p">$</span> python3 scripts/capture_assets.py snapshot/inventory.json assets

<span class="c"># 5. regenerate this index</span>
<span class="p">$</span> python3 scripts/build_site_data.py`;

  $('#docsList').innerHTML = D.docs
    .map((d) => `<li><a href="../${esc(d.path)}" target="_blank" rel="noopener">${esc(d.name)}<span>${esc(d.path)}</span></a></li>`)
    .join('');

  $('#footMeta').textContent = `${D.stats.files} files · ${D.stats.size} · captured ${new Date(D.meta.capturedAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}`;
  $('#freshness').textContent = `Captured ${new Date(D.meta.capturedAt).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })}. CDN hashes change with every deploy, so treat filenames as a timestamp, not an API.`;

  /* ------------------------------------------------------------ command -- */
  const cmdk = $('#cmdk');
  const field = $('#cmdkField');
  const results = $('#cmdkResults');
  const commands = [
    ...D.chapters.map((c) => ({ label: `${c.roman} — ${c.title}`, kind: 'Chapter', run: () => { location.hash = '#chapters'; renderChapter(c.index - 1); } })),
    ...D.docs.map((d) => ({ label: d.name, kind: 'Document', run: () => window.open('../' + d.path, '_blank') })),
    ...navItems.map(([id, label]) => ({ label, kind: 'Section', run: () => (location.hash = '#' + id) })),
    { label: 'Asset vault — images', kind: 'View', run: () => { location.hash = '#assets'; kind = 'images'; $('#assetSearch').value = ''; renderAssets(true); } },
    { label: 'Asset vault — Rive files', kind: 'View', run: () => { location.hash = '#assets'; kind = 'rive'; renderAssets(true); } },
  ];
  let cmdkSel = 0;
  const drawCmdk = () => {
    const q = field.value.trim().toLowerCase();
    const hits = commands.filter((c) => (c.label + c.kind).toLowerCase().includes(q)).slice(0, 9);
    cmdkSel = Math.min(cmdkSel, Math.max(0, hits.length - 1));
    results.innerHTML = hits.length
      ? hits.map((c, i) => `<li><button type="button" data-cmd="${commands.indexOf(c)}" class="${i === cmdkSel ? 'is-sel' : ''}">${esc(c.label)}<em>${esc(c.kind)}</em></button></li>`).join('')
      : '<li class="cmdk-empty">No chapter, document or view matches that.</li>';
  };
  const openCmdk = () => {
    cmdk.hidden = false;
    field.value = '';
    cmdkSel = 0;
    drawCmdk();
    setTimeout(() => field.focus(), 20);
  };
  const closeCmdk = () => (cmdk.hidden = true);
  $('#paletteBtn').addEventListener('click', openCmdk);
  field.addEventListener('input', () => { cmdkSel = 0; drawCmdk(); });
  results.addEventListener('click', (e) => {
    const b = e.target.closest('[data-cmd]');
    if (!b) return;
    closeCmdk();
    commands[Number(b.dataset.cmd)].run();
  });
  cmdk.addEventListener('click', (e) => { if (e.target === cmdk) closeCmdk(); });
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'e') {
      e.preventDefault();
      cmdk.hidden ? openCmdk() : closeCmdk();
    }
    if (e.key === 'Escape') { closeCmdk(); lightbox.hidden = true; }
    if (!cmdk.hidden) {
      if (e.key === 'ArrowDown') { e.preventDefault(); cmdkSel++; drawCmdk(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); cmdkSel = Math.max(0, cmdkSel - 1); drawCmdk(); }
      if (e.key === 'Enter') {
        const q = field.value.trim().toLowerCase();
        const hits = commands.filter((c) => (c.label + c.kind).toLowerCase().includes(q)).slice(0, 9);
        if (hits[cmdkSel]) { closeCmdk(); hits[cmdkSel].run(); }
      }
    }
  });

  /* ------------------------------------------------------- scrollspy etc -- */
  const railLinks = $$('[data-rail]');
  const sectionEls = $$('[data-section]');
  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        railLinks.forEach((l) => l.classList.toggle('is-active', l.dataset.rail === en.target.id));
      });
    },
    { rootMargin: '-25% 0px -65% 0px' }
  );
  sectionEls.forEach((s) => spy.observe(s));

  const reveal = new IntersectionObserver(
    (entries) => entries.forEach((en) => en.isIntersecting && (en.target.classList.add('is-in'), reveal.unobserve(en.target))),
    { threshold: 0.12 }
  );
  $$('.reveal').forEach((el) => reveal.observe(el));
})();
