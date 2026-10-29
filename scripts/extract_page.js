(() => {
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const strip = (u) => (u || '').split('?')[0];
  const textOf = (el) => clean(el.textContent);

  const sections = [...document.querySelectorAll('main section[id]')].map((sec) => {
    const articles = [...sec.querySelectorAll('article')];
    const features = articles
      .map((a) => {
        const heading = a.querySelector('h3,h4,h5');
        const paras = [...a.querySelectorAll('p')].map(textOf).filter((p) => p.length > 8);
        const cta = [...a.querySelectorAll('a[href]')]
          .map((l) => ({ label: clean(l.innerText) || clean(l.getAttribute('aria-label')), href: strip(l.href) }))
          .filter((l) => !l.href.includes('cdn.shopify.com'));
        return {
          title: heading ? textOf(heading) : '',
          description: paras[0] || '',
          extra: paras.slice(1, 4),
          cta: cta.slice(0, 3),
          images: [...new Set([...a.querySelectorAll('img')].map((i) => strip(i.currentSrc || i.src)))].slice(0, 4),
        };
      })
      .filter((f) => f.title);

    const groupLabels = [...sec.querySelectorAll('h3,h4')]
      .filter((h) => !h.closest('article'))
      .map(textOf)
      .filter((t) => t.length > 2);

    return {
      id: sec.id,
      kicker: clean(sec.querySelector('h2 span')?.textContent),
      title: clean(sec.querySelector('h2')?.textContent),
      lead: clean(sec.querySelector('.rich-text')?.textContent),
      text: clean(sec.textContent).slice(0, 12000),
      groupLabels: [...new Set(groupLabels)],
      features,
      linkCount: sec.querySelectorAll('a[href]').length,
      links: [...sec.querySelectorAll('a[href]')]
        .map((a) => ({ label: clean(a.innerText) || clean(a.getAttribute('aria-label')), href: strip(a.href) }))
        .filter((l) => l.href && !l.href.includes('cdn.shopify.com'))
        .slice(0, 60),
      images: [...new Set([...sec.querySelectorAll('img')].map((i) => strip(i.currentSrc || i.src)))].slice(0, 40),
      altText: [...new Set([...sec.querySelectorAll('img[alt]')].map((i) => clean(i.alt)).filter(Boolean))],
      canvases: sec.querySelectorAll('canvas').length,
      heightPx: Math.round(sec.getBoundingClientRect().height),
    };
  });

  return {
    capturedAt: new Date().toISOString(),
    url: location.href,
    title: document.title,
    meta: {
      description: document.querySelector('meta[name="description"]')?.content,
      ogImage: document.querySelector('meta[property="og:image"]')?.content,
      themeColor: document.querySelector('meta[name="theme-color"]')?.content,
    },
    hero: { h1: [...document.querySelectorAll('h1')].map(textOf) },
    nav: [...new Set([...document.querySelectorAll('nav a')].map((a) => clean(a.innerText)).filter(Boolean))],
    footer: clean(document.querySelector('footer')?.textContent).slice(0, 1500),
    sections,
    totals: {
      sections: sections.length,
      features: sections.reduce((n, s) => n + s.features.length, 0),
      links: sections.reduce((n, s) => n + s.linkCount, 0),
      pageHeight: document.body.scrollHeight,
    },
  };
})()
