#!/usr/bin/env python3
"""Build the one-file version of the web port: web/arcade-volleyball.html.

Everything (sprites, code, styles, icons) goes inside a single HTML file, so
it can be downloaded once and played offline by opening it - no server, no
install, nothing else to copy.

Usage: mkstandalone.py web/
"""
import base64
import re
import sys


def data_uri(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def main():
    web = sys.argv[1].rstrip('/\\')
    html = open(f'{web}/index.html', encoding='utf-8').read()
    sprites = open(f'{web}/sprites.js', encoding='utf-8').read()
    game = open(f'{web}/game.js', encoding='utf-8').read()
    icon = data_uri(f'{web}/icon-192.png', 'image/png')

    # the single file has no service worker and no manifest to fetch
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', '')
    html = html.replace('href="icon-192.png"', f'href="{icon}"')
    html = re.sub(r'\n\s*// cache everything on the first visit.*?\n\s*}\n', '\n', html, flags=re.S)
    html = html.replace('<script src="sprites.js"></script>\n<script src="game.js"></script>',
                        f'<script>\n{sprites}\n</script>\n<script>\n{game}\n</script>')
    # there is nothing to install from a local file, but the button has to
    # stay in the page: the script below it looks the element up
    html = html.replace('<button id="install" hidden>Install</button>',
                        '<button id="install" hidden disabled>Install</button>')

    # no external file may be left (game.js mentions sprites.js in a comment)
    assert '<script src=' not in html, 'script inlining failed'
    assert 'manifest' not in html.split('<body')[0], 'manifest link still in the head'
    out = f'{web}/arcade-volleyball.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'{out}: {len(html.encode("utf-8")) / 1024:.0f} KB, self-contained')


if __name__ == '__main__':
    main()
