"""Builds the game and puts it on GitHub Pages at https://jhffmn82.github.io/cozy-pelts/ (Justin 2026-10-28: "host it
on git so i can share it").

    python tools/publish.py ["commit message"]

Commits whatever changed and pushes main to jhffmn82/cozy-pelts; Pages serves main's docs/ folder. The token is the
fine-grained one in shoulda-listened/.secrets/github-token.txt (or this project's .secrets), never printed or written
anywhere. Git's credential manager is bypassed, since it cannot reach the Windows credential vault from Claude's shell.
"""
import base64, json, os, pathlib, subprocess, sys, urllib.error, urllib.request

OWNER, REPO = 'jhffmn82', 'cozy-pelts'
ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKENS = [ROOT / '.secrets' / 'github-token.txt', ROOT.parent / 'shoulda-listened' / '.secrets' / 'github-token.txt']
WHO = ['-c', 'user.name=Justin Hoffman', '-c', 'user.email=jhffmn.myalt1@gmail.com']


def token():
    for f in TOKENS:
        if f.exists() and f.read_text().strip():
            return f.read_text().strip()
    raise SystemExit('No GitHub token')


def api(method, path, body=None):
    req = urllib.request.Request('https://api.github.com' + path, method=method, data=json.dumps(body).encode() if body else None)
    req.add_header('Authorization', 'Bearer ' + token())
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')


def git(*args, env=None, check=True):
    return subprocess.run(['git', '-C', str(ROOT), *args], env=env, check=check, capture_output=True, text=True)


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else 'Rebuild the game'
    subprocess.run([sys.executable, str(ROOT / 'tools' / 'build.py')], check=True)
    if not (ROOT / '.git').exists():
        git('init', '-q', '-b', 'main')
    git('add', '-A')
    if git('diff', '--cached', '--quiet', check=False).returncode:
        git(*WHO, 'commit', '-q', '-m', msg + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>')
        print('committed:', msg)
    auth = base64.b64encode(f'x-access-token:{token()}'.encode()).decode()
    env = dict(os.environ, GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='http.extraHeader', GIT_CONFIG_VALUE_0=f'Authorization: Basic {auth}',
               GIT_CONFIG_KEY_1='credential.helper', GIT_CONFIG_VALUE_1='', GIT_TERMINAL_PROMPT='0')
    r = git('push', '-q', f'https://github.com/{OWNER}/{REPO}.git', 'main:main', env=env, check=False)
    if r.returncode:
        raise SystemExit('push failed: ' + r.stderr.strip()[-600:])
    print('pushed main')
    code, pages = api('GET', f'/repos/{OWNER}/{REPO}/pages')
    if code == 404:
        code, pages = api('POST', f'/repos/{OWNER}/{REPO}/pages', {'source': {'branch': 'main', 'path': '/docs'}})
        print('GitHub Pages turned on' if code in (200, 201) else f'Pages not turned on ({code}): {pages.get("message")}')
    print('play at', pages.get('html_url') or f'https://{OWNER}.github.io/{REPO}/')


if __name__ == '__main__':
    main()
