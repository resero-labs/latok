'''
An exemplar and default LaTok (Linear Algebraic Tokenizer) implementation.

Algorithm and Usage:

* Step 1: Generate a feature matrix for parsing the string
   * A text string is represented as a feature matrix with 1-hot features
     for each character for each feature in offsets.py.
      * Configuration:
         * Make sure all desired features are present, adding to c-extension if needed.

* Step 2: Define the split mask based on (combinations of) features
   * Features in the matrix are linearly combined to generate a masking
     vector whose non-zero entries indicate positions at which to split
     the string.
      * Configuration:
         * Implement "gen_split_mask" to generate the split mask vector
         * Do preprocessing setup and configuration beforehand, such as:
            * Setting up combination masks for "and"-ing and "or"-ing features
            * etc.

* Step 3a: Tokenize the string as a list of strings
   * Call "tokenize"
      * Configuration:
         * Nothing more. Make sure "gen_split_mask" is properly defined.

* Step 3b: Tokenize the string as a list of LaToken instances
   * Call "featurize"
      * Configuration:
         * Nothing more. Make sure "gen_split_mask" is properly defined.
'''

import latok.core.offsets as oft
import numpy as np
from latok.core.latok_utils import gen_block_mask, build_combo_matrix, LaToken, OffsetSpec, FeatureSpec
from latok.latok import _gen_parse_matrix, _combine_matrix_rows


#
# Define offset combinations for tokens
#
TWITTER_OFFSETS1 = [oft.TWITTER_IDX, oft.PREV_SPACE_IDX, oft.NEXT_ALPHA_IDX]
TWITTER_OFFSETS2 = [oft.CHAR_PERIOD_IDX, oft.PREV_SPACE_IDX, oft.NEXT_AT_IDX, oft.AFTER_NEXT_ALPHA_IDX]
EMAIL_OFFSETS = [oft.CHAR_AT_IDX, oft.PREV_ALPHA_NUM_IDX, oft.NEXT_ALPHA_NUM_IDX]
URL_OFFSETS = [oft.CHAR_COLON_IDX, oft.NEXT_SLASH_IDX, oft.AFTER_NEXT_SLASH_IDX, oft.PREV_ALPHA_IDX]
CAMEL_CASE_OFFSETS1 = [oft.UPPER_IDX, oft.NEXT_LOWER_IDX]
CAMEL_CASE_OFFSETS2 = [oft.UPPER_IDX, oft.PREV_LOWER_IDX]


#
# Define abstracted token features
#
TWITTER_FEATURE = FeatureSpec('twitter',
                              [OffsetSpec(present=TWITTER_OFFSETS1),
                               OffsetSpec(present=TWITTER_OFFSETS2)],
                              None, None, None)
EMAIL_FEATURE = FeatureSpec('email',
                            [OffsetSpec(present=EMAIL_OFFSETS)],
                            None, None, None)
URL_FEATURE = FeatureSpec('url',
                          [OffsetSpec(present=URL_OFFSETS)],
                          None, None, None)
CAMEL_CASE_FEATURE = FeatureSpec('camelcase',
                                 [OffsetSpec(present=CAMEL_CASE_OFFSETS2)],
                                 None, None, None)


def build_split_combo_matrix():
    '''
    Define a combo matrix that will split on:
    * Whitespace  OR
    * Symbol OR
    * Prev-Symbol (effectively, each symbol becomes its own token) OR
    * CamelCase:
       * at an Upper-case letter followed by a Lower-case letter OR
       * at an Upper-case letter preceded by a Lower-case letter
    '''
    return build_combo_matrix([
        [oft.SPACE_IDX],
        [oft.SYMBOL_IDX],
        [oft.PREV_SYMBOL_IDX],
        CAMEL_CASE_OFFSETS1,
        CAMEL_CASE_OFFSETS2,
    ])


def build_mask_combo_matrix():
    '''
    Define a combo matrix that will split on:
    * Twitter specials:
       * simple prefixed:
         * at the twitter start symbol (e.g., @, #, $, or ^)
         * following a space and
         * preceding an alphabetic letter
       * dot prefixed:
         * at the period
         * following a space and
         * preceding an atset
         * followed by an alphabetic letter
    * Email addresses:
       * an atset character
       * preceded by an alphabetic letter and
       * followed by an alphabetic letter
    * URL address:
       * a colon character
       * following an alphabetic letter and
       * followed by two forward slashes
    '''
    return build_combo_matrix([
        # Twitter specials
        TWITTER_OFFSETS1,
        # twitter .@
        TWITTER_OFFSETS2,

        # email
        EMAIL_OFFSETS,

        # url
        URL_OFFSETS,
    ])
    

def build_symbol_combo_matrix():
    '''
    Define a combo matrix that will split on:
    * A symbol followed by whitespace
       * e.g., a symbol at the end of a token
    '''
    return build_combo_matrix([
        [oft.SYMBOL_IDX, oft.NEXT_SPACE_IDX],
    ])


#
# Pre-build combination matrix templates to use in gen_split_mask.
#
C_SPLIT = build_split_combo_matrix()
C_MASK = build_mask_combo_matrix()
C_SYM = build_symbol_combo_matrix()


def gen_split_mask(m: np.ndarray):
    '''
    Given a feature matrix from gen_parse_matrix, generate the split mask
    array that identifies character positions at which to split by having
    non-zero entries.
    '''
    m = m.T  # Transpose to view features as rows instead of columns

    splits = (
        # split on whitespace and symbols
        _combine_matrix_rows(m, C_SPLIT) *

        # block out urls, emails, twitter specials
        gen_block_mask(_combine_matrix_rows(m, C_MASK), m[oft.SPACE_IDX]))

    # split on terminating symbols after applying masks
    splits += _combine_matrix_rows(m, C_SYM)

    # start of string is always a boundary
    splits[0] = 1

    return splits


def tokenize(text: str, gen_split_mask_fn=gen_split_mask):
    '''
    Tokenize text using the given split mask generation function, yielding
    each token.

    :param text: The input text to tokenize
    :param gen_split_mask_fn: A function that takes a parse feature matrix
                              and returns a split mask vector.
    '''
    m = _gen_parse_matrix(text)
    splits = gen_split_mask_fn(m)
    non_zero = np.nonzero(splits)[0]
    if len(non_zero) > 0:
        str_idx, end_idx = non_zero[0], 0
        for end_idx in non_zero[1:]:
            token = text[str_idx:end_idx].strip()
            if token:
                yield token
            str_idx = end_idx
        last_token = text[end_idx:].strip()
        if last_token:
            yield last_token
    else:
        yield ''


def featurize(text: str, gen_split_mask_fn=gen_split_mask):
    '''
    Tokenize text using the given split mask generation function, yielding
    each token tagged with its features.

    :param text: The input text to tokenize
    :param gen_split_mask_fn: A function that takes a parse feature matrix
                              and returns a split mask vector.
    '''
    m = _gen_parse_matrix(text)
    splits = gen_split_mask_fn(m)
    non_zero = np.nonzero(splits)[0]
    textlen = len(text)
    if len(non_zero) > 0:
        str_idx, end_idx = non_zero[0], 0
        for end_idx in non_zero[1:]:
            token = text[str_idx:end_idx].strip()
            if token:
                yield LaToken(
                    token, str_idx, end_idx,
                    _combine_matrix_rows(m, np.arange(str_idx, end_idx, dtype=np.int8)),
                    m, None
                )
            str_idx = end_idx
        last_token = text[end_idx:].strip()
        if last_token:
            yield LaToken(
                last_token, end_idx, textlen,
                _combine_matrix_rows(m, np.arange(end_idx, textlen, dtype=np.int8)),
                m, None
            )


def add_abstract_features(la_tokens, feature_specs):
    for la_token in la_tokens:
        for feature_spec in feature_specs:
            if feature_spec.matches(la_token):
                la_token.add_abstract_feature(feature_spec.name)


if __name__ == "__main__":
    text = "This is a #test! Testing, Testing, 1 2 3"
    #text = "can’t wait to get my glasses back 🤓"
    #text = """IKR!! IM LIKE \""WHERE'S MY DADDY AT? 👀) https://t.co/jM3qLZijMc"""
    #text = '$#@^:a./'
    print(f'text={text}')
    m = _gen_parse_matrix(text)
    print(m)
    splits = gen_split_mask(m)
    print(f'splits={splits}')
    non_zero = np.nonzero(splits)[0]
    print(f'non_zero={non_zero}')
    for token in tokenize(text):
        print(f'"{token}"')
    for token in featurize(text):
        print(f'\n"{token.text}" ({token.start_idx}, {token.end_idx}) weight={token.weight()}\n{token.feature_weights()}')
