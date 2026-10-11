"""Batch inference: python predict.py input.csv --output predictions.csv."""
import argparse
from pathlib import Path
import pandas as pd
from src.core import load_bundle, predict
from app import read_csv

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path)
    p.add_argument('--output', type=Path, default=Path('predictions.csv'))
    p.add_argument('--threshold', type=float)
    args = p.parse_args()
    frame = read_csv(args.input.read_text(encoding='utf-8-sig'))
    output = pd.DataFrame(predict(frame, load_bundle(), args.threshold))
    output.to_csv(args.output, index=False)
    print(f'Scored {len(output)} flows. Saved {args.output}')

if __name__ == '__main__':
    main()
