/**
 * Sovereign AI Workbench — Smart India Hackathon Presentation Controller
 * Controls 1920x1080 canvas scaling, keyboard/touch navigation, and export modes.
 */

(function () {
  'use strict';

  const TOTAL_SLIDES = 6;
  let currentSlide = 1;

  // DOM Elements
  const stage = document.getElementById('slide-stage');
  const slides = document.querySelectorAll('.slide');
  const dots = document.querySelectorAll('.dot');
  const progressBar = document.getElementById('progress-bar');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const fullscreenBtn = document.getElementById('fullscreen-btn');
  const printBtn = document.getElementById('print-btn');

  /**
   * Auto-scale the 1920x1080 stage to fit the browser viewport perfectly
   * without scrolling, distortion, or clipping.
   */
  function autoScaleStage() {
    if (document.body.classList.contains('export-mode')) {
      stage.style.transform = 'none';
      return;
    }

    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const targetW = 1920;
    const targetH = 1080;

    // Determine scale factor while preserving 16:9 ratio
    const scale = Math.min(vw / targetW, vh / targetH);
    stage.style.transform = `scale(${scale})`;
  }

  /**
   * Navigate to a specific slide (1 to TOTAL_SLIDES)
   */
  function goToSlide(slideNum) {
    if (slideNum < 1) slideNum = 1;
    if (slideNum > TOTAL_SLIDES) slideNum = TOTAL_SLIDES;

    currentSlide = slideNum;

    // Update active slide class
    slides.forEach((slide) => {
      const num = parseInt(slide.dataset.slide, 10);
      slide.classList.toggle('active', num === currentSlide);
    });

    // Update dots
    dots.forEach((dot) => {
      const target = parseInt(dot.dataset.target, 10);
      dot.classList.toggle('active', target === currentSlide);
    });

    // Update top progress bar
    if (progressBar) {
      const pct = (currentSlide / TOTAL_SLIDES) * 100;
      progressBar.style.width = `${pct}%`;
    }

    // Update URL hash without scroll
    history.replaceState(null, '', `#slide-${currentSlide}`);
  }

  function nextSlide() {
    if (currentSlide < TOTAL_SLIDES) {
      goToSlide(currentSlide + 1);
    }
  }

  function prevSlide() {
    if (currentSlide > 1) {
      goToSlide(currentSlide - 1);
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }
  }

  function triggerPrint() {
    window.print();
  }

  // Keyboard Navigation
  window.addEventListener('keydown', (e) => {
    // Disable shortcuts if inside an input or textarea
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

    switch (e.key) {
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
        e.preventDefault();
        nextSlide();
        break;

      case 'ArrowLeft':
      case 'PageUp':
      case 'Backspace':
        e.preventDefault();
        prevSlide();
        break;

      case 'Home':
        e.preventDefault();
        goToSlide(1);
        break;

      case 'End':
        e.preventDefault();
        goToSlide(TOTAL_SLIDES);
        break;

      case 'f':
      case 'F':
        e.preventDefault();
        toggleFullscreen();
        break;

      case 'p':
      case 'P':
        e.preventDefault();
        triggerPrint();
        break;

      default:
        // Number keys 1-6
        if (e.key >= '1' && e.key <= '6') {
          e.preventDefault();
          goToSlide(parseInt(e.key, 10));
        }
        break;
    }
  });

  // UI Event Listeners
  if (prevBtn) prevBtn.addEventListener('click', prevSlide);
  if (nextBtn) nextBtn.addEventListener('click', nextSlide);
  if (fullscreenBtn) fullscreenBtn.addEventListener('click', toggleFullscreen);
  if (printBtn) printBtn.addEventListener('click', triggerPrint);

  dots.forEach((dot) => {
    dot.addEventListener('click', () => {
      const target = parseInt(dot.dataset.target, 10);
      if (target) goToSlide(target);
    });
  });

  // Window Resize Listener
  window.addEventListener('resize', autoScaleStage);

  // Parse Initial URL Hash or Query Params
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('export') === 'true') {
    document.body.classList.add('export-mode');
  }

  const hash = window.location.hash;
  if (hash && hash.startsWith('#slide-')) {
    const s = parseInt(hash.replace('#slide-', ''), 10);
    if (!isNaN(s) && s >= 1 && s <= TOTAL_SLIDES) {
      currentSlide = s;
    }
  }

  // Initialize
  autoScaleStage();
  goToSlide(currentSlide);
})();
