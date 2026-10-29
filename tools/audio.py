"""Every sound in Cozy Pelts, from ElevenLabs: effects, the hunter's and the narrator's lines, and the music.

    python tools/audio.py            make whatever is missing, then write game/audio/*.mp3 and game/audio.json
    python tools/audio.py --list     what would be made, and nothing else
    python tools/audio.py --music    also the two music tracks (the key needs the music_generation permission)

The key is Shoulda Listened's (.secrets/elevenlabs-api-key.txt there) unless this project has its own, or
ELEVENLABS_API_KEY. Each take is cached in art/audio/cache under a hash of its request, so a run only pays for what
changed. Needs numpy and lameenc.
"""
import concurrent.futures, hashlib, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'art' / 'audio' / 'cache'
OUT = ROOT / 'game' / 'audio'
API = 'https://api.elevenlabs.io/v1'
RATES = {'sfx': 44100, 'voice': 22050, 'music': 44100}
STEREO = {'sfx'}   # sound effects come back as interleaved stereo
VOICES = {'Jessica': 'cgSgspJ2msm6clMCkdW9', 'George': 'JBFqnCBsd6RMkjVDRZzb'}
HUNTER, NARRATOR = 'Jessica', 'George'

# name: (takes, prompt, seconds, loop)
SFX = {
    'squeal': (4, 'a cute baby seal pup squeals once, a short high-pitched cartoon yelp', .8, False),
    'wail': (2, 'a cute baby seal pup lets out a long wobbly cartoon wail that fades into a whimper', 1.6, False),
    'bonk': (3, 'a cartoon wooden club bonk on something soft and furry, a squishy wet thud', .5, False),
    'whoosh': (1, 'a quick swoosh of a small wooden club swinging through cold air', .5, False),
    'splash': (2, 'a small seal slipping into icy water with a gentle splash', 1.0, False),
    'plop': (1, 'a soft thump of a small animal landing on packed snow', .5, False),
    'hop': (1, 'a cartoon boing as a small round creature hops out of the water', .5, False),
    'arf': (2, 'a cute baby seal barks softly, arf arf', .8, False),
    'squawk': (1, 'a seagull squawks twice', .9, False),
    'bark': (1, 'a happy husky puppy yips twice', .7, False),
    'ding': (1, 'a soft cozy chime, a gentle bell twinkle for collecting an item in a cute game', .8, False),
    'buy': (1, 'a cheerful jingle of sleigh bells and a wooden shop bell, an upgrade bought in a cozy game', 1.2, False),
    'golden': (1, 'a magical sparkling glissando of tiny bells, a rare treasure appears', 1.6, False),
    'fish': (1, 'a fish tossed into the sea plops into the water with a splash', .8, False),
    'shore': (1, 'calm arctic shore ambience: gentle waves lapping against ice floes, soft wind, faint distant seagulls, peaceful', 22, True),
    'nightair': (1, 'quiet arctic night ambience: soft wind over snow and a small crackling campfire, very calm', 22, True),
    'drone': (1, 'a small quadcopter drone whirring and buzzing as it lifts off and flies past', 1.6, False),
    'winch': (1, 'a small electric winch whirs and reels in a metal cable, ending with a clunk', 1.0, False),
    'chipper': (2, 'a cartoon wood chipper grinding something soft and squishy, a wet crunchy grind that sputters to a stop', 1.6, False),
    'slurp': (2, 'a huge industrial vacuum hose slurping something heavy up out of water, a deep wet shloop and a hollow metal thunk', 1.2, False),
    'clank': (1, 'heavy factory machinery clanks once and lets out a short hiss of steam', .9, False),
    'mush': (1, 'sleigh bells jingle as a dog sled sets off across the snow and a husky yips excitedly', 1.6, False),
    'coins': (1, 'a satisfying old cash register ka-ching followed by a handful of coins clinking', 1.0, False),
    'hum': (1, 'a steady low industrial factory hum with a slow rhythmic pump thumping, muffled and mechanical', 12, True),
    # the sealocalypse
    'sting': (1, 'a huge dramatic horror orchestra sting with a deep boom and a shrieking choir, the end of the world', 3.0, False),
    'horn': (1, 'a deep ominous war horn blast announcing an attack', 1.8, False),
    'hurt': (2, 'a short pained cartoon grunt of a young woman getting hit', .6, False),
    'croak': (2, 'a wet gurgling monstrous frog croak', .8, False),
    'tongue': (1, 'a fast wet sticky tongue lash, a slurping thwip', .5, False),
    'retch': (2, 'a cartoon monster retching and vomiting a wet splash', .9, False),
    'splat': (3, 'a wet squishy slime splat hit', .5, False),
    'pop': (1, 'a big wet balloon of slime bursting with a squelchy explosion', 1.0, False),
    'hiss': (1, 'a swelling hiss of gas building pressure before a pop', .7, False),
    'gurgle': (1, 'a bubbling gurgle of a monster surfacing from water with a splash', 1.0, False),
    'roar': (2, 'a huge monstrous seal roar, deep and bellowing with a wet gurgle', 1.6, False),
    'harpoon': (2, 'a harpoon gun firing, a pneumatic thunk and a whizzing barbed spear', .6, False),
    'flame': (1, 'a short roaring whoosh of a flamethrower burst', 1.0, False),
    'gun': (2, 'a quick small machine gun burst of three shots, tinny', .5, False),
    'dead': (1, 'a sad slide whistle down and a cartoon thud, game over', 1.6, False),
    'win': (1, 'a triumphant heroic orchestral fanfare with timpani and cymbals, victory', 3.5, False),
    'goo': (2, 'a wet squelchy pop of picking up a blob of slime, short and gooey', .5, False),
    'boom': (1, 'a big cartoon explosion with a deep boom and metal debris clattering down', 2.0, False),
}
LOOPS = {n for n, (_, _, _, loop) in SFX.items() if loop}
# name: (voice, [lines]); words in [brackets] direct the voice and are not spoken
LINES = {
    'ko': (HUNTER, ['[cheerful] Gotcha!', '[giggles] Bonk!', '[happy] Nice and fluffy!', "[pleased] Ooh, that's a good pelt.",
                    '[excited] Into the sled you go!']),
    'sneak': (HUNTER, ["[whispers] Nap time's over."]),
    'goldko': (HUNTER, ["[gasps] It's golden!"]),
    'escape': (HUNTER, ['[groans] Aw, come back!', '[sighs] Slippery little thing.']),
    'shoo': (HUNTER, ['[shouting] Hey! Shoo, shoo!', '[annoyed] Drop it, you feathery thief!']),
    'bought': (HUNTER, ['[happy] Ooh, cozy!', '[excited] Upgrade time!']),
    'fishy': (HUNTER, ['[sing-song] Here, fishy fishy!']),
    'roll': (HUNTER, ["[excited] I'm on a roll!"]),
    'welcome': (NARRATOR, ['[warmly] Welcome to Cozy Pelts, a wholesome family business. The seals are coming up to lounge on the ice.']),
    'goldseal': (NARRATOR, ["[hushed, excited] A golden seal. Don't let it slip away."]),
    'rush': (NARRATOR, ['[cheerful] Seal rush!']),
    'gull': (NARRATOR, ["[alarmed] Mind the gull. It's after your sled."]),
    'stolen': (NARRATOR, ['[sighs] The gull got away with some of your pelts.']),
    'dusk': (NARRATOR, ['[softly] Night falls over the ice. Sleepy seals make for sneaky bonks.']),
    'dawn': (NARRATOR, ['[warmly] A new day on the ice.']),
    'husky': (NARRATOR, ['[warmly] Another husky joins the team. Good dog. Asks no questions.']),
    'drone': (NARRATOR, ['[cheerfully] A drone, and a wood chipper. Seal goes in, pelt comes out. Best not to ask about the middle bit.']),
    'drone2': (NARRATOR, ['[dryly] Another drone. The seals have started looking up.']),
    'factory': (NARRATOR, ['[grandly] The contraption is running. It drinks the sea, and the sea is mostly seals.']),
    'apoc': (NARRATOR, ['[booming, dramatic] You have started... the Sealocalypse.']),
    'cleared': (NARRATOR, ['[relieved] Wave cleared.', '[dryly] That was the easy one.', '[relieved] Wave cleared. Catch your breath.', '[sarcastically] Well done. They will be back.']),
    'mama': (NARRATOR, ['[alarmed] Here comes Big Mama.']),
    'thulu': (NARRATOR, ['[terrified whisper] Sealthulu has risen. Good luck.']),
    'won': (NARRATOR, ['[awed] You won. The sea is quiet now. Too quiet.']),
    'eaten': (NARRATOR, ['[solemnly] You have been eaten. The seals send their regards.']),
    'ow': (HUNTER, ['[pained] Ow!', '[yelps] Ouch!', '[gasps] Oh no!']),
    # rare seals, one line for the first sighting of each
    'r_platinum': (NARRATOR, ['[impressed] A platinum seal. Very exclusive. Very bonkable.']),
    'r_emerald': (NARRATOR, ['[hushed] An emerald seal. Rare, green, and about to be very red.']),
    'r_sapphire': (NARRATOR, ['[awed] A sapphire seal. Blue blood, in every sense.']),
    'r_ruby': (NARRATOR, ["[delighted] A ruby seal. Red suits it. It'll suit it even more in a minute."]),
    'r_diamond': (NARRATOR, ["[whispering] A diamond seal. They say diamonds are forever. We'll see."]),
    'r_rainbow': (NARRATOR, ['[gasps] A rainbow seal! Every colour there is, and red in a minute.']),
    'r_cosmic': (NARRATOR, ['[reverently] A cosmic seal. It crossed the stars to be here. To be clubbed.']),
    'r_holy': (NARRATOR, ["[reverently] A holy seal. It has a halo. The halo won't help."]),
    'decoyup': (NARRATOR, ['[smugly] Word gets around. Fancier seals are coming.']),
    'rareko': (HUNTER, ['[ecstatic] Jackpot!', '[giggles] Shiny!', '[gasps] So pretty. Anyway, bonk.']),
    # the sealocalypse
    'whathave': (HUNTER, ['[horrified] Oh no. What have I done?']),
    'apoc2': (NARRATOR, ["[grimly] The sea is soup now, and the seals aren't seals anymore. They remember you."]),
    'wave': (NARRATOR, ['[ominously] Here they come.', '[dryly] More of them. Of course.', '[tense] Something is crawling out of the water. Lots of somethings.', "[resigned] Another wave. They don't get tired."]),
    'm_frog': (NARRATOR, ['[disgusted] Three eyes, frog legs, and a very long tongue. Lovely.']),
    'm_bat': (NARRATOR, ["[alarmed] They fly now. And they're going to be sick on you."]),
    'm_bloat': (NARRATOR, ["[worried] Don't let that one get close. It's ripe."]),
    'm_kraken': (NARRATOR, ['[nervous] Something in the water has far too many arms.']),
    'lowhp': (NARRATOR, ["[urgently] One more hit and you're seal food."]),
    'mamadown': (NARRATOR, ['[impressed] Big Mama is down. Somebody tell the babies.']),
    'thulu2': (NARRATOR, ["[terrified] Now he's angry."]),
    'thulu3': (NARRATOR, ["[panicking] He's throwing everything he has. Dodge!"]),
    'kill': (HUNTER, ['[grimly] Not so cozy now.', '[battle cry] Come and get it!', '[panting] Got one!', '[cackling] Toasty!']),
    'buyharpoon': (HUNTER, ['[excited] Harpoon time!']),
    'buyflamer': (HUNTER, ['[maniacal giggle] Who wants a barbecue?']),
    'buydrone': (HUNTER, ['[cheerful] Get them, little buddy!']),
    'buyheart': (HUNTER, ["[relieved] Ooh, that's better."]),
    'buyparka': (HUNTER, ['[smugly] Bits of factory. Very fashionable.']),
    'buyaid': (HUNTER, ['[wincing] Ow. Duct tape. Ow.']),
    'hup': (HUNTER, ['[effort] Hup!', '[effort] Hyah!']),
    'tier2': (NARRATOR, ["[uneasy] Twice the slurp. The sea has gone a funny colour. That's probably fine."]),
    'sold': (NARRATOR, ['[warmly] The trader paid up. He never asks where they come from.', '[pleased] Sold. Cozy money.']),
    'full': (NARRATOR, ['[politely] The sled is full. The dogs are waiting.']),
    'mush': (HUNTER, ['[shouting cheerfully] Mush! Mush!', '[sing-song] Off to market!']),
    'byebye': (HUNTER, ['[sweetly] Bye bye, little guy!', '[giggles] Up you go!']),
    'messy': (HUNTER, ['[wincing] Ooh. Messy.']),
}
MUSIC = {
    'day': (90, 'Cozy winter lo-fi for a cute pixel art game: music box melody, soft felt piano, gentle plucked acoustic '
                'guitar, light sleigh bells and brushed percussion, warm and peaceful, slow tempo around 80 bpm, instrumental'),
    'night': (75, 'Sleepy winter lullaby for a cute pixel art game at night: celesta and soft piano over warm pads, '
                  'very calm and gentle, slow, instrumental'),
}


def key():
    k = os.environ.get('ELEVENLABS_API_KEY')
    for p in (ROOT / '.secrets' / 'elevenlabs-api-key.txt', ROOT.parent / 'shoulda-listened' / '.secrets' / 'elevenlabs-api-key.txt'):
        if not k and p.exists():
            k = p.read_text().strip()
    if not k:
        sys.exit('No ElevenLabs key')
    return k


def post(path, body, tag, rate):
    """Raw 16-bit PCM at this rate for this request, from the cache when it was made before."""
    h = hashlib.sha1(json.dumps([path, body], sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f'{tag}-{h}.pcm'
    if f.exists():
        return f.read_bytes()
    sep = '&' if '?' in path else '?'
    req = urllib.request.Request(f'{API}{path}{sep}output_format=pcm_{rate}', data=json.dumps(body).encode(),
                                 headers={'xi-api-key': key(), 'Content-Type': 'application/json', 'User-Agent': 'cozy-pelts'})
    for attempt in range(4):
        try:
            data = urllib.request.urlopen(req, timeout=300).read()
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:400]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(8 * (attempt + 1))
                continue
            raise SystemExit(f'ElevenLabs {e.code} on {tag}: {msg}')
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    with open(CACHE.parent / 'calls.jsonl', 'a', encoding='utf-8') as log:
        log.write(json.dumps({'t': time.strftime('%Y-%m-%d %H:%M:%S'), 'tag': tag, 'path': path,
                              'text': body.get('text') or body.get('prompt'), 'bytes': len(data)}) + '\n')
    return data


def jobs():
    out = []
    for name, (takes, prompt, secs, loop) in SFX.items():
        for i in range(takes):
            body = {'text': prompt, 'duration_seconds': secs, 'prompt_influence': .55, 'model_id': 'eleven_text_to_sound_v2'}
            if loop:
                body['loop'] = True
            if takes > 1:
                body['seed'] = 1000 + i
            out.append(('sfx', f'{name}_{i + 1}' if takes > 1 else name, '/sound-generation', body))
    for name, (voice, lines) in LINES.items():
        for i, text in enumerate(lines):
            body = {'text': text, 'model_id': 'eleven_v3', 'voice_settings': {'stability': .5, 'similarity_boost': .8}}
            out.append(('voice', f'{name}_{i + 1}' if len(lines) > 1 else name, f'/text-to-speech/{VOICES[voice]}', body))
    for name, (secs, prompt) in (MUSIC.items() if '--music' in sys.argv else ()):   # the key needs music_generation
        out.append(('music', name, '/music', {'prompt': prompt, 'music_length_ms': secs * 1000, 'model_id': 'music_v1',
                                              'force_instrumental': True}))
    return out


def finish(kind, name, pcm):
    import numpy as np, lameenc
    RATE = RATES[kind]
    x = np.frombuffer(pcm, '<i2').astype(np.float64) / 32768
    if kind in STEREO:
        x = x[:len(x) // 2 * 2].reshape(-1, 2).mean(axis=1)
    if kind != 'music' and name not in LOOPS:
        loud = np.flatnonzero(np.abs(x) > .015)
        if len(loud):
            x = x[max(0, loud[0] - int(RATE * .01)):loud[-1] + int(RATE * .06)]
    x = x / (np.max(np.abs(x)) or 1) * (.9 if kind == 'voice' else .85)
    fade = int(RATE * (.6 if kind == 'music' else .25 if name in LOOPS else .004))
    if len(x) > 2 * fade and fade:
        x[:fade] *= np.linspace(0, 1, fade)
        x[-fade:] *= np.linspace(1, 0, fade)
    e = lameenc.Encoder()
    e.set_bit_rate({'music': 56, 'voice': 40}.get(kind, 48)); e.set_in_sample_rate(RATE); e.set_channels(1); e.set_quality(2)
    data = bytes(e.encode((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes()) + e.flush())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{name}.mp3').write_bytes(data)
    return len(x) / RATE, len(data)


def main():
    todo = jobs()
    if '--list' in sys.argv:
        for kind, name, path, body in todo:
            print(kind, name, (body.get('text') or body.get('prompt'))[:70])
        print(len(todo), 'items')
        return
    manifest = {}

    def run(job):
        kind, name, path, body = job
        secs, size = finish(kind, name, post(path, body, name, RATES[kind]))
        return kind, name, secs, size

    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for kind, name, secs, size in pool.map(run, todo):
            manifest[name] = {'kind': kind, 'secs': round(secs, 2)}
            print(f'{kind:5} {name:12} {secs:5.1f} s {size // 1024:4d} KB')
    (ROOT / 'game' / 'audio.json').write_text(json.dumps(manifest, indent=1))
    print('total', sum((OUT / f'{n}.mp3').stat().st_size for n in manifest) // 1024, 'KB')


if __name__ == '__main__':
    main()
