#!/usr/bin/env python3
'''
Script to measure tokenization timing.

NOTE: currently, you'll need to manually ^C out of execution if you don't want to wait for the full input file to be processed!

usage:

# scripts/timing/time_tokenizer.py <path-to-file-with-strings-to-tokenize-one-string-per-line>
      [--mincount <count-at-which-to-start-showing-progress>]
      [--outfile <path-to-write-out-generated-tokens-one-string-per-line>]
'''
import argparse
import csv
import gzip
import json
import os
import sys
from datetime import datetime
from latok.core.default_tokenizer import gen_split_mask, tokenize, featurize
from latok.latok import _gen_parse_matrix
from latok.util.progress_tracker import ProgressTracker


def process_file(filepath, function, progress_tracker):
    '''
    Apply function to each tweet in the filepath.
    '''
    if filepath.endswith('.gz'):
        infile = gzip.open(filepath, 'rt', encoding='utf-8')
    else:
        infile = open(filepath, 'r', encoding='utf-8')
    try:
        for count, row in enumerate(csv.reader(infile)):
            text = json.loads(row[1]).strip()
            function(text)
            progress_tracker.inc(True)
    finally:
        infile.close()    
    return count


class LaTokenizeWrapper:
    def tokenize(self, text):
        return list(tokenize(text))


class LaSplitWrapper:
    def tokenize(self, text):
        gen_split_mask(_gen_parse_matrix(text))
        return None


class LaMatrixWrapper:
    def tokenize(self, text):
        _gen_parse_matrix(text)
        return None


class LaFeatureWrapper:
    def tokenize(self, text):
        return list(featurize(text))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='path to file with texts, one per line')
    parser.add_argument('--split', help='(optional) Set to only generate the split mask and not to generate tokens', action='store_true', default=False)
    parser.add_argument('--matrix', help='(optional) Set to only generate the parse matrix and not split into tokens', action='store_true', default=False)
    parser.add_argument('--features', help='(optional) Set to featurize the tokens', action='store_true', default=False)
    parser.add_argument('--mincount', help='(optional, default=100000) minimum count at which to begin displaying progress', type=int, default=100000)
    parser.add_argument('--outfile', help='(optional) file to which tokenizations will be emitted if present.')
    args = parser.parse_args()
    print(f'{datetime.now()}: {args}', file=sys.stderr)

    infile = args.infile
    split = args.split
    matrix = args.matrix
    features = args.features
    mincount = args.mincount
    outfile = args.outfile

    if args.outfile:
        split = matrix = False

    total_count = 0

    tokenizer = None
    if split:
        tokenizer = LaSplitWrapper()
    elif matrix:
        tokenizer = LaMatrixWrapper()
    elif features:
        tokenizer = LaFeatureWrapper()
    else:
        tokenizer = LaTokenizeWrapper()

    outfile = None
    if args.outfile:
        outfile = open(args.outfile, 'w', encoding='utf-8')

    def tokenize_line_no_output(line):
        global tokenizer
        tokenizer.tokenize(line)

    def tokenize_line_with_output(line):
        global tokenizer, outfile
        tokens = tokenizer.tokenize(line)
        print('\t'.join(tokens), file=outfile)

    tokenize_line = tokenize_line_with_output if outfile else tokenize_line_no_output

    tokenizer.tokenize("This is a test line, just to get things warmed up...")

    print(f'{datetime.now()}: Beginning tokenization...')
    progress_tracker = ProgressTracker(item_type="line", min_report_count=(mincount-1))
    try:
        total_count = process_file(infile, tokenize_line, progress_tracker)
        print(f'{datetime.now()}: ...tokenized {total_count} lines')
    finally:
        progress_tracker.report()
        if outfile:
            outfile.close()
