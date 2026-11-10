# STEEL BALL RUN: STAND RUSH — GitHub Pages edition

This is the original Pygame game logic adapted to run in a browser using Pygbag. The browser port retains the Python racing/combat/Stand/character/boss logic and the original shape-drawn graphics. The original five music tracks have been synthesized from the original Python audio generator and bundled as WAV files, avoiding a slow browser startup. Sound effects use the original synthesis function when the browser supports Pygame audio.

## Update an existing GitHub Pages repository

Upload the **contents** of this ZIP to the root of your repository, replacing `game/main.py` and `.github/workflows/pages.yml` and adding the `game/audio/` directory and `inject_fullscreen.py`. Keep the original folder structure. On GitHub, open **Actions**, wait for **Build and deploy Pygame to GitHub Pages** to finish, then hard refresh your game page with Ctrl+Shift+R.

The browser has a fixed **⛶ Fullscreen** button in the top-right corner of the page, independent of Python/Pygame. Click it to enter fullscreen; click **Exit fullscreen** or press Esc to leave. A small fullscreen control is also drawn in the upper-right of the game canvas. F11 is intercepted by some browsers and cannot be relied upon.

## New repository setup

1. Create a public GitHub repository and upload the project contents, including the hidden `.github` directory.
2. In **Settings → Pages**, select **GitHub Actions** as the deployment source.
3. Open **Actions** to monitor deployment, then visit `https://YOUR-USERNAME.github.io/REPO/`.

## Important compatibility notes

- The original Python gameplay and drawing routines are retained. Browser audio, storage, fullscreen and the asynchronous event loop require platform adaptations, so **pixel-for-pixel / frame-for-frame identity is not guaranteed** without a browser playtest.
- The browser saves progress to `localStorage`, not the desktop JSON file. The supplied JSON is included for reference; a previous browser save takes precedence.
- `python-chess` may be unavailable in some browser environments; chess mode needs separate verification.
- The original source optionally loads `stand_sprites.png`, but that file was not supplied. The original fallback drawing remains in use.
- The music tracks are generated from the game's original `_write_music_track` implementation; the browser may require a user click before audio can play.
- Keep a backup of the previously working version before replacing files.

## Local testing

Run `py -m pip install pygbag`, then `py -m pygbag game` in Command Prompt and open the displayed URL. To build the same HTML as GitHub Actions: `py -m pygbag --build game`, followed by `py inject_fullscreen.py`.
