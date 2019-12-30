'''
Utilities for LaTok tokenization.
'''

import numpy as np
import re
from dataclasses import dataclass
#pylint: disable=no-name-in-module
from latok.latok import _gen_parse_matrix, _gen_block_mask, _combine_matrix_rows


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

    NOTE: if idx_lists is just a list (not a list of lists),
          then it will be treated as [idx_lists].

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
    if not isinstance(idx_lists, list):
        idx_lists = [[idx_lists]]
    elif len(idx_lists) > 0 and not isinstance(idx_lists[0], list):
        idx_lists = [idx_lists]
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
    'Apos',
    'Hash',
    'Dollar',
    'Caret',
    'Emoji',
    'Emoji_Presentation',
    'Emoji_Modifier_Base',
    'Emoji_Component',
    'Extended_Pictographic',
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
    * m: parse matrix
    '''
    text: str
    start_idx: int
    end_idx: int
    features: np.ndarray
    m: np.ndarray
    abstract_features: list

    @property
    def size(self):
        return len(self.text)

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

    def add_abstract_feature(self, feature_name):
        if self.abstract_features is None:
            self.abstract_features = list()
        self.abstract_features.append(feature_name)


def _apply_combo_matrix(combo_matrix, mt):
    s = _combine_matrix_rows(mt, combo_matrix)
    nz = np.nonzero(s)
    return nz[0]
    #return np.nonzero(s)[0]


class OffsetSpec:
    '''
    Specification of offsets to be present and/or absent.
    * present: list of offsets where features are to be present
    * absent: list of offsets where features are to be absent
    * pcmat: present combo matrix ndarray
    * acmat: absent combo matrix ndarray
    '''
    def __init__(self, present=None, absent=None):
        self.present = present
        self.absent = absent
        self.pcmat = None
        self.acmat = None
        if present is not None and len(present) > 0:
            self.pcmat = build_combo_matrix(present)
        if absent is not None and len(absent) > 0:
            self.acmat = build_combo_matrix(absent)

    @property
    def has_present(self):
        return self.present is not None and len(self.present) > 0

    @property
    def has_absent(self):
        return self.absent is not None and len(self.absent) > 0

    def matches(self, mt, pa_align=False):
        result, p, a = False, None, None
        if self.has_present:
            p = _apply_combo_matrix(self.pcmat, mt)
            if len(p) == 0:
                return False
            else:
                result = True
        if self.has_absent:
            #import pdb; pdb.set_trace()
            a = _apply_combo_matrix(self.acmat, mt)
            if pa_align and p is not None:
                a *= p
            if len(a) > 0:
                return False
            else:
                result = True
        return result


@dataclass
class FeatureSpec:
    '''
    Structure for specifying an abstract feature to a range of characters.
    * name: feature name.
    * char_features: list of OffsetSpec instances, where this feature applies
                     if any OffsetSpec applies at any one char,
                     where an OffsetSpec applies at a character if all 'present'
                     offset features are present and all 'absent' offset
                     features are absent at the same character.
    * token_features: list of OffsetSpec instances where this feature applies
                      if any OffsetSpec applies to a range of characters,
                      where an OffsetSpec applies to a range of characters if
                      all 'present' offset features are present for any
                      character in the range and all 'absent' offset features
                      are absent for all of the characters in the range.
    * regexes: validating regexes for text in the range (succeed if any match).
    * not_regexes: invalidating regexes for text in the range (fail if any match).
    '''
    name: str
    char_features: list
    token_features: list
    regexes: list
    not_regexes: list

    def matches(self, la_token):
        result = False
        mt = la_token.m[la_token.start_idx:la_token.end_idx,].T
        if self.char_features is not None and len(self.char_features) > 0:
            for offset_spec in self.char_features:
                if offset_spec.matches(mt, pa_align=True):
                    result = True
                    break
            if not result:
                return False
        if self.token_features is not None and len(self.token_features) > 0:
            for offset_spec in self.token_features:
                if offset_spec.matches(mt, pa_align=False):
                    result = True
                    break
            if not result:
                return False
        if self.regexes is not None and len(self.regexes) > 0:
            for r in self.regexes:
                if re.match(r, la_token.text) is not None:
                    result = True
                    break
            if not result:
                return False
        if self.not_regexes is not None and len(self.not_regexes) > 0:
            for r in self.not_regexes:
                if re.match(r, la_token.text) is None:
                    result = True
                    break
            if not result:
                return False
        return result
