/* ==========================================================================
   OCAC — Main JavaScript
   Features: mobile menu, scroll header, back-to-top, fade-in,
             year filter, image lightbox
   ========================================================================== */
(function() {
  'use strict';

  // ---------- Mobile Menu ----------
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function() {
      var expanded = this.getAttribute('aria-expanded') === 'true';
      this.setAttribute('aria-expanded', !expanded);
      nav.classList.toggle('is-open');
    });
  }

  // ---------- Scroll: header shadow ----------
  var header = document.getElementById('site-header');
  var lastScroll = 0;
  if (header) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 10) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
      lastScroll = window.scrollY;
    }, { passive: true });
  }

  // ---------- Back to Top ----------
  var btn = document.createElement('button');
  btn.className = 'back-to-top';
  btn.innerHTML = '↑';
  btn.setAttribute('aria-label', 'Back to top');
  document.body.appendChild(btn);

  window.addEventListener('scroll', function() {
    btn.classList.toggle('is-visible', window.scrollY > 500);
  }, { passive: true });

  btn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ---------- Fade-in Animation ----------
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.item-card').forEach(function(card, i) {
    card.style.opacity = '0';
    card.style.transform = 'translateY(16px)';
    card.style.transition = 'opacity 0.5s cubic-bezier(0.25,0.1,0.25,1) ' + (i % 4) * 0.06 + 's, transform 0.5s cubic-bezier(0.25,0.1,0.25,1) ' + (i % 4) * 0.06 + 's';
    observer.observe(card);
  });

  // ---------- Year Filter ----------
  var filterBar = document.getElementById('filter-bar');
  var grid = document.getElementById('items-grid');
  var noResults = document.getElementById('no-results');

  if (filterBar && grid) {
    var filterLinks = filterBar.querySelectorAll('a[data-filter]');
    var cards = grid.querySelectorAll('.item-card');

    filterLinks.forEach(function(link) {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        var filter = this.getAttribute('data-filter');

        // Update active state
        filterLinks.forEach(function(l) { l.classList.remove('is-active'); });
        this.classList.add('is-active');

        // Filter cards
        var visibleCount = 0;
        cards.forEach(function(card) {
          var year = card.getAttribute('data-year');
          var show = (filter === 'all') || (year === filter);
          card.style.display = show ? '' : 'none';
          if (show) visibleCount++;
        });

        // Show/hide no results
        if (noResults) {
          noResults.style.display = visibleCount === 0 ? '' : 'none';
        }
      });
    });
  }

  // ---------- Image Lightbox ----------
  function createLightbox() {
    var overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    overlay.innerHTML = '<button class="lightbox-close" aria-label="Close">×</button>' +
      '<button class="lightbox-nav lightbox-prev" aria-label="Previous">‹</button>' +
      '<img src="" alt="">' +
      '<button class="lightbox-nav lightbox-next" aria-label="Next">›</button>';
    document.body.appendChild(overlay);

    var img = overlay.querySelector('img');
    var closeBtn = overlay.querySelector('.lightbox-close');
    var prevBtn = overlay.querySelector('.lightbox-prev');
    var nextBtn = overlay.querySelector('.lightbox-next');
    var images = [];
    var currentIndex = 0;

    function open(src, gallery) {
      images = gallery || [src];
      currentIndex = images.indexOf(src);
      if (currentIndex === -1) currentIndex = 0;
      img.src = images[currentIndex];
      overlay.classList.add('is-active');
      document.body.style.overflow = 'hidden';
      updateNav();
    }

    function close() {
      overlay.classList.remove('is-active');
      document.body.style.overflow = '';
    }

    function navigate(dir) {
      currentIndex = (currentIndex + dir + images.length) % images.length;
      img.src = images[currentIndex];
      updateNav();
    }

    function updateNav() {
      var showNav = images.length > 1;
      prevBtn.style.display = showNav ? '' : 'none';
      nextBtn.style.display = showNav ? '' : 'none';
    }

    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) close();
    });
    prevBtn.addEventListener('click', function(e) { e.stopPropagation(); navigate(-1); });
    nextBtn.addEventListener('click', function(e) { e.stopPropagation(); navigate(1); });

    document.addEventListener('keydown', function(e) {
      if (!overlay.classList.contains('is-active')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') navigate(-1);
      if (e.key === 'ArrowRight') navigate(1);
    });

    return { open: open };
  }

  var lightbox = createLightbox();

  // Attach to gallery images
  document.querySelectorAll('.article-gallery').forEach(function(gallery) {
    var imgs = gallery.querySelectorAll('img');
    var srcs = Array.prototype.map.call(imgs, function(i) { return i.src; });
    imgs.forEach(function(img) {
      img.addEventListener('click', function() {
        lightbox.open(this.src, srcs);
      });
    });
  });

  // Also attach to article body images (not featured image)
  document.querySelectorAll('.article-body img:not(.article-featured-img)').forEach(function(img) {
    if (img.closest('.article-gallery')) return; // skip gallery images, already handled
    img.style.cursor = 'pointer';
    img.addEventListener('click', function() {
      lightbox.open(this.src);
    });
  });

})();
