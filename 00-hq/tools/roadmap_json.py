"""Turn 00-hq/ROADMAP.md into rows for the Kalpa CEO Room dashboard.

Usage: python3 00-hq/tools/roadmap_json.py OUT.json
Each row: id, queue (Agents | Akhil (CEO)), world, status (to do | in progress | done | blocked), title, done_on.
"""
import json, re, sys
from pathlib import Path

STATUS = {'x': 'done', '~': 'in progress', ' ': 'to do', '!': 'blocked'}
ITEM = re.compile(r'- \[(.)\] \*\*([AC]\d+[a-z]?)\*\* (\S+) · (.*)')

def parse(text):
    rows, queue = [], None
    for line in text.splitlines():
        if line.startswith('## Agent queue'):
            queue = 'Agents'
        elif line.startswith('## CEO queue'):
            queue = 'Akhil (CEO)'
        m = ITEM.match(line.strip())
        if not (m and queue):
            continue
        title = re.sub(r'`|\*\*', '', m.group(4))
        title = re.split(r'\. Check:|\(done |\(claimed', title)[0].strip()
        done = re.search(r'\(done (\d{4}-\d\d-\d\d)', line)
        rows.append({'id': m.group(2), 'queue': queue, 'world': m.group(3).split('/')[0],
                     'status': STATUS[m.group(1)], 'title': title[:140], 'done_on': done.group(1) if done else ''})
    return rows

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    rows = parse((root / '00-hq/ROADMAP.md').read_text(encoding='utf-8'))
    assert rows and all(r['id'] for r in rows), 'no roadmap rows parsed'
    Path(sys.argv[1]).write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    print(f'{len(rows)} rows -> {sys.argv[1]}')
