// ============================================================================
// JINX'S MAGICAL REWIND MACHINE - Landing Page
// ============================================================================

const API_BASE_URL = 'http://localhost:5000';

// ============================================================================
// PAGE LOAD ANIMATIONS
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initBackgroundStars();
    animatePageEntrance();
    setupFormHandlers();
});

// Create animated background stars
function initBackgroundStars() {
    const starsContainer = document.getElementById('stars');
    const starCount = 100;

    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        starsContainer.appendChild(star);

        // Animate each star with GSAP
        gsap.to(star, {
            opacity: Math.random() * 0.5 + 0.3,
            duration: Math.random() * 2 + 1,
            repeat: -1,
            yoyo: true,
            ease: 'power1.inOut'
        });
    }
}

// Animate logo and form entrance
function animatePageEntrance() {
    const logo = document.getElementById('logo');
    const formCard = document.getElementById('formCard');

    // Logo explosion entrance
    gsap.timeline()
        .from(logo, {
            scale: 0,
            rotation: -180,
            opacity: 0,
            duration: 1.2,
            ease: 'back.out(1.7)'
        })
        .to(logo, {
            opacity: 1,
            duration: 0.3
        }, '-=0.8')
        // Animate each heading word separately
        .from('#logo h1, #logo h2, #logo h3', {
            y: -50,
            opacity: 0,
            stagger: 0.2,
            duration: 0.6,
            ease: 'power3.out'
        }, '-=0.6');

    // Form card slides up
    gsap.timeline({ delay: 0.8 })
        .from(formCard, {
            y: 100,
            opacity: 0,
            duration: 1,
            ease: 'power3.out'
        })
        .to(formCard, {
            opacity: 1,
            duration: 0.3
        }, '-=0.8')
        // Animate form fields
        .from('.form-group', {
            x: -30,
            opacity: 0,
            stagger: 0.15,
            duration: 0.5,
            ease: 'power2.out'
        }, '-=0.5');
}

// ============================================================================
// FORM HANDLING
// ============================================================================

function setupFormHandlers() {
    const form = document.getElementById('rewindForm');
    const submitBtn = document.getElementById('submitBtn');

    // Add focus animations to inputs
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            gsap.to(input, {
                scale: 1.02,
                duration: 0.2,
                ease: 'power2.out'
            });
        });

        input.addEventListener('blur', () => {
            gsap.to(input, {
                scale: 1,
                duration: 0.2,
                ease: 'power2.out'
            });
        });
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleFormSubmit();
    });
}

async function handleFormSubmit() {
    const gameName = document.getElementById('gameName').value.trim();
    const tagLine = document.getElementById('tagLine').value.trim();
    const platform = document.getElementById('platform').value;

    const submitBtn = document.getElementById('submitBtn');
    const loadingState = document.getElementById('loadingState');
    const errorMessage = document.getElementById('errorMessage');

    // Hide error if showing
    errorMessage.classList.add('hidden');

    // Show loading state
    submitBtn.classList.add('hidden');
    loadingState.classList.remove('hidden');

    // Animate loading spinner
    gsap.to('.spinner', {
        rotation: 360,
        duration: 1,
        repeat: -1,
        ease: 'linear'
    });

    try {
        // Call backend API
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                gameName: gameName,
                tagLine: tagLine,
                platform: platform,
                matchCount: 30
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze player');
        }

        // Success! Store data and trigger explosion
        storePlayerData(data, gameName, tagLine);
        await triggerExplosionTransition();

    } catch (error) {
        console.error('Error:', error);

        // Show error message
        errorMessage.textContent = `💥 Oops! ${error.message}. Try again!`;
        errorMessage.classList.remove('hidden');

        // Shake the form on error
        gsap.to('#formCard', {
            x: [-10, 10, -10, 10, 0],
            duration: 0.5,
            ease: 'power2.inOut'
        });

        // Reset button state
        submitBtn.classList.remove('hidden');
        loadingState.classList.add('hidden');
    }
}

// Store player data in localStorage for map page
function storePlayerData(data, gameName, tagLine) {
    localStorage.setItem('rewindData', JSON.stringify({
        playerInfo: {
            gameName,
            tagLine,
            ...data.player
        },
        zones: data.zones,
        metadata: data.metadata,
        session_token: data.session_token
    }));
}

// ============================================================================
// EXPLOSION TRANSITION
// ============================================================================

async function triggerExplosionTransition() {
    const formCard = document.getElementById('formCard');
    const logo = document.getElementById('logo');

    // Create explosion particles
    createExplosionParticles();

    // Animate explosion sequence
    const timeline = gsap.timeline({
        onComplete: () => {
            // Navigate to map page after explosion
            window.location.href = 'map.html';
        }
    });

    timeline
        // Shake everything
        .to([logo, formCard], {
            x: () => Math.random() * 20 - 10,
            y: () => Math.random() * 20 - 10,
            duration: 0.1,
            repeat: 5,
            yoyo: true,
            ease: 'power2.inOut'
        })
        // Explosion - scale up and fade
        .to([logo, formCard], {
            scale: 1.5,
            opacity: 0,
            duration: 0.6,
            ease: 'power2.in'
        }, '-=0.3')
        // Flash screen
        .to('body', {
            backgroundColor: '#FF1493',
            duration: 0.1
        }, '-=0.3')
        .to('body', {
            backgroundColor: '#00D4FF',
            duration: 0.1
        })
        .to('body', {
            backgroundColor: '#050816',
            duration: 0.2
        });

    return timeline;
}

function createExplosionParticles() {
    const particleCount = 50;
    const colors = ['#FF1493', '#00D4FF', '#9B30FF', '#FFFFFF'];

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.left = '50%';
        particle.style.top = '50%';
        document.body.appendChild(particle);

        // Animate particle explosion
        gsap.to(particle, {
            x: (Math.random() - 0.5) * window.innerWidth,
            y: (Math.random() - 0.5) * window.innerHeight,
            opacity: 0,
            scale: Math.random() * 2,
            duration: 1.5,
            ease: 'power2.out',
            onComplete: () => {
                particle.remove();
            }
        });
    }
}

// ============================================================================
// UTILITY: Check if we have cached data (for testing)
// ============================================================================

// Allow users to go directly to map if they have data
window.addEventListener('load', () => {
    const cachedData = localStorage.getItem('rewindData');

    if (cachedData) {
        // Add a "View Map" button if data exists
        const formCard = document.getElementById('formCard');
        const existingMapBtn = document.getElementById('viewMapBtn');

        if (!existingMapBtn) {
            const viewMapBtn = document.createElement('button');
            viewMapBtn.id = 'viewMapBtn';
            viewMapBtn.className = 'w-full mt-4 py-3 bg-jinx-blue/20 border border-jinx-blue text-jinx-blue font-semibold rounded-lg hover:bg-jinx-blue hover:text-white transition-all duration-300 font-body';
            viewMapBtn.textContent = '🗺️ View Previous Rewind';
            viewMapBtn.onclick = () => {
                window.location.href = 'map.html';
            };

            formCard.appendChild(viewMapBtn);

            // Animate button in
            gsap.from(viewMapBtn, {
                y: 20,
                opacity: 0,
                duration: 0.5,
                delay: 1.5,
                ease: 'power2.out'
            });
        }
    }
});
