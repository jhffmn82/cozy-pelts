# Cozy Pelts

A cozy pixel-art clicker on the arctic ice. Seals haul out onto the floes to lounge; tap one and your hunter runs over
and bonks it for pelts. Hurt seals scoot for the water, napping ones take sneak bonks, golden ones are rare and
skittish, and the gull has its eye on your sled. Spend pelts on a sturdier club, a husky with a helper sled, warmer
mittens, snow boots, a fish bucket and hot cocoa, then upgrade the camp.

**Play:** https://jhffmn82.github.io/cozy-pelts/

Tap or click a seal to bonk it, tap the ice to walk, `F` tosses a fish, `Space` bonks the nearest seal.

## How it's made

- Art: [PixelLab](https://pixellab.ai). The background is the concept painting converted to pixel art with the
  animals and HUD painted out; every sprite, animation and effect was generated or animated there
  (`tools/pl.py`, packed by `tools/pack.py`).
- Sound: [ElevenLabs](https://elevenlabs.io) sound effects, ambience and voice lines (`tools/audio.py`). The music box
  score is synthesised in the browser.
- The game is one HTML file with everything inlined: `python tools/build.py` writes `docs/index.html`, which GitHub
  Pages serves. `python tools/publish.py` builds, commits and pushes.
