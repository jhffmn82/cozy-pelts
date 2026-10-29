# Cozy Pelts

A cozy pixel-art clicker on the arctic ice, and a wholesome family business. Seals haul out onto the floes to lounge;
tap one and your hunter runs over and bonks it. Knocked-out seals go on the sled as pelts, and the sled has to be sent
up the road to the hut, where the trader pays in coins and asks no questions.

**Play:** https://jhffmn82.github.io/cozy-pelts/, or [on itch.io](https://jhffmn82.itch.io/cozy-pelts)

Tap or click a seal to bonk it, tap the ice to walk, tap the sled (or `S`) to send it up to the hut, `F` tosses a
fish, `Space` bonks the nearest seal.

If things take a turn: on a computer, `WASD` runs (hopping narrow water), `Space` jumps (with a somersault),
`Shift` dashes, clicking shoots where you point and right-clicking walks there; `1` `2` `3`, `Q` or the mouse
wheel switch weapons. On a phone, drag on the ice to run or tap to walk there, and use **FIRE** and **JUMP**.

Coins buy, at prices that multiply with every level:

- **Clubs:** driftwood, frozen salmon, whale bone, ship anchor, narwhal tusk. Each hits harder.
- **Fish Bucket**: more room on the ice, and the fish toss recharges 30% faster a level.
- **Bigger Sled** and a **Husky Team**: carry more per trip and get there faster. From three dogs, the team sets
  off on its own when the sled is full.
- **Seal Drones**, up to three: they lower a hook onto a lounging seal and fly it to a wood chipper by the hut.
- **Seal Decoy**: a wooden seal that tells the others it's safe up here. More seals, and more golden ones.
- **The Contraption**: the last big purchase, in three tiers. Its candy-striped tube loops once, then roams the
  water slurping seals out of the sea and straight into coins. Each tier is a little worse for the sea. Nobody
  knows what the third one does. Find out.

Hurt seals scoot for the water, napping ones take sneak bonks, golden ones are rare and skittish, and the gull steals
off the sled.

## How it's made

- Art: [PixelLab](https://pixellab.ai). The background is the concept painting converted to pixel art with the
  animals and HUD painted out; every sprite, animation and effect was generated or animated there
  (`tools/pl.py`, packed by `tools/pack.py`).
- Sound: [ElevenLabs](https://elevenlabs.io) sound effects, ambience and voice lines (`tools/audio.py`). The music box
  score is synthesised in the browser.
- itch.io: `python tools/itch.py` makes the upload zip, cover, banner, snowy page background and screenshots in
  `out/itch/`, drawn by the game itself; `itch/description.html` and `itch/settings.md` are the page's text and
  every setting on its form and theme.
- The game is one HTML file with everything inlined: `python tools/build.py` writes `docs/index.html`, which GitHub
  Pages serves. `python tools/publish.py` builds, commits and pushes.
