// Interactive Robot Animation Script
document.addEventListener('DOMContentLoaded', function() {
    // Robot eye blinking animation
    function createRobotEyes() {
        const eyes = document.createElement('div');
        eyes.className = 'robot-eyes';
        eyes.innerHTML = `
            <div class="eye left-eye"></div>
            <div class="eye right-eye"></div>
        `;
        document.body.appendChild(eyes);
        
        // Blinking animation
        setInterval(() => {
            const leftEye = document.querySelector('.left-eye');
            const rightEye = document.querySelector('.right-eye');
            leftEye.style.height = '2px';
            rightEye.style.height = '2px';
            setTimeout(() => {
                leftEye.style.height = '20px';
                rightEye.style.height = '20px';
            }, 150);
        }, 3000);
    }
    
    // Futuristic loading animation
    function showLoadingSequence() {
        const loader = document.createElement('div');
        loader.className = 'robot-loader';
        loader.innerHTML = `
            <div class="loading-text">INITIALIZING...</div>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        `;
        document.body.appendChild(loader);
        
        setTimeout(() => {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.remove();
            }, 500);
        }, 2000);
    }
    
    // Holographic text effect
    function addHolographicEffect() {
        const textElements = document.querySelectorAll('h1, h2');
        textElements.forEach(element => {
            element.addEventListener('mouseenter', function() {
                this.style.textShadow = '0 0 5px #00ffff, 0 0 10px #00ffff, 0 0 15px #00ffff, 0 0 20px #00ffff';
                this.style.animation = 'hologram 0.5s infinite';
            });
            
            element.addEventListener('mouseleave', function() {
                this.style.textShadow = '0 0 10px rgba(0, 255, 255, 0.7)';
                this.style.animation = 'glow 1.5s infinite alternate';
            });
        });
    }
    
    // AI voice simulation
    function playRobotSound() {
        // Create audio context for synthetic robot sounds
        if (window.AudioContext || window.webkitAudioContext) {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            function beep(frequency, duration) {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.value = frequency;
                oscillator.type = 'square';
                
                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + duration);
            }
            
            // Robot startup sound sequence
            setTimeout(() => beep(800, 0.1), 100);
            setTimeout(() => beep(1000, 0.1), 250);
            setTimeout(() => beep(1200, 0.2), 400);
        }
    }
    
    // Particle system for futuristic background
    function createParticleSystem() {
        const canvas = document.createElement('canvas');
        canvas.className = 'particle-canvas';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        document.body.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const particles = [];
        
        for (let i = 0; i < 50; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: Math.random() * 3 + 1
            });
        }
        
        function animateParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'rgba(0, 255, 255, 0.3)';
            
            particles.forEach(particle => {
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
                if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
                
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fill();
            });
            
            requestAnimationFrame(animateParticles);
        }
        
        animateParticles();
    }
    
    // Initialize all robot features
    showLoadingSequence();
    setTimeout(() => {
        createRobotEyes();
        addHolographicEffect();
        createParticleSystem();
        playRobotSound();
    }, 2000);
    
    // Interactive button responses
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('button')) {
            playRobotSound();
            e.target.style.boxShadow = '0 0 20px #00ffff';
            setTimeout(() => {
                e.target.style.boxShadow = 'none';
            }, 300);
        }
    });
});