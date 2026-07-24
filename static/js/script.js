document.addEventListener('DOMContentLoaded', () => {
  if (typeof window === 'undefined') return;

  console.log('boho-bloom: script.js loaded v3');

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
    const isActive = toggle.classList.toggle('active');
    navLinks?.classList.toggle('active', isActive);
    toggle.setAttribute('aria-expanded', String(isActive));
    document.body.style.overflow = isActive ? 'hidden' : '';
  });

  const closeAllOverlays = () => {
    toggle?.classList.remove('active');
    navLinks?.classList.remove('active');
    toggle?.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    document.querySelectorAll('.overlay.active, .modal.active, [data-open="true"]').forEach((el) => {
      el.classList.remove('active');
      el.removeAttribute('data-open');
    });
  };

  document.querySelectorAll('.navbar-links a, .navbar-brand').forEach((link) => {
    link.addEventListener('click', () => {
      closeAllOverlays();
    });
  });

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (event) => {
      const targetId = anchor.getAttribute('href');
      if (targetId && targetId.length > 1) {
        const target = document.querySelector(targetId);
        if (target) {
          event.preventDefault();
          closeAllOverlays();
          history.pushState(null, '', targetId);
          const navbarHeight = navbar ? navbar.offsetHeight : 0;
          const top = target.getBoundingClientRect().top + window.pageYOffset - navbarHeight - 12;
          window.scrollTo({ top, behavior: 'smooth' });
        }
      }
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
  bookingForm?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = bookingForm.querySelector('button[type="submit"]');
    if (!button) return;
    if (button.disabled) return;

    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = 'Sending...';
    button.style.opacity = '0.7';

    const formData = new FormData(bookingForm);
    const payload = {
      name: formData.get('name') || bookingForm.querySelector('input[type="text"]')?.value || '',
      phone: formData.get('phone') || bookingForm.querySelector('input[type="tel"]')?.value || '',
      service: bookingForm.querySelector('select')?.value || '',
      message: bookingForm.querySelector('textarea')?.value || '',
    };

    try {
      const res = await fetch('/api/booking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.ok) {
        button.textContent = 'Sent!';
        button.style.background = '#7b5738';
        setTimeout(() => {
          button.textContent = originalText;
          button.style.background = '';
          button.disabled = false;
          button.style.opacity = '1';
          bookingForm.reset();
        }, 3000);
      } else {
        throw new Error(data.detail || 'Failed to send');
      }
    } catch (err) {
      button.textContent = 'Try Again';
      button.style.background = '#b48860';
      setTimeout(() => {
        button.textContent = originalText;
        button.style.background = '';
        button.disabled = false;
        button.style.opacity = '1';
      }, 2000);
    }
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

  const pageGlow = document.querySelector('.page-glow');
  if (pageGlow) {
    pageGlow.style.animation = 'floatGlow 8s ease-in-out infinite';
  }
});

function initProfileEdit() {
  const editBtn = document.getElementById('profile-edit-btn');
  const cancelBtn = document.getElementById('profile-cancel-btn');
  const saveBtn = document.getElementById('profile-save-btn');
  const actions = document.getElementById('profile-actions');
  const message = document.getElementById('profile-message');
  const fields = document.querySelectorAll('.profile-field[data-field]');

  if (!editBtn || !cancelBtn || !saveBtn) return;

  let originals = {};

  function storeOriginals() {
    originals = {};
    fields.forEach(function(f) {
      var input = f.querySelector('.profile-field-edit');
      if (input) originals[f.dataset.field] = input.value;
    });
  }

  function enterEditMode() {
    storeOriginals();
    fields.forEach(function(f) { f.classList.add('editing'); });
    actions.classList.add('visible');
    editBtn.style.display = 'none';
    message.textContent = '';
    message.className = 'profile-message';
  }

  function exitEditMode() {
    fields.forEach(function(f) { f.classList.remove('editing'); });
    actions.classList.remove('visible');
    editBtn.style.display = '';
  }

  function cancelEdit() {
    fields.forEach(function(f) {
      var input = f.querySelector('.profile-field-edit');
      if (input && originals[f.dataset.field] !== undefined) {
        input.value = originals[f.dataset.field];
        var display = f.querySelector('.profile-field-value');
        if (display) display.textContent = input.value || '\u2014';
      }
    });
    exitEditMode();
  }

  function showSuccess(msg) {
    message.textContent = msg;
    message.className = 'profile-message profile-message-success';
  }

  function showError(msg) {
    message.textContent = msg;
    message.className = 'profile-message profile-message-error';
  }

  function updateAvatar(name) {
    var avatar = document.getElementById('profile-avatar');
    if (!avatar) return;
    var trimmed = (name || '').trim();
    var initials = 'U';
    if (trimmed) {
      var parts = trimmed.split(/\s+/);
      if (parts.length >= 2) {
        initials = (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      } else {
        initials = parts[0][0].toUpperCase();
      }
    }
    avatar.textContent = initials;
  }

  editBtn.addEventListener('click', enterEditMode);

  cancelBtn.addEventListener('click', cancelEdit);

  saveBtn.addEventListener('click', async function() {
    var nameInput = document.getElementById('input-name');
    var dobInput = document.getElementById('input-dob');
    if (!nameInput) return;

    var name = nameInput.value.trim();
    if (!name) {
      showError('Name cannot be empty');
      return;
    }

    var payload = { name: name };
    if (dobInput && dobInput.value) {
      payload.date_of_birth = dobInput.value;
    }

    try {
      var res = await fetch('/profile/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        var errData;
        try { errData = await res.json(); } catch (_) {}
        showError((errData && errData.detail) || 'Unable to update profile. Please try again.');
        return;
      }

      var data = await res.json();

      var nameDisplay = document.getElementById('field-name');
      if (nameDisplay) nameDisplay.textContent = data.name;
      updateAvatar(data.name);

      if (data.date_of_birth) {
        var dobDisplay = document.getElementById('field-dob');
        if (dobDisplay) dobDisplay.textContent = data.date_of_birth;
        var ageDisplay = document.getElementById('field-age');
        if (ageDisplay && data.age !== null && data.age !== undefined) {
          ageDisplay.textContent = data.age + ' years';
        }
      }

      exitEditMode();
      showSuccess('Profile updated successfully');
      setTimeout(function() {
        message.textContent = '';
        message.className = 'profile-message';
      }, 3000);
    } catch (err) {
      showError('Unable to update profile. Please try again.');
    }
  });

  storeOriginals();
}
