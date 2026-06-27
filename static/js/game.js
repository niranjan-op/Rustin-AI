document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const boardEl = document.getElementById('bingo-board');
    const drawBtn = document.getElementById('draw-btn');
    const lastNumberEl = document.getElementById('last-number');
    let board = [];
    let marked = Array(5).fill().map(() => Array(5).fill(false));

    themeToggle.addEventListener('click', () => {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-bs-theme', newTheme);
        console.log("Theme toggled to:", newTheme);
    });

    async function initGame() {
        console.log("Initializing game...");
        try {
            const res = await fetch('/api/new-game');
            const data = await res.json();
            console.log("Board received:", data.board);
            board = data.board;
            renderBoard();
        } catch (e) {
            console.error("Error initializing game:", e);
        }
    }

    function renderBoard() {
        boardEl.innerHTML = '';
        for (let r = 0; r < 5; r++) {
            for (let c = 0; c < 5; c++) {
                const colDiv = document.createElement('div');
                colDiv.className = 'col';
                const cell = document.createElement('div');
                cell.className = 'bingo-cell';
                cell.textContent = board[r][c];
                if (r === 2 && c === 2) {
                    cell.classList.add('marked');
                    marked[r][c] = true;
                }
                cell.onclick = () => markCell(r, c, cell);
                colDiv.appendChild(cell);
                boardEl.appendChild(colDiv);
            }
        }
    }

    function markCell(r, c, el) {
        if (r === 2 && c === 2) return;
        marked[r][c] = !marked[r][c];
        el.classList.toggle('marked');
        checkWin();
    }

    drawBtn.onclick = async () => {
        const res = await fetch('/api/draw-number');
        const data = await res.json();
        lastNumberEl.textContent = data.number;
    };

    async function checkWin() {
        const res = await fetch('/api/check-win', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ marked })
        });
        const data = await res.json();
        if (data.win) alert('BINGO!');
    }

    initGame();
});
