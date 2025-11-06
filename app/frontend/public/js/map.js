// ============================================================================
// JINX'S MAGICAL REWIND MACHINE - Interactive Map with Character Movement
// ============================================================================

let playerData = null;
let character = {
    x: 0,
    y: 0,
    element: null,
    isMoving: false
};

let camera = {
    x: 0,
    y: 0,
    zoom: 1.8,  // Start zoomed IN!
    minZoom: 1,
    maxZoom: 3
};

let mapState = {
    width: 0,
    height: 0,
    element: null,
    container: null
};

const ZONE_PROXIMITY_THRESHOLD = 150; // pixels - how close to be to interact with zone
const CHARACTER_SPEED = 400; // pixels per second
const CAMERA_SMOOTHNESS = 0.3; // seconds for camera follow

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadPlayerData();
    initializeMap();
    createCharacter();
    setupEventListeners();
    animatePageEntrance();
    startGameLoop();
});

// Load player data from localStorage
function loadPlayerData() {
    console.log('🔍 Loading data from localStorage...');
    const rawData = localStorage.getItem('rewindData');

    if (!rawData) {
        console.error('❌ No data in localStorage!');
        alert('No rewind data found. Please analyze a player first!');
        window.location.href = 'index.html';
        return;
    }

    console.log('✅ Found data in localStorage:', rawData.substring(0, 200) + '...');

    try {
        playerData = JSON.parse(rawData);
        console.log('✅ Parsed player data successfully:', playerData);
        console.log('Player info:', playerData.playerInfo);
        console.log('Zones:', Object.keys(playerData.zones || {}));
        console.log('Metadata:', playerData.metadata);

        updatePlayerInfo();
        // updateStatsCard(); // Disabled - stats card elements not in HTML
    } catch (error) {
        console.error('❌ Error parsing player data:', error);
        console.error('Raw data:', rawData);
        alert('Error loading data. Please try again.');
        window.location.href = 'index.html';
    }
}

// Initialize map dimensions and viewport
function initializeMap() {
    const mapContainer = document.querySelector('.map-container');
    const mapImage = document.querySelector('.map-image');

    mapState.container = mapContainer;
    mapState.element = mapImage;

    // Get map dimensions after image loads
    mapImage.addEventListener('load', () => {
        updateMapDimensions();
        centerCameraOnMap();
    });

    // If image already loaded
    if (mapImage.complete) {
        updateMapDimensions();
        centerCameraOnMap();
    }
}

function updateMapDimensions() {
    const rect = mapState.element.getBoundingClientRect();
    mapState.width = rect.width;
    mapState.height = rect.height;
}

function centerCameraOnMap() {
    camera.x = mapState.width / 2;
    camera.y = mapState.height / 2;

    // Apply initial zoom
    console.log('📹 Setting initial zoom to:', camera.zoom);
    applyCameraTransform();
}

// Create playable character
function createCharacter() {
    console.log('🎮 Creating character...');

    const charElement = document.createElement('div');
    charElement.id = 'character';
    charElement.innerHTML = `
        <div class="character-sprite">
            <div class="character-glow"></div>
            <div class="character-body"></div>
            <div class="character-trail"></div>
        </div>
    `;

    mapState.container.appendChild(charElement);
    character.element = charElement;

    // Start at center of map
    character.x = mapState.width / 2;
    character.y = mapState.height / 2;

    console.log('✅ Character created at:', character.x, character.y);
    console.log('Map size:', mapState.width, 'x', mapState.height);

    updateCharacterPosition();

    // Make sure character is visible
    setTimeout(() => {
        if (character.element) {
            console.log('Character element:', character.element);
            console.log('Character position:', character.element.style.left, character.element.style.top);
        }
    }, 100);
}

function updateCharacterPosition() {
    if (!character.element) return;

    gsap.set(character.element, {
        left: character.x,
        top: character.y,
        xPercent: -50,
        yPercent: -50
    });
}

// Update header with player info
function updatePlayerInfo() {
    const playerNameEl = document.getElementById('playerName');

    if (playerData && playerData.playerInfo) {
        const { gameName, tagLine, summoner_name, level, rank } = playerData.playerInfo;
        const displayName = summoner_name || `${gameName}#${tagLine}`;
        const levelText = level ? `Level ${level}` : '';
        const rankText = rank ? `${rank.tier} ${rank.rank}` : '';

        playerNameEl.textContent = `${displayName} ${levelText} ${rankText}`.trim();
    }
}

// Update stats summary card
function updateStatsCard() {
    const metadata = playerData.metadata || {};

    const matchCount = metadata.matches_analyzed || '30';
    document.getElementById('matchCount').textContent = matchCount;

    const cached = metadata.cached ? 'Cached' : 'Fresh';
    document.getElementById('cacheStatus').textContent = cached;

    const generatedAt = metadata.generated_at;
    if (generatedAt) {
        const date = new Date(generatedAt * 1000);
        const timeAgo = getTimeAgo(date);
        document.getElementById('generatedAt').textContent = timeAgo;
    }
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };

    for (let [name, secondsInInterval] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInInterval);
        if (interval >= 1) {
            return interval === 1 ? `1 ${name} ago` : `${interval} ${name}s ago`;
        }
    }

    return 'Just now';
}

// ============================================================================
// ANIMATIONS
// ============================================================================

function animatePageEntrance() {
    // Zones pop in with stagger
    gsap.from('.zone-overlay', {
        scale: 0,
        opacity: 0,
        stagger: 0.1,
        duration: 0.6,
        ease: 'back.out(1.7)',
        delay: 0.5
    });

    // Character appears immediately (no delay!)
    if (character.element) {
        console.log('🎬 Animating character entrance');
        gsap.from(character.element, {
            scale: 0,
            opacity: 0,
            duration: 0.8,
            ease: 'elastic.out(1, 0.5)',
            delay: 0.3
        });
    } else {
        console.warn('⚠️ Character element not found for animation');
    }
}

// ============================================================================
// CHARACTER MOVEMENT
// ============================================================================

function moveCharacterTo(targetX, targetY) {
    // Clamp to map bounds
    targetX = Math.max(50, Math.min(mapState.width - 50, targetX));
    targetY = Math.max(50, Math.min(mapState.height - 50, targetY));

    const distance = Math.hypot(targetX - character.x, targetY - character.y);
    const duration = distance / CHARACTER_SPEED;

    // Calculate rotation angle
    const angle = Math.atan2(targetY - character.y, targetX - character.x) * (180 / Math.PI);

    character.isMoving = true;

    // Animate character movement
    gsap.to(character, {
        x: targetX,
        y: targetY,
        duration: duration,
        ease: 'power1.inOut',
        onUpdate: () => {
            updateCharacterPosition();
            updateCamera();
            checkZoneProximity();
        },
        onComplete: () => {
            character.isMoving = false;
            checkZoneInteraction();
        }
    });

    // Rotate character toward movement direction
    gsap.to(character.element, {
        rotation: angle,
        duration: 0.3,
        ease: 'power2.out'
    });

    // Create movement particles
    createMovementTrail(targetX, targetY);
}

function createMovementTrail(targetX, targetY) {
    const trailCount = 5;
    const startX = character.x;
    const startY = character.y;

    for (let i = 0; i < trailCount; i++) {
        setTimeout(() => {
            const particle = document.createElement('div');
            particle.className = 'movement-particle';
            particle.style.left = `${character.x}px`;
            particle.style.top = `${character.y}px`;
            mapState.container.appendChild(particle);

            gsap.to(particle, {
                opacity: 0,
                scale: 0,
                duration: 0.5,
                ease: 'power2.out',
                onComplete: () => particle.remove()
            });
        }, i * 100);
    }
}

// ============================================================================
// CAMERA SYSTEM
// ============================================================================

function updateCamera() {
    // Camera follows character
    const targetCameraX = character.x;
    const targetCameraY = character.y;

    // Smooth camera movement
    gsap.to(camera, {
        x: targetCameraX,
        y: targetCameraY,
        duration: CAMERA_SMOOTHNESS,
        ease: 'power2.out'
    });

    applyCameraTransform();
}

function applyCameraTransform() {
    const container = mapState.container;
    const containerRect = container.getBoundingClientRect();
    const centerX = containerRect.width / 2;
    const centerY = containerRect.height / 2;

    // Calculate transform to center camera on character
    const translateX = centerX - camera.x * camera.zoom;
    const translateY = centerY - camera.y * camera.zoom;

    gsap.set(container, {
        x: translateX,
        y: translateY,
        scale: camera.zoom
    });
}

function zoomCamera(delta) {
    const zoomSpeed = 0.1;
    const newZoom = camera.zoom + delta * zoomSpeed;

    camera.zoom = Math.max(camera.minZoom, Math.min(camera.maxZoom, newZoom));

    gsap.to(mapState.container, {
        scale: camera.zoom,
        duration: 0.3,
        ease: 'power2.out'
    });
}

// ============================================================================
// ZONE INTERACTION
// ============================================================================

function checkZoneProximity() {
    const zones = document.querySelectorAll('.zone-overlay');

    zones.forEach(zone => {
        const rect = zone.getBoundingClientRect();
        const containerRect = mapState.container.getBoundingClientRect();

        // Get zone center in map coordinates
        const zoneX = (rect.left + rect.width / 2 - containerRect.left) / camera.zoom;
        const zoneY = (rect.top + rect.height / 2 - containerRect.top) / camera.zoom;

        const distance = Math.hypot(character.x - zoneX, character.y - zoneY);

        if (distance < ZONE_PROXIMITY_THRESHOLD) {
            zone.classList.add('zone-nearby');
            highlightZone(zone, true);
        } else {
            zone.classList.remove('zone-nearby');
            highlightZone(zone, false);
        }
    });
}

function highlightZone(zone, isNear) {
    if (isNear) {
        gsap.to(zone, {
            borderWidth: '4px',
            borderColor: 'rgba(255, 20, 147, 1)',
            backgroundColor: 'rgba(255, 20, 147, 0.4)',
            scale: 1.05,
            duration: 0.3,
            ease: 'power2.out'
        });
    } else {
        gsap.to(zone, {
            borderWidth: '2px',
            borderColor: 'rgba(255, 20, 147, 0.3)',
            backgroundColor: 'rgba(255, 20, 147, 0.1)',
            scale: 1,
            duration: 0.3,
            ease: 'power2.out'
        });
    }
}

function checkZoneInteraction() {
    const nearbyZones = document.querySelectorAll('.zone-nearby');

    if (nearbyZones.length > 0) {
        // Auto-open first nearby zone
        const zone = nearbyZones[0];
        const zoneId = zone.getAttribute('data-zone');

        // Flash zone to show interaction
        gsap.timeline()
            .to(zone, {
                scale: 1.2,
                duration: 0.2,
                ease: 'power2.out'
            })
            .to(zone, {
                scale: 1.05,
                duration: 0.2,
                ease: 'power2.in'
            });

        // Show zone story
        setTimeout(() => handleZoneClick(zoneId, zone), 300);
    }
}

function handleZoneClick(zoneId, zoneElement) {
    console.log('Zone activated:', zoneId);

    const zones = playerData.zones || {};
    const zoneData = zones[zoneId];

    if (!zoneData) {
        showModal('Zone Not Found', 'No story available for this zone yet. Try refreshing your data!', {});
        return;
    }

    showModal(zoneData.zone_name, zoneData.story, zoneData.stats || {});
}

// ============================================================================
// MODAL SYSTEM
// ============================================================================

function showModal(zoneName, story, stats) {
    const modal = document.getElementById('storyModal');
    const titleEl = document.getElementById('modalZoneTitle');
    const contentEl = document.getElementById('storyContent');
    const statsEl = document.getElementById('statsContent');

    titleEl.textContent = zoneName;
    contentEl.textContent = story;

    if (stats && Object.keys(stats).length > 0) {
        statsEl.innerHTML = formatStats(stats);
        document.getElementById('modalStats').style.display = 'block';
    } else {
        document.getElementById('modalStats').style.display = 'none';
    }

    modal.classList.add('active');

    gsap.timeline()
        .fromTo('.modal-content',
            { scale: 0.7, opacity: 0, y: 100 },
            { scale: 1, opacity: 1, y: 0, duration: 0.5, ease: 'back.out(1.7)' }
        );
}

function closeModal() {
    const modal = document.getElementById('storyModal');

    gsap.to('.modal-content', {
        scale: 0.7,
        opacity: 0,
        y: 100,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => {
            modal.classList.remove('active');
        }
    });
}

function formatStats(stats) {
    const statLines = [];

    for (let [key, value] of Object.entries(stats)) {
        const formattedKey = key
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');

        let formattedValue = value;
        if (typeof value === 'number') {
            formattedValue = value.toFixed(2);
        }

        statLines.push(`<div class="flex justify-between">
            <span>${formattedKey}:</span>
            <span class="text-jinx-pink font-semibold">${formattedValue}</span>
        </div>`);
    }

    return statLines.join('');
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function setupEventListeners() {
    // Click map to move character
    mapState.container.addEventListener('click', (e) => {
        // Don't move if clicking on a zone overlay
        if (e.target.classList.contains('zone-overlay') || e.target.classList.contains('zone-label')) {
            return;
        }

        const rect = mapState.container.getBoundingClientRect();
        const x = (e.clientX - rect.left) / camera.zoom;
        const y = (e.clientY - rect.top) / camera.zoom;

        moveCharacterTo(x, y);
    });

    // Zoom with mouse wheel
    mapState.container.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -1 : 1;
        zoomCamera(delta);
    });

    // Modal close
    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    document.getElementById('closeModalBtn2').addEventListener('click', closeModal);

    document.getElementById('storyModal').addEventListener('click', (e) => {
        if (e.target.id === 'storyModal') {
            closeModal();
        }
    });

    // Navigation buttons
    document.getElementById('backBtn').addEventListener('click', () => {
        window.location.href = 'index.html';
    });

    document.getElementById('refreshBtn').addEventListener('click', handleRefresh);

    // Keyboard controls
    setupKeyboardControls();
}

function setupKeyboardControls() {
    const moveSpeed = 100;

    document.addEventListener('keydown', (e) => {
        // ESC to close modal
        if (e.key === 'Escape') {
            closeModal();
            return;
        }

        // SPACEBAR - test movement (move to random spot)
        if (e.key === ' ') {
            e.preventDefault();
            const randomX = Math.random() * mapState.width;
            const randomY = Math.random() * mapState.height;
            console.log('🎯 SPACEBAR pressed - moving to random spot:', randomX, randomY);
            moveCharacterTo(randomX, randomY);
            return;
        }

        // Arrow keys to move character
        let dx = 0, dy = 0;

        switch(e.key) {
            case 'ArrowUp':
            case 'w':
            case 'W':
                dy = -moveSpeed;
                break;
            case 'ArrowDown':
            case 's':
            case 'S':
                dy = moveSpeed;
                break;
            case 'ArrowLeft':
            case 'a':
            case 'A':
                dx = -moveSpeed;
                break;
            case 'ArrowRight':
            case 'd':
            case 'D':
                dx = moveSpeed;
                break;
            default:
                return;
        }

        e.preventDefault();
        console.log(`⌨️ Keyboard: Moving character by dx=${dx}, dy=${dy}`);
        moveCharacterTo(character.x + dx, character.y + dy);
    });
}

// ============================================================================
// GAME LOOP
// ============================================================================

function startGameLoop() {
    // Update zone proximity continuously
    setInterval(() => {
        if (!character.isMoving) {
            checkZoneProximity();
        }
    }, 100);
}

// ============================================================================
// REFRESH FUNCTIONALITY
// ============================================================================

async function handleRefresh() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.textContent = '⏳ Refreshing...';
    refreshBtn.disabled = true;

    try {
        const { gameName, tagLine, riot_id } = playerData.playerInfo;
        const riotIdFormatted = riot_id ? riot_id.replace('#', '-') : `${gameName}-${tagLine}`;

        const response = await fetch(`/api/refresh/${riotIdFormatted}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to refresh data');
        }

        localStorage.setItem('rewindData', JSON.stringify({
            playerInfo: { gameName, tagLine, ...data.player },
            zones: data.zones,
            metadata: data.metadata
        }));

        location.reload();

    } catch (error) {
        console.error('Refresh error:', error);
        alert(`Failed to refresh: ${error.message}`);
        refreshBtn.textContent = '🔄 Refresh';
        refreshBtn.disabled = false;
    }
}
