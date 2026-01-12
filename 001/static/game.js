document.addEventListener('DOMContentLoaded', () => {

    const svg = document.getElementById('game-board');
    const statusLabel = document.getElementById('status-label');
    const resetButton = document.getElementById('reset-button');
    const PIECE_RADIUS = 20;
    const NODE_RADIUS = 8;

    let nodeCoords = {};
    let adjList = {};
    let selectedNode = null;
    let currentPlayer = '';

    function drawBoard(positions) {
        svg.innerHTML = ''; // Clear board

        // Draw connections
        for (const startNode in adjList) {
            const startCoord = nodeCoords[startNode];
            for (const endNode of adjList[startNode]) {
                if (parseInt(startNode) < parseInt(endNode)) {
                    const endCoord = nodeCoords[endNode];
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', startCoord[0]);
                    line.setAttribute('y1', startCoord[1]);
                    line.setAttribute('x2', endCoord[0]);
                    line.setAttribute('y2', endCoord[1]);
                    line.setAttribute('class', 'line');
                    svg.appendChild(line);
                }
            }
        }

        // Draw nodes, pieces, and numbers
        for (const node in nodeCoords) {
            const coord = nodeCoords[node];
            
            // Node background
            const nodeCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            nodeCircle.setAttribute('cx', coord[0]);
            nodeCircle.setAttribute('cy', coord[1]);
            nodeCircle.setAttribute('r', PIECE_RADIUS + 2); // Make it slightly larger for clickability
            nodeCircle.setAttribute('class', 'node');
            nodeCircle.setAttribute('data-node', node);
            if (parseInt(node) === selectedNode) {
                nodeCircle.classList.add('selected');
            }
            svg.appendChild(nodeCircle);

            const pieceType = positions[node];
            if (pieceType) {
                const pieceCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                pieceCircle.setAttribute('cx', coord[0]);
                pieceCircle.setAttribute('cy', coord[1]);
                pieceCircle.setAttribute('r', PIECE_RADIUS);
                pieceCircle.setAttribute('class', `piece-${pieceType}`);
                svg.appendChild(pieceCircle);

                const pieceText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                pieceText.setAttribute('x', coord[0]);
                pieceText.setAttribute('y', coord[1]);
                pieceText.textContent = pieceType === 'D' ? 'Δ' : 'O';
                pieceText.setAttribute('class', `piece-text-${pieceType}`);
                svg.appendChild(pieceText);
            }
            
            // Node number
            const numText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            numText.setAttribute('x', coord[0]);
            numText.setAttribute('y', coord[1] + PIECE_RADIUS + 15);
            numText.textContent = node;
            numText.setAttribute('class', 'node-number');
            svg.appendChild(numText);
        }
    }

    async function handleNodeClick(nodeId) {
        if (currentPlayer !== 'D' || !nodeId) return;

        if (selectedNode === null) {
            // Select a piece
            const response = await fetch('/gamestate');
            const state = await response.json();
            if (state.positions[nodeId] === 'D') {
                selectedNode = nodeId;
                statusLabel.textContent = `选中棋子 at ${nodeId}. 请点击目标位置。`;
                drawBoard(state.positions);
            }
        } else {
            // Move the piece
            const startNode = selectedNode;
            const endNode = nodeId;
            selectedNode = null; // Reset selection regardless of move success

            try {
                const response = await fetch('/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start: startNode, end: endNode }),
                });

                const result = await response.json();

                if (response.ok) {
                    statusLabel.textContent = result.message || '移动成功。';
                    if (result.game_over) {
                        currentPlayer = '';
                        statusLabel.textContent = `游戏结束! ${result.win_message}`;
                    } else {
                        statusLabel.textContent = `回合 ${Math.floor(result.turn_count)}: 到你了 (Δ).`;
                    }
                     drawBoard(result.positions);
                } else {
                    throw new Error(result.error || '无效移动');
                }

            } catch (error) {
                statusLabel.textContent = `错误: ${error.message}`;
                // Re-fetch state to revert visual selection
                fetchGameState();
            }
        }
    }
    
    async function fetchGameState() {
        try {
            const response = await fetch('/gamestate');
            const state = await response.json();
            
            nodeCoords = state.node_coords;
            adjList = state.adj_list;
            currentPlayer = state.current_player;

            if (state.game_over) {
                statusLabel.textContent = `游戏结束! ${state.win_message}`;
            } else {
                statusLabel.textContent = state.message;
            }
            
            drawBoard(state.positions);

        } catch (error) {
            statusLabel.textContent = '无法加载游戏状态，请刷新页面。';
            console.error('Error fetching game state:', error);
        }
    }

    async function resetGame() {
        try {
            await fetch('/reset', { method: 'POST' });
            selectedNode = null;
            fetchGameState();
        } catch (error) {
            statusLabel.textContent = '重置游戏失败。';
            console.error('Error resetting game:', error);
        }
    }

    svg.addEventListener('click', (event) => {
        const target = event.target;
        if (target.classList.contains('node')) {
            const nodeId = parseInt(target.getAttribute('data-node'));
            handleNodeClick(nodeId);
        }
    });

    resetButton.addEventListener('click', resetGame);

    // Initial load
    fetchGameState();
});
