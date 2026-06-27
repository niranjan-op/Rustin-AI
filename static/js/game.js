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
        html.setAttribute('data-bs-theme', currentTheme === 'dark' ? 'light' : 'dark');
    });

    async function initGame() {
        const res = await fetch('/api/new-game');
        const data = await res.json();
        board = data.board;
        renderBoard();
    }

    function renderBoard() {
        boardEl.innerHTML = '';
        for (let r = 0; r < 5; r++) {
            for (let c = 0; c < 5; c++) {
                const cell = document.createElement('div');
                cell.className = 'col-2-4 bingo-cell';
                cell.textContent = board[r][c];
                if (r === 2 && c === 2) cell.classList.add('marked');
                cell.onclick = () => markCell(r, c, cell);
                boardEl.appendChild(cell);
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
