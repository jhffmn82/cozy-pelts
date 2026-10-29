# itch.io page settings

Everything the "Create new project" form and the theme editor ask for. `python tools/itch.py` builds the files it names
in `out/itch/` (from `docs/index.html`, so build first), and `itch/description.html` is the description.

## Create new project (itch.io → Dashboard → Create new project)

| Field | Value |
|---|---|
| Title | Cozy Pelts |
| Project URL | `cozy-pelts` |
| Short description or tagline | A cozy pixel-art clicker about a wholesome family business on the ice. |
| Classification | Games |
| Kind of project | HTML |
| Release status | Released |
| Pricing | No payments |
| Uploads | `out/itch/cozy-pelts-html5.zip`, then tick **This file will be played in the browser** |
| Embed options | Embed in page; viewport **1200 × 760** (the ice draws at a whole 3x there, with the ledger beside it and nothing to scroll); tick **Mobile friendly** (orientation: Default) and **Fullscreen button**; leave **Automatically start on page load** off, so the player's click starts the game with sound |
| Description | Paste from `itch/description.html` (open it in a browser, select the text in the parchment box, copy) |
| Genre | Simulation |
| Tags | clicker, incremental, idle, cozy, cute, pixel-art, comedy, dark-humor, funny, winter |
| AI generation disclosure | Yes. Graphics (PixelLab), sound (ElevenLabs effects and voices), and text and code (written with Claude) |
| App store links, custom noun | Leave empty |
| Community | Comments |
| Visibility | Draft first. Check the game plays on the page, then Public |
| Cover image | `out/itch/cover.png` (630 × 500) |
| Screenshots | The seven `out/itch/screenshot-*.png`, in order. None of them shows the Sealocalypse, which stays a surprise |

## Edit theme (on the project page, after saving)

The game's own palette: a dusky arctic evening outside, the parchment ledger inside.

| Setting | Value |
|---|---|
| Banner | `out/itch/banner.png` |
| Background | `#2a2550`, with `out/itch/background.png` as its image, tiled (snow) |
| Inner background | `#f7e9d2` |
| Text | `#4b2a2b` |
| Links | `#8c1e2a` |
| Buttons | `#c9333f` |
| Fonts | Pixelify Sans for headers if the list has it (the game's font), otherwise a pixel font such as Silkscreen; body text left as it is |

## Later updates

butler pushes a new build to the same page from the command line: `butler push out/itch/cozy-pelts-html5.zip <your-itch-username>/cozy-pelts:html5`, with an itch.io API key from Settings → API keys.
