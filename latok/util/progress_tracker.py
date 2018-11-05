'''
Progress tracking for long running tasks
'''
from datetime import datetime
import math
import sys


def get_log_progress(count: int) -> bool:
    return count % (10 ** math.floor(math.log(count, 10))) == 0

class ProgressTracker:
    '''
    Utility for tracking progress of a long running processing task over
    many items.

    As items are tracked, progress will be reported in terms of the count
    and rate of processing on a log scale. Progresss on processing each of
    the first 10 will be reported, then each 10, each 100, etc.
    '''

    def __init__(self, item_type="item", item_type_plural=None, outfile=sys.stderr,
                 min_report_count=0):
        '''
        Initialize with the text to use (singular and plural) while reporting
        on progress for each item processed and with the stream to write the
        reporting to.
        '''
        self._item_type = item_type
        self._item_type_plural = item_type_plural if item_type_plural is not None else item_type + 's'
        self._outfile = outfile
        self._count = 0
        self._min_report_count = min_report_count
        self._starttime = datetime.now()

    def inc(self, show_elapsed=False):
        ''' Mark another item being processed and auto-report on a log scale '''
        self._count += 1
        if get_log_progress(self._count):
            self.report(show_elapsed=show_elapsed)

    def report(self, show_elapsed=True):
        ''' Report on the current progress '''
        if self._count > self._min_report_count:
            curtime = datetime.now()
            deltatime = (curtime - self._starttime)
            dsecs = deltatime.total_seconds()
            elapsed_string = ' in {}'.format(deltatime) if show_elapsed else ''
            if self._count > dsecs and dsecs > 0:
                rate = self._count / dsecs
                print('{}: processed {} {} @ {:.4f}/sec{}'.format(
                    str(curtime), self._count, self._item_type_plural,
                    rate, elapsed_string),
                      file=self._outfile)
            elif self._count > 0:
                rate = deltatime / self._count
                print('{}: processed {} {} @ {}/{}{}'.format(
                    str(curtime), self._count, self._item_type_plural,
                    str(rate), self._item_type, elapsed_string),
                      file=self._outfile)
            self._outfile.flush()
