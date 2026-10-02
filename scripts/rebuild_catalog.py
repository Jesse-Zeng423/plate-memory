"""Explicit developer-only Wikidata refresh into a NEW directory.

Runtime does not import this script. Only public IDs are transmitted. Inspect
changed labels before shipping a new pack; hashes detect corruption, not truth.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.catalog.schema import validate_pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New directory; existing directories are refused.')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output directory; existing snapshots are never overwritten.')
    original = json.loads((ROOT/'data/catalog/v1/dishes.json').read_text(encoding='utf-8'))
    records = []
    for seed in original['items']:
        qid = seed['id']
        request = urllib.request.Request('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json', headers={'User-Agent':'PlateMemory/0.1 public offline catalog build'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError('Source response too large.')
        entity = json.loads(raw)['entities'][qid]
        name = entity['labels'].get('en',entity['labels'].get('mul'))['value']
        if name != seed['name']:
            raise ValueError('Source label changed; review '+qid+' before rebuilding.')
        records.append(dict(seed, names={k:v['value'] for k,v in entity['labels'].items() if k in ('en','mul','zh','zh-hans','zh-hant')}, aliases=sorted(set(v['value'] for k,vs in entity.get('aliases',{}).items() if k in ('en','zh','zh-hans','zh-hant') for v in vs)), source={'url':'https://www.wikidata.org/wiki/'+qid,'revision':entity['lastrevid']}))
    pack = validate_pack({'schema_version':1,'items':records})
    raw = (json.dumps(pack,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    manifest=json.loads((ROOT/'data/catalog/v1/manifest.json').read_text(encoding='utf-8'))
    manifest.update(count=len(records),sha256=hashlib.sha256(raw).hexdigest(),retrieved_at=datetime.now(timezone.utc).isoformat())
    args.output.mkdir(parents=True)
    (args.output/'dishes.json').write_bytes(raw)
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Prepared {len(records)} concepts in {args.output}; review before release.')


if __name__ == '__main__':
    main()
