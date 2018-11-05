'''
Utilities for LaTok tokenization.
'''

import numpy as np
from dataclasses import dataclass
from latok.latok import _gen_parse_matrix, _gen_block_mask


def gen_parse_matrix(text: str) -> np.ndarray:
    '''
    Generate a feature matrix for parsing (tokenizing) a string,
    Where for each letter there is a row of features as identified in offsets.py.
    '''
    return _gen_parse_matrix(text)


def gen_block_mask(a1: np.ndarray, a2: np.ndarray) -> np.ndarray:
    '''
    Given two aligning arrays of 1's and 0's,
    generate a mask of ones with zeros between a2 1's where a1 has a 1,
    treating a2's endpoints as 1's.
    '''
    return _gen_block_mask(a1, a2)


def build_combo_matrix(idx_lists):
    '''
    Given a list of lists of indexes, generate a combo matrix,
    padded with -1's, where each row's values are feature indices
    (from offsets.py) to multiply, or effectively "and", and rows
    are added, or effectively "or'd".

    Examples:
    (1) to build a combo matrix for identifying a space OR
    a symbol, the input lists would be:

    [[oft.SPACE_IDX], [oft.SYMBOL_IDX]]

    (2) to build a combo matrix for identifying twitter
    specials where a twitter-special character follows a space
    AND precedes an alpha OR a period precedes an atset AND
    follows a space AND precedes an atset followed by an alpha,
    the input lists would be:

    [[oft.TWITTER_IDX, oft.PREV_SPACE_IDX, oft.NEXT_ALPHA_IDX],
     [oft.CHAR_PERIOD_IDX, oft.PREV_SPACE_IDX, oft.NEXT_AT_IDX,
      oft.AFTER_NEXT_ALPHA_IDX]]
    '''
    nrows = len(idx_lists)
    ncols = max(len(idx_list) for idx_list in idx_lists)
    m = np.ones((nrows, ncols), dtype=np.int8) * -1
    for i, idx_list in enumerate(idx_lists):
        for j, idx in enumerate(idx_list):
            m[i, j] = idx
    return m


# Names of features from offsets.py (in order)
FEATURE_NAMES = [
    'Alpha',
    'AlphaNum',
    'Num',
    'Lower',
    'Upper',
    'Space',
    'Symbol',
    'Twitter',
    '@',
    ':',
    '/',
    '.',
    'Prev_Alpha',
    'Next_Alpha',
    'Prev_AlphaNum',
    'Next_AlphaNum',
    'Prev_Lower',
    'Next_Lower',
    'Prev_Space',
    'Next_Space',
    'Prev_Symbol',
    'Next_@',
    'Next_/',
    'After_Next_Alpha',
    'After_Next_/',
]


NUM_FEATURES = len(FEATURE_NAMES)


@dataclass
class LaToken:
    '''
    Structure for a token including:
    * text: token text
    * start_idx: token starting index in its string
    * end_idx: token end index in its string
    * features: token feature vector
    '''
    text: str
    start_idx: int
    end_idx: int
    features: np.ndarray

    def weight(self, weighting=None):
        '''
        Get the weight of this token as the sum of its (optionally weighted) features.
        '''
        return np.sum((self.features * weighting) if weighting else self.features)

    def feature_weights(self):
        '''
        Get the non-zero feature names mapped to their weights.
        '''
        return {FEATURE_NAMES[idx]: self.features[idx] for idx in np.nonzero(self.features)[0]}
