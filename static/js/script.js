document.addEventListener('DOMContentLoaded', () => {
  if (typeof window === 'undefined') return;

  const navbar = document.querySelector('.navbar');
  const toggle = document.querySelector('.navbar-toggle');
  const navLinks = document.querySelector('.navbar-links');

  window.addEventListener('scroll', () => {
    if (!navbar) return;
    if (window.pageYOffset > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }, { passive: true });

  toggle?.addEventListener('click', () => {
    toggle.classList.toggle('active');
    navLinks?.classList.toggle('active');
    document.body.style.overflow = navLinks?.classList.contains('active') ? 'hidden' : '';
  });

  document.querySelectorAll('.navbar-links a').forEach((link) => {
    link.addEventListener('click', () => {
      toggle?.classList.remove('active');
      navLinks?.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (event) => {
      event.preventDefault();
      const targetId = anchor.getAttribute('href');
      const target = targetId ? document.querySelector(targetId) : null;
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -40px 0px'
  });

  document.querySelectorAll('.reveal').forEach((element) => {
    revealObserver.observe(element);
  });

  const bookingForm = document.querySelector('.booking-form');
  bookingForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const button = bookingForm.querySelector('button[type="submit"]');
    if (!button) return;

    const originalText = button.textContent;
    button.textContent = 'Thank You';
    button.style.background = '#7b5738';

    setTimeout(() => {
      button.textContent = originalText;
      button.style.background = '';
      bookingForm.reset();
    }, 2500);
  });

  const cursorGlow = document.createElement('div');
  cursorGlow.className = 'cursor-glow';
  cursorGlow.style.cssText = `
    position: fixed;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(212, 177, 142, 0.18), transparent 70%);
    pointer-events: none;
    z-index: 9999;
    transform: translate(-50%, -50%);
    transition: opacity 0.3s ease;
    opacity: 0;
  `;
  document.body.appendChild(cursorGlow);

  let glowTimeout;

  document.addEventListener('mousemove', (event) => {
    cursorGlow.style.left = `${event.clientX}px`;
    cursorGlow.style.top = `${event.clientY}px`;
    cursorGlow.style.opacity = '1';
    clearTimeout(glowTimeout);
    glowTimeout = setTimeout(() => {
      cursorGlow.style.opacity = '0';
    }, 1200);
  }, { passive: true });

  document.addEventListener('mouseleave', () => {
    cursorGlow.style.opacity = '0';
  }, { passive: true });
});
