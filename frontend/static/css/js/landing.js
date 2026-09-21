/* ============================================================
   LEARNING-365 — LANDING PAGE JAVASCRIPT
   Handles: scroll reveals, navbar, mobile menu, counter
   animation, heatmap generation, cursor glow, modals
   ============================================================ */

(function () {
    'use strict';

    // Respect reduced-motion preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ----------------------------------------------------------
       1. SCROLL REVEAL (IntersectionObserver)
       ---------------------------------------------------------- */
    function initScrollReveal() {
        const revealElements = document.querySelectorAll('.reveal');
        if (!revealElements.length) return;

        if (prefersReducedMotion) {
            revealElements.forEach(el => el.classList.add('visible'));
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -60px 0px'
        });

        revealElements.forEach(el => observer.observe(el));
    }

    /* ----------------------------------------------------------
       2. NAVBAR STICKY / SHRINK
       ---------------------------------------------------------- */
    function initNavbar() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        let lastScroll = 0;

        window.addEventListener('scroll', () => {
            const currentScroll = window.scrollY;

            if (currentScroll > 60) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        }, { passive: true });
    }

    /* ----------------------------------------------------------
       3. MOBILE HAMBURGER TOGGLE
       ---------------------------------------------------------- */
    function initMobileMenu() {
        const hamburger = document.getElementById('hamburgerBtn');
        const mobileNav = document.getElementById('mobileNav');
        const overlay = document.getElementById('mobileOverlay');

        if (!hamburger || !mobileNav) return;

        function toggleMenu() {
            const isOpen = mobileNav.classList.contains('open');

            if (isOpen) {
                mobileNav.classList.remove('open');
                hamburger.classList.remove('active');
                if (overlay) {
                    overlay.classList.remove('show');
                    setTimeout(() => { overlay.style.display = 'none'; }, 300);
                }
                document.body.style.overflow = '';
            } else {
                mobileNav.classList.add('open');
                hamburger.classList.add('active');
                if (overlay) {
                    overlay.style.display = 'block';
                    requestAnimationFrame(() => overlay.classList.add('show'));
                }
                document.body.style.overflow = 'hidden';
            }
        }

        hamburger.addEventListener('click', toggleMenu);
        if (overlay) overlay.addEventListener('click', toggleMenu);

        // Close on link click
        mobileNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (mobileNav.classList.contains('open')) {
                    toggleMenu();
                }
            });
        });
    }

    /* ----------------------------------------------------------
       4. COUNTER ANIMATION
       ---------------------------------------------------------- */
    function initCounterAnimation() {
        const counters = document.querySelectorAll('.counter');
        if (!counters.length) return;

        let triggered = false;
        const statsSection = document.querySelector('.hero-social-proof') || document.querySelector('[data-counter-trigger]');

        function animateCounters() {
            counters.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-target'), 10);
                if (isNaN(target)) return;

                const duration = 2000;
                const steps = 60;
                const increment = target / steps;
                let current = 0;
                let step = 0;

                function updateCount() {
                    step++;
                    current = Math.min(Math.ceil(increment * step), target);
                    counter.textContent = current.toLocaleString();

                    if (step < steps) {
                        requestAnimationFrame(updateCount);
                    } else {
                        counter.textContent = target.toLocaleString();
                    }
                }

                if (prefersReducedMotion) {
                    counter.textContent = target.toLocaleString();
                } else {
                    updateCount();
                }
            });
        }

        if (statsSection) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !triggered) {
                        triggered = true;
                        animateCounters();
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.3 });

            observer.observe(statsSection);
        } else {
            // Fallback: animate on scroll
            window.addEventListener('scroll', () => {
                if (!triggered) {
                    triggered = true;
                    animateCounters();
                }
            }, { once: true });
        }
    }

    /* ----------------------------------------------------------
       5. HEATMAP GENERATION
       ---------------------------------------------------------- */
    function initHeatmap() {
        const grid = document.getElementById('heatmapGrid');
        if (!grid) return;

        const totalWeeks = 52;
        const totalDays = totalWeeks * 7;

        // Generate pseudo-random intensity pattern
        // Using a seeded approach so it looks consistent on each load
        function seededRandom(seed) {
            let x = Math.sin(seed) * 10000;
            return x - Math.floor(x);
        }

        for (let i = 0; i < totalDays; i++) {
            const cell = document.createElement('div');
            cell.classList.add('hm-cell');

            const rand = seededRandom(i * 7 + 42);

            if (rand > 0.75) {
                cell.classList.add('l4');
            } else if (rand > 0.55) {
                cell.classList.add('l3');
            } else if (rand > 0.35) {
                cell.classList.add('l2');
            } else if (rand > 0.2) {
                cell.classList.add('l1');
            }
            // else: empty (default)

            grid.appendChild(cell);
        }
    }

    /* ----------------------------------------------------------
       6. CURSOR GLOW
       ---------------------------------------------------------- */
    function initCursorGlow() {
        const glow = document.getElementById('cursor-glow');
        if (!glow || prefersReducedMotion) return;

        // Use matchMedia for touch devices
        if ('ontouchstart' in window) {
            glow.style.display = 'none';
            return;
        }

        document.addEventListener('mousemove', (e) => {
            glow.style.left = e.clientX + 'px';
            glow.style.top = e.clientY + 'px';
        }, { passive: true });
    }

    /* ----------------------------------------------------------
       7. TERMS MODAL
       ---------------------------------------------------------- */
    function initTermsModal() {
        const modal = document.getElementById('termsModal');
        const openBtn = document.getElementById('openTermsModal');
        const closeBtn = document.getElementById('closeTermsBtn');
        const acceptBtn = document.getElementById('acceptTermsBtn');

        if (!modal) return;

        function openModal(e) {
            if (e) e.preventDefault();
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }

        function closeModal() {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }

        if (openBtn) openBtn.addEventListener('click', openModal);
        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (acceptBtn) acceptBtn.addEventListener('click', closeModal);

        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                closeModal();
            }
        });
    }

    /* ----------------------------------------------------------
       8. CONTACT SECTION REVEAL
       ---------------------------------------------------------- */
    function initContactReveal() {
        document.querySelectorAll('.open-contact-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const helpSection = document.getElementById('help-center');
                if (!helpSection) return;

                helpSection.style.display = 'block';
                setTimeout(() => {
                    helpSection.classList.add('visible');
                    helpSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 50);
            });
        });
    }

    /* ----------------------------------------------------------
       9. SMOOTH SCROLL FOR ANCHOR LINKS
       ---------------------------------------------------------- */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(link => {
            link.addEventListener('click', (e) => {
                const targetId = link.getAttribute('href');
                if (targetId === '#') return;

                const targetEl = document.querySelector(targetId);
                if (targetEl) {
                    e.preventDefault();
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    /* ----------------------------------------------------------
       INIT ALL
       ---------------------------------------------------------- */
    document.addEventListener('DOMContentLoaded', () => {
        initScrollReveal();
        initNavbar();
        initMobileMenu();
        initCounterAnimation();
        initHeatmap();
        initCursorGlow();
        initTermsModal();
        initContactReveal();
        initSmoothScroll();
    });

})();
