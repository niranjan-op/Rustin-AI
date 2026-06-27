# Bingo Game Project

## Overview
A web-based Bingo game with a Flask backend and Bootstrap frontend.

## Tech Stack
- Backend: Python, Flask
- Frontend: HTML5, Bootstrap 5, JavaScript (Vanilla)
- Styling: CSS3 with custom properties for theme toggling.

## Directory Structure
- `app.py`: Flask application with game logic.
- `templates/index.html`: Main game interface.
- `static/css/style.css`: Theme-aware styling.
- `static/js/game.js`: Frontend game interaction.

## Architectural Decisions
- Used Flask for simple state management.
- Used CSS variables for theme toggling (Dark/Light).
- Used Bootstrap 5 for layout.
- Smooth transitions implemented via CSS `transition` properties.

## Known Issues
- Win detection is currently client-side state sent to server.
- No persistent storage (state resets on server restart).
