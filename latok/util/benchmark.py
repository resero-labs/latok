import csv
import gzip
import json
import sys
from datetime import datetime
from latok.util.progress_tracker import ProgressTracker


def emoji_tweetfile_generator(filepath, col=0):
    '''
    Given the path to the benchmarking emoji tweet csv file, yield each tweet
    text from the specified column; where column 0 has the emojis in tact and
    column 1 has the emojis removed.
    :param filepath: Path to the emoji csv file
    :param col: Column (0 or 1) to return
    '''
    if filepath.endswith('.gz'):
        infile = gzip.open(filepath, 'rt', encoding='utf-8')
    else:
        infile = open(filepath, 'r', encoding='utf-8')
    try:
        for row in csv.reader(infile):
            yield json.loads(row[col]).strip()
    finally:
        infile.close()


def benchmark(function, iterator, max_iters=300000, max_seconds=60,
              min_report_count=10000, item_type='item',
              out=sys.stdout):
    '''
    Apply the function to the text from the iterator, reporting progress along
    the way.
    :param function: Function to be timed as function(text) is called over the
        text returned from the iterator
    :param iterator: An iterator over text to be processed
    :param max_iters: The maximum number of iterations to process. No limit if 0
    :param min_report_count: The count at which to start reporting status
    :param item_type: Descriptor of each text to be used when reporting status
    :param out: Output stream for reporting status, or don't report if None.
    '''
    if out:
        progress_tracker = ProgressTracker(
            item_type=item_type, min_report_count=min_report_count-1,
            outfile=out)
    starttime = datetime.now()
    try:
        for count, text in enumerate(iterator):
            function(text)
            if (out):
                progress_tracker.inc(True)
            if ((max_iters > 0 and count >= max_iters) or
                (max_seconds > 0 and
                 (datetime.now() - starttime).total_seconds() > max_seconds)):
                break
    finally:
        deltatime = datetime.now() - starttime
        if (out):
            progress_tracker.report()
    return count, deltatime.total_seconds()
