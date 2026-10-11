"""Download the attributed UCI source archive and verify its recorded hash."""
import hashlib
import json
from pathlib import Path
import urllib.request
from zipfile import ZipFile
from .core import ROOT

URL = 'https://archive.ics.uci.edu/static/public/942/rt-iot2022.zip'

def main():
    folder = ROOT / 'data/raw'
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / 'rt-iot2022.zip'
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=120) as response:
            content = response.read()
        archive.write_bytes(content)
    expected_file = ROOT / 'reports/source.json'
    if expected_file.exists():
        expected = json.loads(expected_file.read_text())['archive_sha256']
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise ValueError('Source archive has changed. Review provenance before retraining.')
    with ZipFile(archive) as z:
        with z.open('RT_IOT2022') as source:
            (folder / 'RT_IOT2022').write_bytes(source.read())
    print('Ready:', folder / 'RT_IOT2022')

if __name__ == '__main__':
    main()
