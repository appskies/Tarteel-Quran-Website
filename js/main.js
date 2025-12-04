/**
 * Tarteel Quran - Main JavaScript
 * Handles animations, scroll effects, and interactivity
 */

// Debug log
console.log('Tarteel Quran JS loaded');

// App Store URL
const APP_STORE_URL = 'https://apps.apple.com/us/app/ai-quran-reader-athkar-dua/id6749589788';

/**
 * TikTok In-App Browser Detection & Workaround
 * TikTok blocks App Store links in their WebView, so we detect it and show instructions
 */
function initTikTokWorkaround() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;

    // Check for TikTok's in-app browser
    const isTikTokBrowser = /musical_ly|BytedanceWebview|TikTok/i.test(userAgent);

    // Check if URL has tiktok param (user opened in Safari from TikTok)
    const urlParams = new URLSearchParams(window.location.search);
    const fromTikTok = urlParams.get('from') === 'tiktok';

    if (isTikTokBrowser) {
        console.log('TikTok in-app browser detected');

        // Add param to URL so Safari knows to redirect
        if (!fromTikTok) {
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set('from', 'tiktok');
            window.history.replaceState({}, '', newUrl);
        }

        showTikTokToast();
    } else if (fromTikTok) {
        // User opened in Safari from TikTok - redirect to App Store
        console.log('Opened from TikTok in real browser - redirecting to App Store');
        window.location.href = APP_STORE_URL;
    }
}

/**
 * Show toast message for TikTok users
 */
function showTikTokToast() {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('tiktok-toast');

    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'tiktok-toast';
        toastContainer.className = 'tiktok-toast';
        toastContainer.innerHTML = `
            <div class="tiktok-toast-bubble">
                <div class="tiktok-toast-tail"></div>
                <p>On <svg class="tiktok-icon" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M34.1451 0H26.0556V32.6956C26.0556 38.4348 21.3582 43.1304 15.6167 43.1304C9.87529 43.1304 5.17786 38.4348 5.17786 32.6956C5.17786 27.0435 9.78857 22.4348 15.3565 22.2609V14.0869C5.26458 14.2609 -2.82593 22.4348 -2.82593 32.6956C-2.82593 43.0435 5.43803 51 15.7034 51C25.9688 51 34.2318 42.8696 34.2318 32.6956V15.6522C37.5765 18.087 41.7536 19.4783 46.1041 19.5652V11.3913C39.4954 11.1304 34.1451 6.17391 34.1451 0Z" fill="black"/></svg> you need to tap on the <span class="dots-icon">•••</span> and then tap on <span class="highlight">"Open in browser"</span> to download the app for free.</p>
            </div>
        `;
        document.body.appendChild(toastContainer);

        // Animate in after a brief delay
        setTimeout(() => {
            toastContainer.classList.add('show');
        }, 500);
    }
}

/**
 * Close TikTok toast
 */
function closeTikTokToast() {
    const toast = document.getElementById('tiktok-toast');
    if (toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
}

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing...');

    // Initialize TikTok workaround first
    initTikTokWorkaround();

    // Initialize all features
    initNavbar();
    initScrollReveal();
    initSmoothScroll();
    initParallaxEffect();
    initCardHoverEffect();
    initTestimonialSlider();
    initHeroSlider();
});

/**
 * Navigation Bar functionality
 * Handles scroll effects and mobile menu toggle
 */
function initNavbar() {
    console.log('Initializing navbar...');

    const navbar = document.querySelector('.navbar');
    const navbarToggle = document.getElementById('navbarToggle');
    const navbarMenu = document.getElementById('navbarMenu');
    const navbarLinks = document.querySelectorAll('.navbar-link');

    // Scroll effect for navbar
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // Mobile menu toggle
    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function() {
            navbarToggle.classList.toggle('active');
            navbarMenu.classList.toggle('active');
            document.body.style.overflow = navbarMenu.classList.contains('active') ? 'hidden' : '';
        });

        // Close menu when clicking a link
        navbarLinks.forEach(link => {
            link.addEventListener('click', function() {
                navbarToggle.classList.remove('active');
                navbarMenu.classList.remove('active');
                document.body.style.overflow = '';
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbar.contains(e.target) && navbarMenu.classList.contains('active')) {
                navbarToggle.classList.remove('active');
                navbarMenu.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    console.log('Navbar initialized');
}

/**
 * Scroll Reveal Animation
 * Reveals elements as they come into viewport
 */
function initScrollReveal() {
    console.log('Initializing scroll reveal...');

    // Elements to reveal on scroll
    const revealElements = document.querySelectorAll(
        '.feature-card, .benefit-card, .testimonial-card, .showcase-item, .rating-card'
    );

    // Add reveal class to elements
    revealElements.forEach(el => {
        el.classList.add('reveal');
    });

    // Intersection Observer options
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    // Create observer
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    // Observe all reveal elements
    revealElements.forEach(el => {
        observer.observe(el);
    });

    console.log(`Observing ${revealElements.length} elements for reveal`);
}

/**
 * Smooth Scroll for anchor links
 */
function initSmoothScroll() {
    console.log('Initializing smooth scroll...');

    const links = document.querySelectorAll('a[href^="#"]');
    const navbar = document.querySelector('.navbar');
    const navbarHeight = navbar ? navbar.offsetHeight : 70;

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            // Scroll to top if just "#"
            if (href === '#') {
                e.preventDefault();
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
                return;
            }

            const target = document.querySelector(href);

            if (target) {
                e.preventDefault();
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navbarHeight;
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    console.log(`Added smooth scroll to ${links.length} links`);
}

/**
 * Parallax effect for hero section
 */
function initParallaxEffect() {
    console.log('Initializing parallax effect...');

    const hero = document.querySelector('.hero');
    const heroImage = document.querySelector('.hero-image');

    if (!hero || !heroImage) {
        console.log('Hero elements not found, skipping parallax');
        return;
    }

    let ticking = false;

    window.addEventListener('scroll', function() {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                const scrolled = window.pageYOffset;
                const heroHeight = hero.offsetHeight;

                // Only apply parallax within hero section
                if (scrolled < heroHeight) {
                    const parallaxValue = scrolled * 0.3;
                    heroImage.style.transform = `translateY(${parallaxValue}px)`;
                }

                ticking = false;
            });

            ticking = true;
        }
    });

    console.log('Parallax effect initialized');
}

/**
 * Enhanced hover effects for cards
 */
function initCardHoverEffect() {
    console.log('Initializing card hover effects...');

    const cards = document.querySelectorAll('.feature-card, .benefit-card');

    cards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-10px)`;
        });

        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
        });
    });

    console.log(`Added hover effects to ${cards.length} cards`);
}

/**
 * Testimonial Slider - Unique Modern Design
 * Features: 3D perspective, smooth transitions, progress dots
 */
function initTestimonialSlider() {
    console.log('Initializing testimonial slider...');

    const slider = document.querySelector('.testimonials-slider');
    if (!slider) {
        console.log('Slider not found, skipping initialization');
        return;
    }

    const track = slider.querySelector('.slider-track');
    const cards = slider.querySelectorAll('.testimonial-card');
    const dots = slider.querySelectorAll('.slider-dot');
    const prevBtn = slider.querySelector('.slider-prev');
    const nextBtn = slider.querySelector('.slider-next');

    let currentIndex = 0;
    let autoPlayInterval;
    const autoPlayDelay = 6000; // 6 seconds for better readability
    let startX = 0;
    let isDragging = false;
    let isAnimating = false;

    // Initialize first card as active
    updateSlider();

    // Auto-play functionality
    function startAutoPlay() {
        stopAutoPlay();
        autoPlayInterval = setInterval(() => {
            goToSlide(currentIndex + 1);
        }, autoPlayDelay);
    }

    function stopAutoPlay() {
        if (autoPlayInterval) {
            clearInterval(autoPlayInterval);
        }
    }

    // Go to specific slide with animation lock
    function goToSlide(index) {
        if (isAnimating) return;
        isAnimating = true;

        // Loop around
        if (index >= cards.length) {
            currentIndex = 0;
        } else if (index < 0) {
            currentIndex = cards.length - 1;
        } else {
            currentIndex = index;
        }

        updateSlider();

        // Release animation lock after transition
        setTimeout(() => {
            isAnimating = false;
        }, 600);
    }

    // Update slider position and active states
    function updateSlider() {
        // Move track with smooth transition
        track.style.transform = `translateX(-${currentIndex * 100}%)`;

        // Update cards with staggered animation feel
        cards.forEach((card, index) => {
            card.classList.remove('active');
            if (index === currentIndex) {
                // Small delay for active card to create nice effect
                setTimeout(() => {
                    card.classList.add('active');
                }, 100);
            }
        });

        // Update dots with progress animation
        dots.forEach((dot, index) => {
            dot.classList.remove('active');
            if (index === currentIndex) {
                dot.classList.add('active');
            }
        });
    }

    // Event Listeners for arrows
    prevBtn.addEventListener('click', () => {
        goToSlide(currentIndex - 1);
        stopAutoPlay();
        startAutoPlay();
    });

    nextBtn.addEventListener('click', () => {
        goToSlide(currentIndex + 1);
        stopAutoPlay();
        startAutoPlay();
    });

    // Dot navigation
    dots.forEach((dot, index) => {
        dot.addEventListener('click', () => {
            goToSlide(index);
            stopAutoPlay();
            startAutoPlay();
        });
    });

    // Touch/Swipe support with improved feel
    let touchStartTime;

    slider.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        touchStartTime = Date.now();
        isDragging = true;
        stopAutoPlay();
    }, { passive: true });

    slider.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        // Could add visual feedback here if desired
    }, { passive: true });

    slider.addEventListener('touchend', (e) => {
        if (!isDragging) return;

        const endX = e.changedTouches[0].clientX;
        const diff = startX - endX;
        const touchDuration = Date.now() - touchStartTime;

        // Quick swipe (< 300ms) or long swipe (> 50px)
        if (Math.abs(diff) > 50 || (Math.abs(diff) > 20 && touchDuration < 300)) {
            if (diff > 0) {
                goToSlide(currentIndex + 1);
            } else {
                goToSlide(currentIndex - 1);
            }
        }

        isDragging = false;
        startAutoPlay();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        const sliderRect = slider.getBoundingClientRect();
        const isInView = sliderRect.top < window.innerHeight && sliderRect.bottom > 0;

        if (isInView) {
            if (e.key === 'ArrowLeft') {
                goToSlide(currentIndex - 1);
                stopAutoPlay();
                startAutoPlay();
            } else if (e.key === 'ArrowRight') {
                goToSlide(currentIndex + 1);
                stopAutoPlay();
                startAutoPlay();
            }
        }
    });

    // Pause on hover
    slider.addEventListener('mouseenter', stopAutoPlay);
    slider.addEventListener('mouseleave', startAutoPlay);

    // Pause when page is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopAutoPlay();
        } else {
            startAutoPlay();
        }
    });

    // Start auto-play
    startAutoPlay();

    console.log('Testimonial slider initialized with', cards.length, 'cards');
}

/**
 * Add loading animation class when page loads
 */
window.addEventListener('load', function() {
    console.log('Window loaded - Adding page-loaded class');
    document.body.classList.add('page-loaded');

    // Trigger initial reveal for elements already in viewport
    const revealElements = document.querySelectorAll('.reveal');
    revealElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('active');
        }
    });
});

/**
 * Utility: Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility: Throttle function for performance
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Hero Image Slider - Time-sensitive rotation
 * Automatically switches between hero images
 */
function initHeroSlider() {
    console.log('Initializing hero slider...');

    const slides = document.querySelectorAll('.hero-slide');
    if (slides.length < 2) {
        console.log('Not enough slides for hero rotation');
        return;
    }

    let currentSlide = 0;
    const slideInterval = 5000; // 5 seconds

    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            if (i === index) {
                slide.classList.add('active');
            }
        });
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    // Start auto-rotation
    let autoRotate = setInterval(nextSlide, slideInterval);

    // Pause on hover
    const heroImage = document.querySelector('.hero-image');
    if (heroImage) {
        heroImage.addEventListener('mouseenter', () => {
            clearInterval(autoRotate);
        });

        heroImage.addEventListener('mouseleave', () => {
            autoRotate = setInterval(nextSlide, slideInterval);
        });
    }

    // Pause when page is not visible
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            clearInterval(autoRotate);
        } else {
            autoRotate = setInterval(nextSlide, slideInterval);
        }
    });

    console.log('Hero slider initialized with', slides.length, 'slides');
}
