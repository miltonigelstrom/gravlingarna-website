/* GRÄVLINGARNA — scroll-reveal + före/efter auto-avslöjning */
(function () {
  'use strict';
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Scroll-reveal (synligt by default; göm bara det som är utanför vyn) ---------- */
  const revealEls = Array.from(document.querySelectorAll('.reveal'));
  if (revealEls.length && 'IntersectionObserver' in window && !reduce) {
    const vh = window.innerHeight || document.documentElement.clientHeight;
    const hidden = [];
    revealEls.forEach((el) => {
      if (el.getBoundingClientRect().top > vh * 0.82) { el.classList.add('pre'); hidden.push(el); }
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.remove('pre'); io.unobserve(e.target); }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -6% 0px' });
    hidden.forEach((el) => io.observe(el));
  }

  /* ---------- Före / Efter ---------- */
  function ease(t) { return 1 - Math.pow(1 - t, 3); }

  function setupBA(el) {
    const target = 50;          // slutläge: 50/50-jämförelse
    let raf = null;
    let interactive = false;

    function animateTo(from, to, dur, after) {
      const t0 = performance.now();
      cancelAnimationFrame(raf);
      (function step(now) {
        const p = Math.min(1, (now - t0) / dur);
        el.style.setProperty('--pos', (from + (to - from) * ease(p)).toFixed(2));
        if (p < 1) raf = requestAnimationFrame(step);
        else if (after) after();
      })(t0);
    }

    function play() {
      if (reduce) { el.style.setProperty('--pos', target); enableDrag(); return; }
      el.style.setProperty('--pos', 100);
      // liten paus, svep sedan ut för att avslöja EFTER, vila i 50/50
      setTimeout(() => animateTo(100, 18, 1500, () => {
        animateTo(18, target, 700, enableDrag);
      }), 280);
    }

    function enableDrag() {
      if (interactive) return;
      interactive = true;
      el.setAttribute('data-ready', '');
      const rect = () => el.getBoundingClientRect();
      let dragging = false;
      const move = (clientX) => {
        const r = rect();
        const pos = Math.max(0, Math.min(100, ((clientX - r.left) / r.width) * 100));
        cancelAnimationFrame(raf);
        el.style.setProperty('--pos', pos.toFixed(2));
      };
      el.addEventListener('pointerdown', (e) => { dragging = true; el.setPointerCapture(e.pointerId); move(e.clientX); });
      el.addEventListener('pointermove', (e) => { if (dragging) move(e.clientX); });
      window.addEventListener('pointerup', () => { dragging = false; });
      el.addEventListener('pointerleave', () => { if (!dragging) {} });
    }

    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { play(); io.unobserve(el); }
      });
    }, { threshold: 0.4 });
    io.observe(el);
  }

  document.querySelectorAll('[data-ba]').forEach(setupBA);

  /* ---------- Sticky header skugga ---------- */
  const header = document.querySelector('[data-header]');
  if (header) {
    const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- Mobilmeny ---------- */
  const burger = document.querySelector('[data-burger]');
  const nav = document.querySelector('[data-nav]');
  if (burger && nav) {
    burger.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      burger.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => {
      nav.classList.remove('open'); burger.classList.remove('open');
    }));
  }

  /* ---------- Enkel formulär-feedback (mock) ---------- */
  const form = document.querySelector('[data-contact-form]');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const note = form.querySelector('[data-form-note]');
      if (note) { note.hidden = false; }
      form.querySelectorAll('input, textarea, button').forEach((f) => { f.disabled = true; });
    });
  }
})();
