"""Builds the single-file game: game/src.html with the atlas, its frame table, the background and the audio inlined.

  python tools/build.py [artifact_out.html]

Writes docs/index.html (the full page GitHub Pages serves) and, when given, the same page without
the <html>/<head>/<body> wrapper for publishing as a claude.ai artifact.
"""
import base64, json, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def data_url(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


def audio_json():
    """Every clip tools/audio.py made, as {name: base64 MP3}."""
    manifest = os.path.join(ROOT, "game", "audio.json")
    if not os.path.exists(manifest):
        return "{}"
    clips = {n: base64.b64encode(open(os.path.join(ROOT, "game", "audio", n + ".mp3"), "rb").read()).decode()
             for n in json.load(open(manifest))}
    return json.dumps(clips, separators=(",", ":"))


def main():
    src = open(os.path.join(ROOT, "game", "src.html"), encoding="utf-8").read()
    page = (src.replace("/*ATLAS_JSON*/{}", open(os.path.join(ROOT, "game", "atlas.json")).read())
               .replace("/*AUDIO_JSON*/{}", audio_json())
               .replace("__ATLAS_PNG__", data_url(os.path.join(ROOT, "game", "atlas.png")))
               .replace("__BG_PNG__", data_url(os.path.join(ROOT, "art", "ref", "bg_clean.png"))))
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    full = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '</head>\n<body>\n' + page + '\n</body>\n</html>\n')
    open(os.path.join(ROOT, "docs", "index.html"), "w", encoding="utf-8", newline="\n").write(full)
    if len(sys.argv) > 1:
        open(sys.argv[1], "w", encoding="utf-8", newline="\n").write(page)
    print("built docs/index.html, %d KB" % (len(full) // 1024))


if __name__ == "__main__":
    main()
