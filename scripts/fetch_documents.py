#!/usr/bin/env python3
import requests
import pathlib
import sys

def main():
    urls = [
        'https://www.example.com',
        'https://www.wikipedia.org',
        'https://www.iana.org/domains/reserved',
    ]
    out_dir = pathlib.Path('rag_corpus')
    out_dir.mkdir(parents=True, exist_ok=True)
    fetched = 0
    for idx, url in enumerate(urls, start=1):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            filename = out_dir / f'doc_{idx}.html'
            with open(filename, 'wb') as f:
                f.write(resp.content)
            fetched += 1
            print(f'Fetched {url} -> {filename}')
        except Exception as e:
            print(f'Failed to fetch {url}: {e}', file=sys.stderr)
    print(f'Fetched {fetched} documents.')

if __name__ == '__main__':
    main()