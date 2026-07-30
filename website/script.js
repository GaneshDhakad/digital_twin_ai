/**
 * TWIN.OS — DIGITAL TWIN AI DESIGN SYSTEM INTERACTION ENGINE
 * Powers scroll animations, interactive tabs, animated number counters, and accordion FAQ.
 */

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initFAQ();
    initCounters();
    initScrollAnimations();
    initMobileMenu();
});

/**
 * 1. Product Showcase Interactive Tabs
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.showcase-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');

            // Deactivate all buttons & contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Activate current
            btn.classList.add('active');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.classList.add('active');
            }
        });
    });
}

/**
 * 2. FAQ Expandable Accordion
 */
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(item => {
        const questionBtn = item.querySelector('.faq-question');
        if (questionBtn) {
            questionBtn.addEventListener('click', () => {
                const isActive = item.classList.contains('active');

                // Optional: Close all other FAQ items for a clean single-open accordion
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('active');
                    }
                });

                // Toggle current item
                if (isActive) {
                    item.classList.remove('active');
                } else {
                    item.classList.add('active');
                }
            });
        }
    });
}

/**
 * 3. Animated Statistics Counters (Scroll-triggered)
 */
function initCounters() {
    const counters = document.querySelectorAll('.stat-number');
    let hasAnimated = false;

    if ('IntersectionObserver' in window) {
        const statsSection = document.getElementById('statistics');
        if (!statsSection) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !hasAnimated) {
                    hasAnimated = true;
                    counters.forEach(counter => animateCounter(counter));
                }
            });
        }, { threshold: 0.3 });

        observer.observe(statsSection);
    } else {
        // Fallback for older browsers
        counters.forEach(counter => animateCounter(counter));
    }
}

function animateCounter(counter) {
    const target = parseFloat(counter.getAttribute('data-target'));
    const suffix = counter.getAttribute('data-suffix') || '';
    const duration = 1800; // ms
    const startTime = performance.now();
    const isFloat = target % 1 !== 0;

    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing out quint
        const easeOut = 1 - Math.pow(1 - progress, 4);
        const currentVal = (target * easeOut);

        if (isFloat) {
            counter.textContent = currentVal.toFixed(1) + suffix;
        } else {
            counter.textContent = Math.round(currentVal) + suffix;
        }

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else {
            // Final exact value
            counter.textContent = target + suffix;
        }
    }

    requestAnimationFrame(updateCounter);
}

/**
 * 4. Scroll-Triggered Entrance Animations
 */
function initScrollAnimations() {
    const cards = document.querySelectorAll('.glass-card, .pricing-card, .stat-card, .feature-card');

    if ('IntersectionObserver' in window) {
        const cardObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    cardObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(24px)';
            card.style.transition = 'opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
            cardObserver.observe(card);
        });
    }
}

/**
 * 5. Mobile Navigation Menu Toggle
 */
function initMobileMenu() {
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (mobileBtn && navLinks) {
        mobileBtn.addEventListener('click', () => {
            const isDisplayed = navLinks.style.display === 'flex';
            if (isDisplayed) {
                navLinks.style.display = 'none';
            } else {
                navLinks.style.display = 'flex';
                navLinks.style.flexDirection = 'column';
                navLinks.style.position = 'absolute';
                navLinks.style.top = '76px';
                navLinks.style.left = '0';
                navLinks.style.right = '0';
                navLinks.style.background = 'rgba(255, 255, 255, 0.96)';
                navLinks.style.padding = '24px';
                navLinks.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)';
                navLinks.style.borderBottom = '1px solid #E5E7EB';
            }
        });
    }
}
