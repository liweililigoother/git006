document.addEventListener('DOMContentLoaded', () => {
    const gameContainer = document.getElementById('game-container');
    const plane = document.getElementById('player-plane');
    const healthEl = document.getElementById('health');
    const scoreEl = document.getElementById('score');
    const messageContainer = document.getElementById('critical-message-container');

    let health = 100;
    let score = 0;
    let criticalAnnounced = 0; // 0: not announced, 1, 2, 3 for each stage
    let isGameOver = false;

    const GAME_WIDTH = gameContainer.offsetWidth;
    const GAME_HEIGHT = gameContainer.offsetHeight;

    // --- Plane Movement ---
    document.addEventListener('mousemove', (e) => {
        if(isGameOver) return;
        let x = e.clientX - gameContainer.getBoundingClientRect().left;
        // Clamp plane position within game bounds
        x = Math.max(25, Math.min(x, GAME_WIDTH - 25));
        plane.style.transform = `translateX(${x - (plane.offsetWidth / 2)}px)`;
    });

    // --- Bombing ---
    gameContainer.addEventListener('click', (e) => {
        if(isGameOver) return;
        createBomb(e.clientX - gameContainer.getBoundingClientRect().left);
    });

    function createBomb(x) {
        const bomb = document.createElement('div');
        bomb.className = 'bomb';
        bomb.style.left = `${x - 4}px`;
        bomb.style.top = `${plane.offsetTop + 50}px`; // Start from plane's bottom
        gameContainer.appendChild(bomb);
    }

    // --- Targets ---
    function createTarget() {
        if(isGameOver) return;
        const target = document.createElement('div');
        target.className = 'target';
        const size = 30 + Math.random() * 40;
        target.style.width = `${size}px`;
        target.style.height = `${size}px`;
        target.style.left = `${Math.random() * (GAME_WIDTH - size)}px`;
        target.style.top = `${GAME_HEIGHT}px`; // Start from bottom and move up
        gameContainer.appendChild(target);
        
        // Add text to some targets for fun
        if (Math.random() > 0.7) {
            target.textContent = "I'm back!";
        }
    }

    // --- Game Loop ---
    let lastTime = 0;
    function gameLoop(timestamp) {
        if(isGameOver && !document.querySelector('.explosion')) {
            // Wait for explosions to finish before showing final message
             messageContainer.textContent = `游戏结束! 最终得分: ${score}`;
             messageContainer.style.color = '#00ff00'; // Green for final score
             return; // Stop the loop
        }
        
        const deltaTime = timestamp - lastTime;
        lastTime = timestamp;

        if (!isGameOver) {
            // Update bombs
            document.querySelectorAll('.bomb').forEach(bomb => {
                let top = parseFloat(bomb.style.top);
                top += 300 * (deltaTime / 1000); // speed
                if (top > GAME_HEIGHT) {
                    bomb.remove();
                } else {
                    bomb.style.top = `${top}px`;
                }
            });

            // Update targets (move them up)
            document.querySelectorAll('.target').forEach(target => {
                let top = parseFloat(target.style.top);
                top -= 100 * (deltaTime / 1000); // speed
                if (top < -target.offsetHeight) {
                    target.remove();
                    updateHealth(-10); // Lose health if target escapes
                } else {
                    target.style.top = `${top}px`;
                }
            });
            
            // Collision Detection
            checkCollisions();

            // Check Critical Health
            checkCriticalHealth();
        }

        requestAnimationFrame(gameLoop);
    }

    // --- Collision & Effects ---
    function checkCollisions() {
        const bombs = document.querySelectorAll('.bomb');
        const targets = document.querySelectorAll('.target');

        bombs.forEach(bomb => {
            const bombRect = bomb.getBoundingClientRect();
            targets.forEach(target => {
                const targetRect = target.getBoundingClientRect();
                if (
                    bombRect.left < targetRect.right &&
                    bombRect.right > targetRect.left &&
                    bombRect.top < targetRect.bottom &&
                    bombRect.bottom > targetRect.top
                ) {
                    bomb.remove();
                    createExplosion(targetRect.left + targetRect.width / 2, targetRect.top + targetRect.height / 2);
                    
                    // Anti-gravity effect
                    target.remove(); // Simple removal for now, can be replaced with animation
                    
                    updateScore(10);
                }
            });
        });
    }
    
    function createExplosion(x, y) {
        const explosion = document.createElement('div');
        explosion.className = 'explosion';
        explosion.style.left = `${x}px`;
        explosion.style.top = `${y}px`;
        gameContainer.appendChild(explosion);
        setTimeout(() => explosion.remove(), 500); // Cleanup explosion element
    }

    // --- Score & Health ---
    function updateHealth(change) {
        if(isGameOver) return;
        health += change;
        if (health <= 0) {
            health = 0;
            gameOver();
        }
        healthEl.textContent = health;
    }

    function updateScore(points) {
        if(isGameOver) return;
        score += points;
        scoreEl.textContent = score;
    }

    // --- "Important things are said three times" ---
    function checkCriticalHealth() {
        if (health <= 10 && health > 0 && criticalAnnounced < 1) {
            criticalAnnounced = 1;
            gameContainer.style.animation = "shake 0.5s";
            messageContainer.textContent = "注意：要掉下去了！";
        } else if (health <= 10 && health > 0 && criticalAnnounced < 2) {
            // This needs a trigger, let's tie it to time for simplicity
            setTimeout(() => {
                if(health > 0 && !isGameOver) {
                    criticalAnnounced = 2;
                     messageContainer.textContent = "注意：真的要掉下去了！！";
                }
            }, 3000); // 3 seconds after the first warning
        } else if (health <= 10 && health > 0 && criticalAnnounced < 3) {
            setTimeout(() => {
                 if(health > 0 && !isGameOver) {
                    criticalAnnounced = 3;
                    plane.style.borderBottomColor = 'red'; // Visual damage
                    messageContainer.textContent = "注意：说三遍了，真没救了！！！";
                 }
            }, 6000); // 6 seconds after the first warning
        }
        
        if (health > 10 && criticalAnnounced > 0) {
            criticalAnnounced = 0; // Reset if health is restored
            messageContainer.textContent = "";
            gameContainer.style.animation = "";
            plane.style.borderBottomColor = '#c0c0c0';
        }
    }
    
    function gameOver() {
        if(isGameOver) return;
        isGameOver = true;
        
        // Final big explosion on the plane
        const planeRect = plane.getBoundingClientRect();
        createExplosion(planeRect.left + planeRect.width/2, planeRect.top + planeRect.height/2);
        
        plane.remove(); // Plane is destroyed
    }

    // --- Start Game ---
    // Spawn targets periodically
    setInterval(() => {
        if(!isGameOver) createTarget();
    }, 2000);

    // Start the game loop
    requestAnimationFrame(gameLoop);
});
