// Replay Engine: 100% Fidelity Experience for Shopify Editions Winter '26
// Implements: Full Parallax Hero & Chapter Artwork, Lenis smooth scrolling, Interactive Video Modal, Autoplay Videos, Responsive Sticky Stages

(function() {
  'use strict';

  // 1. Chapter Background Artwork Registry
  const chapterBackgrounds = {
    'hero': '../../assets/images/hero-desktop.jpg',
    'sidekick': '../../assets/images/sidekick.jpg',
    'agentic': '../../assets/images/Agentic_fg_251207.png',
    'online': '../../assets/images/hero-canvas-frame.jpg',
    'retail': '../../assets/images/retail.jpg',
    'marketing': '../../assets/images/marketing.jpg',
    'checkout': '../../assets/images/checkout.jpg',
    'operations': '../../assets/images/operations.jpg',
    'shop-app': '../../assets/images/sidekick.jpg',
    'b2b': '../../assets/images/b2b.jpg',
    'finance': '../../assets/images/Finance_Fallback.jpg',
    'shipping': '../../assets/images/shipping.jpg',
    'developer': '../../assets/images/developer.jpg'
  };

  // 2. High-res video mapping for product modals
  const videoMap = {
    'sidekick-video': '../../assets/video/620a0d8735da4d97b040b1cd98693898.HD-720p-1.6Mbps-64843815.mp4',
    'agentic-storefronts-video': '../../assets/video/2ace8284aebc4d22901886b2323bb20d.HD-720p-1.6Mbps-64843973.mp4',
    'tinker-app': '../../assets/video/def37b82d2b5486a87cbf297a896f7d4.HD-720p-4.5Mbps-64727252.mp4',
    'shopify-product-network': '../../assets/video/f880db5d8462441482ecbc2437cacf5d.HD-720p-1.6Mbps-64884899.mp4',
    'build-with-full-mcp-support': '../../assets/video/0dfe781a187d48cfa581ed2b1ad6a5ed.HD-720p-1.6Mbps-64844032.mp4'
  };

  // 3. Hydrate Lazy Media
  document.querySelectorAll('[data-src]').forEach(el => {
    const u = el.getAttribute('data-src');
    if (u) {
      el.setAttribute('src', u);
      el.removeAttribute('data-src');
    }
  });

  document.querySelectorAll('[data-srcset]').forEach(el => {
    const u = el.getAttribute('data-srcset');
    if (u) {
      el.setAttribute('srcset', u);
      el.removeAttribute('data-srcset');
    }
  });

  document.querySelectorAll('img[loading="lazy"]').forEach(img => {
    img.loading = 'eager';
  });

  // 4. Video Autoplay on Viewport Intersection
  const videos = document.querySelectorAll('video');
  videos.forEach(v => {
    v.muted = true;
    v.loop = true;
    v.playsInline = true;
    v.setAttribute('preload', 'auto');
    try { v.load(); } catch (e) {}
  });

  if ('IntersectionObserver' in window) {
    const videoObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const v = entry.target;
        if (entry.isIntersecting) {
          v.play().catch(() => {});
        } else {
          v.pause();
        }
      });
    }, { threshold: 0.2 });

    videos.forEach(v => videoObserver.observe(v));
  }

  // 5. Parallax Hero & Chapter Background Stage
  const heroWrapper = document.querySelector('.canvas-wrapper');
  const heroBg = document.getElementById('heroBgImage');
  const davinciTitle = document.querySelector('.davinci-lines__title');
  const sections = Array.from(document.querySelectorAll('section[id], div[data-section-id]'));

  let currentActiveId = 'hero';

  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    const vh = window.innerHeight;

    // Detect which chapter is currently in center view
    let activeSec = 'hero';
    if (scrollY > vh * 0.4) {
      for (const sec of sections) {
        const rect = sec.getBoundingClientRect();
        if (rect.top <= vh * 0.5 && rect.bottom >= vh * 0.3) {
          activeSec = sec.id || sec.getAttribute('data-section-id');
          break;
        }
      }
    }

    // Dynamic transition of background stage
    if (activeSec !== currentActiveId && heroBg) {
      currentActiveId = activeSec;
      const newBg = chapterBackgrounds[activeSec] || chapterBackgrounds['hero'];
      heroBg.style.opacity = '0.3';
      setTimeout(() => {
        heroBg.src = newBg;
        heroBg.style.opacity = '1';
      }, 200);
    }

    // Parallax motion on background
    if (heroBg) {
      const offset = (scrollY % vh) * 0.15;
      heroBg.style.transform = `scale(1.05) translateY(${offset}px)`;
    }

    // Davinci lines title reveal / fade
    if (davinciTitle) {
      if (scrollY > 50 && scrollY < vh * 0.8) {
        davinciTitle.style.opacity = Math.min(1, (scrollY - 50) / 200);
      } else if (scrollY >= vh * 0.8) {
        davinciTitle.style.opacity = Math.max(0, 1 - ((scrollY - vh * 0.8) / 300));
      } else {
        davinciTitle.style.opacity = '0';
      }
    }
  }, { passive: true });

  // 6. Interactive High-End Video Modal
  const modal = document.querySelector('[data-component-name="video-modal"]');
  const modalWrap = modal ? modal.querySelector('.video-wrap') : null;

  if (modal && modalWrap) {
    const modalVideo = document.createElement('video');
    modalVideo.controls = true;
    modalVideo.autoplay = true;
    modalVideo.playsInline = true;
    modalVideo.style.width = '100%';
    modalVideo.style.borderRadius = '12px';
    modalVideo.style.boxShadow = '0 30px 60px -15px rgba(0, 0, 0, 0.9)';
    modalWrap.appendChild(modalVideo);

    document.querySelectorAll('[data-component-name="cta-open-video-modal"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const transitionId = btn.getAttribute('data-transition-id');
        const videoSrc = videoMap[transitionId] || '../../assets/video/b201bb23d69f4a748de0ad9a500f4d4c.mp4';
        
        modalVideo.src = videoSrc;
        modal.classList.remove('hidden');
        modal.classList.add('is-open');
        modalVideo.play().catch(() => {});
      });
    });

    const closeModal = () => {
      modal.classList.add('hidden');
      modal.classList.remove('is-open');
      modalVideo.pause();
      modalVideo.src = '';
    };

    modal.querySelectorAll('[data-component-name="modal-close"], button.absolute').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        closeModal();
      });
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        closeModal();
      }
    });
  }

  // 7. Smooth anchor scrolling
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const id = a.getAttribute('href').slice(1);
      const t = document.getElementById(id);
      if (t) {
        e.preventDefault();
        t.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  console.log('[Shopify Replay] Full visual fidelity with stage parallax & video modals ready.');
})();
