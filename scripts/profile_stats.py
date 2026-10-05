"""Render public GitHub repository statistics as a self-contained SVG."""
import json
import os
from pathlib import Path
from html import escape
from urllib.request import Request, urlopen
from datetime import datetime, timezone

def fetch(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'arunod-profile-art'}
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        return json.load(response)

def render(repos, output):
    owned = [r for r in repos if not r.get('fork')]
    ranked = sorted(owned, key=lambda r: (-r['stargazers_count'], r['name'].lower()))[:4]
    stars = sum(r['stargazers_count'] for r in owned)
    forks = sum(r['forks_count'] for r in owned)
    langs = len({r['language'] for r in owned if r.get('language')})
    def t(x, y, value, size=16, color='#c3d0ed', weight=400):
        return f'<text x="{x}" y="{y}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(str(value))}</text>'
    s = '''<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="432" viewBox="0 0 1120 432" role="img" aria-label="Public repository statistics"><defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#172443"/><stop offset="1" stop-color="#101629"/></linearGradient><linearGradient id="bar"><stop stop-color="#69e5e1"/><stop offset="1" stop-color="#ba8aef"/></linearGradient></defs><rect x="1" y="1" width="1118" height="430" rx="23" fill="url(#bg)" stroke="#374767"/>'''
    s += t(38, 43, '05 / PUBLIC GITHUB SNAPSHOT', 12, '#80e6e3', 600)
    s += t(38, 88, 'The work, at a glance.', 28, '#edf1ff', 700)
    for i, (number, label) in enumerate([(len(repos), 'PUBLIC REPOS'), (stars, 'STARS · OWN REPOS'), (forks, 'FORKS · OWN REPOS'), (langs, 'PRIMARY LANGUAGES')]):
        x = 38 + i * 269
        s += f'<rect x="{x}" y="112" width="250" height="97" rx="13" fill="#14243f" stroke="#304565"/>'
        s += t(x+18, 155, number, 32, '#eeeaff', 700) + t(x+18, 185, label, 11, '#9bafd3', 600)
    s += t(38, 246, 'TOP ORIGINAL REPOSITORIES BY STARS', 11, '#9bafd3', 600)
    largest = max([r['stargazers_count'] for r in ranked] or [1]) or 1
    for i, r in enumerate(ranked):
        y = 276 + i*29
        name = r['name']
        if len(name) > 41:
            name = name[:38] + '…'
        s += t(38, y, name, 14)
        s += f'<rect x="450" y="{y-12}" width="532" height="12" rx="6" fill="#25324c"/>'
        width = 532 * r['stargazers_count'] / largest
        if width:
            s += f'<rect x="450" y="{y-12}" width="{width:.2f}" height="12" rx="6" fill="url(#bar)"/>'
        s += t(1005, y, r['stargazers_count'], 14, '#d8c6fa')
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    s += t(38, 407, 'Public data only • Forked repositories excluded from stars, forks and language totals.', 11, '#8fa4c7')
    s += t(855, 407, date, 11, '#8fa4c7') + '</svg>'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(s, encoding='utf-8')

if __name__ == '__main__':
    user = os.environ.get('PROFILE_USER', 'arunodmanoharaofficial')
    repos = []
    for page in range(1, 101):
        batch = fetch(f'https://api.github.com/users/{user}/repos?type=owner&per_page=100&page={page}')
        repos.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError('Pagination exceeded safe limit; refusing incomplete stats')
    render(repos, Path('dist/studio-stats.svg'))
    print(f'Rendered statistics from {len(repos)} public repositories')
