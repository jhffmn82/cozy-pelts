"""Everything the itch.io page needs, in out/itch/:

    python tools/itch.py

  cozy-pelts-html5.zip   the game (docs/index.html as index.html), to upload as "played in the browser"
  cover.png              630 x 500, the thumbnail on itch.io's listings
  banner.png             960 x 280, the page's header image
  background.png         a tile of falling snow for the page background
  screenshot-*.png       1280 x 820, the game as a desktop browser shows it

The pictures are drawn by the game itself (docs/index.html, so run tools/build.py first), with the title lettered
in the game's own font and ledger colours (at weight 500, where its C still reads as a C). The Sealocalypse stays out of them, as it does out of the README.
Needs Playwright (with the installed Chrome) and Pillow.
"""
import base64, io, pathlib, random, zipfile
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'out' / 'itch'
GAME = ROOT / 'docs' / 'index.html'
W, H = 256, 231

# The game's own palette (the :root of game/src.html).
DUSK, DUSK2, WOOD, WOOD_DARK, PARCH, INK, BERRY, BERRY_DARK, SNOW = (
    '#2a2550', '#3b3470', '#6e4127', '#3d2315', '#f7e9d2', '#4b2a2b', '#c9333f', '#8c1e2a', '#fffaf3')

# Lettering for the cover and banner: a parchment sign in a wood frame, like the game's toasts and ledger.
COMPOSE = """<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@500&display=block">
<style>
  html, body { margin: 0; background: %(dusk)s; }
  #c { position: relative; width: %(w)dpx; height: %(h)dpx; overflow: hidden; font-family: 'Pixelify Sans'; }
  #c img { position: absolute; image-rendering: pixelated; }
  .sign { position: absolute; background: %(parch)s; color: %(ink)s; border: 6px solid %(wood)s; border-radius: 12px;
          box-shadow: 0 0 0 4px %(wood_dark)s, 0 10px 22px rgba(20, 10, 40, .45); text-align: center; }
  .sign b { display: block; font-weight: 500; color: %(berry_dark)s; letter-spacing: .02em; line-height: 1; text-shadow: 0 4px 0 #e2b98b; }
  .sign span { display: block; font-weight: 500; letter-spacing: .02em; }
</style>
<div id="c">%(body)s</div>"""


# Before the game loads: a seeded Math.random, and a switch (__hold) that keeps the game's own frame loop waiting, so
# the cover and banner scenes can be stepped by hand at a fixed 1/60 s and come out the same every run.
STEADY = """(() => {
  let seed = 20261029; Math.random = () => (seed = seed * 16807 % 2147483647) / 2147483647;
  const raf = window.requestAnimationFrame.bind(window); window.__hold = false;
  window.requestAnimationFrame = cb => raf(t => window.__hold ? window.requestAnimationFrame(cb) : cb(t));
})()"""
COVER_SEALS = ['pup', 'grey', 'grey', 'pup', 'gold', 'pup']


def compose(page, w, h, body):
    page.set_content(COMPOSE % dict(w=w, h=h, body=body, dusk=DUSK, parch=PARCH, ink=INK, wood=WOOD, wood_dark=WOOD_DARK, berry_dark=BERRY_DARK))
    page.evaluate('document.fonts.ready')
    page.wait_for_function('document.fonts.check("500 40px \'Pixelify Sans\'")')
    return page.locator('#c').screenshot()


def data_url(img):
    b = io.BytesIO(); img.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def build_zip():
    z = OUT / 'cozy-pelts-html5.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as f:
        f.write(GAME, 'index.html')
    print(f'{z.name}: {z.stat().st_size // 1024} KB')


def background():
    """Snow on the dusk, as a 240 px tile: soft flakes of two sizes and the odd sparkle, like the sky in the game."""
    rnd = random.Random(7)
    t = Image.new('RGBA', (240, 240), (0, 0, 0, 0))
    px = t.load()
    for _ in range(26):
        x, y, a = rnd.randrange(240), rnd.randrange(240), rnd.randrange(50, 120)
        for dx, dy in ([(0, 0), (1, 0), (0, 1), (1, 1)] if rnd.random() < .45 else [(0, 0)]):
            px[(x + dx) % 240, (y + dy) % 240] = (255, 250, 243, a)
    for _ in range(4):
        x, y = rnd.randrange(240), rnd.randrange(240)
        for dx, dy, a in [(0, 0, 170), (1, 0, 90), (-1, 0, 90), (0, 1, 90), (0, -1, 90)]:
            px[(x + dx) % 240, (y + dy) % 240] = (255, 250, 243, a)
    t = t.resize((480, 480), Image.NEAREST)
    t.save(OUT / 'background.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob('*.png'): f.unlink()
    build_zip()
    background()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1280, 'height': 820})
        page.add_init_script(STEADY)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(GAME.as_uri())
        page.wait_for_function('window.__cp !== undefined')
        page.wait_for_function('document.fonts.check("700 20px \'Pixelify Sans\'")')
        page.wait_for_timeout(800)
        ev = page.evaluate
        n = [0]

        def shot(name, wait=0):
            if wait: page.wait_for_timeout(wait)
            n[0] += 1
            page.screenshot(path=str(OUT / f'screenshot-{n[0]}-{name}.png'))

        def scene():
            """The ice as it is now, at one art pixel per pixel (the canvas is drawn at a whole 3x here)."""
            url = ev("document.querySelector('#view').toDataURL()")
            im = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGB')
            return im.resize((W, H), Image.NEAREST)

        def toast(text):
            # held on, since the game's own toasts would replace it or take it down mid-shot
            ev("t => { const e = document.querySelector('#toast'); e.textContent = t; e.classList.add('show'); window.__pin = setInterval(() => { e.textContent = t; e.classList.add('show'); }, 20); }", text)

        def spawn(kinds):
            ev("""ks => { const c = __cp; for (const k of ks) { if (!c.spawnSeal(false)) continue; const s = c.seals()[c.seals().length - 1];
                    s.type = k; s.T = c.TYPES[k]; s.hp = s.maxHp = s.T.hp; } }""", kinds)

        # The start card.
        ev('localStorage.clear()')
        shot('start')
        ev("document.querySelector('#startBtn').click(); const c = __cp; c.S.sound.voice = false; c.S.sound.sfx = false; c.S.sound.music = false; 1")
        # The banner's scene: the first evening, with the clock held and stepped, so it comes out the same every run.
        ev("__hold = true; const c = __cp; c.S.dayT = .8; c.step(150); 1")
        banner_scene = scene()
        ev("const c = __cp; c.S.dayT = .3; c.step(60); __hold = false; 1")
        # Day one: a few seals hauled out, one bonk mid-swing, the blood on the snow.
        spawn(['pup', 'grey', 'pup', 'gold'])
        page.wait_for_timeout(3200)
        ev("""(() => { const c = __cp, s = c.seals().find(s => s.type === 'pup' && ['idle', 'scoot', 'look', 'roll', 'nap'].includes(s.state)) || c.seals()[0];
                c.hitSeal(s); c.hitSeal(s); c.tap(s.x, s.y - 8); })()""")
        shot('bonk', 700)
        # The cover's scene, held and stepped as well: the anchor up over a grey seal, a stain where a pup was,
        # a loaded sled and the dogs.
        ev("""(() => { __hold = true; const c = __cp; c.S.coins = 3e6;
                for (const id of ['club', 'club', 'club', 'decoy', 'decoy', 'decoy', 'decoy', 'decoy', 'decoy', 'decoy', 'decoy', 'bucket', 'bucket', 'sled', 'dogs', 'dogs']) c.buy(id);
                c.refresh(); c.seals().length = 0; })()""")
        spawn(COVER_SEALS)
        ev("""(() => { const c = __cp; c.step(300);
                const live = c.seals().filter(s => ['idle', 'look', 'roll', 'nap'].includes(s.state));
                const pup = live.find(s => s.type === 'pup'); if (pup) while (pup.hp > 0) c.hitSeal(pup);
                c.step(90);
                // the grey seal and the hunter set down on the open floe in the middle, the anchor going up
                const h = c.hunter, v = c.seals().find(s => s.type === 'grey' && ['idle', 'look', 'roll', 'nap'].includes(s.state));
                if (v) { Object.assign(v, { x: 100, y: 186, state: 'idle', t: 0, alpha: 1 });
                         // nobody on top of it, nobody half in the water, and a few pelts on the sled
                         const keep = c.seals().filter(s => s === v || (['idle', 'look', 'roll', 'nap'].includes(s.state) && s.alpha >= 1 && Math.hypot(s.x - 100, (s.y - 186) * 1.5) > 40));
                         c.seals().length = 0; c.seals().push(...keep); c.S.sledB = [[30, 'pup'], [12, 'gold']];
                         Object.assign(h, { x: 126, y: 186, dir: -1, path: null, target: v, pending: 1, victim: v, swing: .08, struck: false }); c.step(1); }
              })()""")
        cover_scene = scene()
        ev("const c = __cp; c.step(60); __hold = false; 1")
        # A rare one surfaces: a ruby seal, which reads in a still (rainbow only cycles colour, holy is pale on snow).
        spawn(['ruby', 'pup', 'grey'])
        page.wait_for_timeout(3000)
        # in plain view on the floe by the dock, with room round it
        ev("""(() => { const c = __cp; let r = c.seals().find(s => s.type === 'ruby');
                if (!r) { c.seals().splice(0, 2); c.spawnSeal(false); r = c.seals()[c.seals().length - 1]; r.type = 'ruby'; r.T = c.TYPES.ruby; }
                Object.assign(r, { x: 168, y: 108, state: 'idle', t: 0, alpha: 1, dir: -1 });
                const keep = c.seals().filter(s => s === r || Math.hypot(s.x - 168, (s.y - 108) * 1.5) > 40); c.seals().length = 0; c.seals().push(...keep); })()""")
        toast('Your first ruby seal! Its pelts sell for 480 each.')
        shot('ruby-seal', 600)
        ev("clearInterval(window.__pin); document.querySelector('#toast').classList.remove('show')")
        # Drones, the chipper, a loaded sled and the dogs.
        ev("const c = __cp; for (const id of ['drones', 'drones', 'drones']) c.buy(id); c.refresh(); 1")
        spawn(['pup', 'grey', 'gold', 'pup', 'sapphire', 'pup'])
        shot('drones', 5200)
        ev("const c = __cp; c.S.sledB = [[40, 'pup'], [16, 'gold'], [8, 'ruby']]; c.sendSled(); 1")
        shot('sled', 3200)
        # Evening at camp.
        ev("const c = __cp; c.S.dayT = .8; 1")
        spawn(['pup', 'grey'])
        shot('evening', 2500)
        # The contraption, first tier, next morning: the tube roaming the water.
        ev("const c = __cp; c.S.dayT = .3; c.S.factory = 1; c.syncMachines(); c.refresh(); 1")
        spawn(['pup', 'grey', 'pup'])
        shot('contraption', 6500)
        if errors: print('page errors:', errors)

        # The cover: the camp at 3x, the sign over the sky.
        cp = browser.new_page(viewport={'width': 630, 'height': 500})
        img = data_url(cover_scene)
        (OUT / 'cover.png').write_bytes(compose(cp, 630, 500, f"""
          <img src="{img}" style="width:{W * 3}px;height:{H * 3}px;left:-126px;top:-150px">
          <div class="sign" style="left:28px;top:24px;padding:14px 26px 12px"><b style="font-size:72px">Cozy Pelts</b>
          <span style="font-size:22px;margin-top:8px">a wholesome family business</span></div>"""))
        # The banner: the hut, the mountains and the evening sky at 4x, the sign beside them.
        bp = browser.new_page(viewport={'width': 960, 'height': 280})
        img = data_url(banner_scene)
        (OUT / 'banner.png').write_bytes(compose(bp, 960, 280, f"""
          <img src="{img}" style="width:{W * 4}px;height:{H * 4}px;left:-64px;top:-40px">
          <div class="sign" style="left:36px;top:58px;padding:16px 30px 14px"><b style="font-size:80px">Cozy Pelts</b>
          <span style="font-size:24px;margin-top:10px">Seal goes in, pelt comes out.</span></div>"""))
        browser.close()
    for f in sorted(OUT.glob('*.png')):
        print(f'{f.name}: {Image.open(f).size[0]} x {Image.open(f).size[1]}')


if __name__ == '__main__':
    main()
