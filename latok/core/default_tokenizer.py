'''
An exemplar and default LaTok (Linear Algebraic Tokenizer) implementation.

The default tokenizer uses the following strategy for tokenizing:
  (1) Identify various split tokens based on combinations of character properties
  (2) Mask blocks of characters to remain together as tokens
  (3) Identify remaining split tokens (or exceptions to general blocks)

Tokenizer Configuration and Usage:

* Tokenization modes:
  * "tokenize" will yield token strings from the input string
    * Plain vanilla keeps all non-white text, including symbols
      * This is a fast mode without incurring any overhead for creating
        token instances or adding auxiliary information.
    * Adding conditions (like ignoring symbols) uses "featurize"
      * which has a small performance cost
* "featurize" will yield LaToken instances
  * including summed character-level feature information
  * "abstract featurization" will add token-level feature information
    to the LaToken token instances.
* "gen_split_mask" will generate the split mask from which tokens are derived
  * This is the fastest tokenization mode and may be suitable for some applications

* Configuration:
  * the split1/block/split2 property lists control splitting character positions
    * split1 finds initial locations for splitting and from which blocks
      of token characters can be masked to prevent further splitting
    * block masks out token characters to prevent further splitting (up to
      whitespace)
    * split2 enables splitting overreaching blocks (e.g., trailing symbols)
  * the abstract_feature_specs specify token-level features to be computed
    * and enable generic replacement for tokens having these features
      * For example: Tokens identified as a URL can be replaced with "_URL"
        when tokenized.

Underlying Tokenization Algorithm and Usage:

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

import latok.core.constants as C
import latok.core.offsets as oft
import numpy as np
from typing import Dict, Sequence
from latok.core.latok_utils import gen_block_mask, build_combo_matrix, LaToken, FeatureSpec
#pylint: disable=no-name-in-module
from latok.latok import _gen_parse_matrix, _combine_matrix_rows


# Define a combo matrix that will split on:
# * Whitespace  OR
# * Symbol OR
# * Prev-Symbol (effectively, each symbol becomes its own token) OR
# * CamelCase:
#    * at an Upper-case letter followed by a Lower-case letter OR
#    * at an Upper-case letter preceded by a Lower-case letter
DEFAULT_SPLIT_PROPS1 = [
    [oft.SPACE_IDX],
    [oft.SYMBOL_IDX],
    [oft.PREV_SYMBOL_IDX],
    C.CAMEL_CASE_OFFSETS1,
    C.CAMEL_CASE_OFFSETS2,
]

# Define a combo matrix that will split on:
# * Twitter specials:
#    * simple prefixed:
#      * at the twitter start symbol (e.g., @, #, $, or ^)
#      * following a space and
#      * preceding an alphabetic letter
#    * dot prefixed:
#      * at the period
#      * following a space and
#      * preceding an atset
#      * followed by an alphabetic letter
# * Email addresses:
#    * an atset character
#    * preceded by an alphabetic letter and
#    * followed by an alphabetic letter
# * URL address:
#    * a colon character
#    * following an alphabetic letter and
#    * followed by two forward slashes
# * Numeric tokens:
#    * any number char
# * Embedded apostrophe tokens
#    * an apostrophe character
#    * preceded by an alphabetic letter and
#    * followed by an alphabetic letter
DEFAULT_BLOCK_PROPS = [
    # Twitter specials
    C.TWITTER_OFFSETS1,
    # twitter .@
    C.TWITTER_OFFSETS2,

    # email
    C.EMAIL_OFFSETS,

    # url
    C.URL_OFFSETS,

    # numeric
    C.NUMERIC_OFFSETS,

    # embedded apostrophe
    C.EMBEDDED_APOS_OFFSETS,
]

# Define a combo matrix that will split on:
# * A symbol followed by whitespace
#    * e.g., a symbol at the end of a token
DEFAULT_SPLIT_PROPS2 = [
    [oft.SYMBOL_IDX, oft.NEXT_SPACE_IDX],
]


def get_specs_and_repls(spec_repl_tuples):
    '''
    Given a list of (FeatureSpec, repl_str) tuples,
    return the list of FeatureSpecs and a map from each FeatureSpec
    name to its corresponding repl_str.

    NOTE that if an abstract feature is to be generated, but not
    replaces, then the repl_str of None should be used and the
    resulting map will not have an entry for the FeatureSpec name.

    :param spec_repl_tuples: a list of (FeatureSpec, repl_str) tuples
    :return: spec_list, repl_map
    '''
    if spec_repl_tuples is None:
        return None, None
    specs = list()
    repls = dict()
    for spec, repl_str in spec_repl_tuples:
        if spec is not None:
            specs.append(spec)
            if repl_str is not None:
                repls[spec.name] = repl_str
    if len(repls) == 0:
        repls = None
    if len(specs) == 0:
        specs = None
    return specs, repls


class DefaultTokenizer:
    '''
    The default tokenizer uses the following strategy for tokenizing:
    (1) Identify various split tokens based on combinations of character properties
    (2) Mask blocks of characters to remain together as tokens
    (3) Identify remaining split tokens (or exceptions to general blocks)
    '''
    def __init__(self,
                 split_props1=None, block_props=None, split_props2=None,
                 abstract_feature_specs=None, abstract_token_replacements=None,
                 specs_and_repls=None, to_lower=False, drop_symbols=False,
                 keep_emojis=True, replace_abstract_tokens=None):
        '''
        Initialize with the given split/block/split properties.
        :param split_props1: The initial properties for identifying splits.
            default is DEFAULT_SPLIT_PROPS1
        :param block_props: The properties identifying spans to mask based
            on initial characters (and ending at whitespace). default is
            DEFAULT_BLOCK_PROPS
        :param split_props2: The remaining split token properties, or
            exceptions to blocks (ending at whitespace) -- e.g., trailing
            symbols on blocks. default is DEFAULT_SPLIT_PROPS2
        :param abstract_feature_specs: A list of FeatureSpec instances for
            abstract features with which to augment featurized tokens.
        :param abstract_token_replacements: A dictionary from abstract
            feature spec name to replacement text for tokens having the
            abstract feature.
        :param specs_and_repls: A list of (FeatureSpec, repl_str) tuples for
            defining the abstract_feature_specs and abstract_token_replacements
            map.
        :param to_lower: True to lowercase token text when tokenizing.
        :param drop_symbols: True to drop symbols when tokenizing.
        :param keep_emojis: True to keep emojis when dropping symbols.
        :param relace_abstract_tokens: True to always replace abstract tokens
            by default when tokenizing; False to not replace by default; None
            to set to True when specs are present or False when absent
        '''
        self._split_props1 = self._block_props = self._split_props2 = None
        self._c_split1 = self._c_block = self._c_split2 = None
        self.split_props1 = split_props1  # setter also sets _c_split1
        self.block_props = block_props    # setter also sets _c_block
        self.split_props2 = split_props2  # setter also sets _c_split2
        self.abstract_feature_specs = abstract_feature_specs
        self.abstract_token_replacements = abstract_token_replacements
        if specs_and_repls is not None:
            self.abstract_feature_specs, self.abstract_token_replacements = \
                get_specs_and_repls(specs_and_repls)
        self.to_lower = to_lower
        self.drop_symbols = drop_symbols
        self.keep_emojis = keep_emojis
        self.replace_abstract_tokens = replace_abstract_tokens
        if replace_abstract_tokens is None:
            self.replace_abstract_tokens = (
                self.abstract_feature_specs is not None)

    @property
    def split_props1(self):
        return self._split_props1

    @split_props1.setter
    def split_props1(self, value):
        if value is None:
            value = DEFAULT_SPLIT_PROPS1
        self._split_props1 = value
        self._c_split1 = build_combo_matrix(value)

    @property
    def block_props(self):
        return self._block_props

    @block_props.setter
    def block_props(self, value):
        if value is None:
            value = DEFAULT_BLOCK_PROPS
        self._block_props = value
        self._c_block = build_combo_matrix(value)

    @property
    def split_props2(self):
        return self._split_props2

    @split_props2.setter
    def split_props2(self, value):
        if value is None:
            value = DEFAULT_SPLIT_PROPS2
        self._split_props2 = value
        self._c_split2 = build_combo_matrix(value)

    def copy(self, split_props1=None, block_props=None, split_props2=None,
             abstract_feature_specs=None, abstract_token_replacements=None,
             specs_and_repls=None, to_lower=None, drop_symbols=None,
             keep_emojis=None, replace_abstract_tokens=None):
        '''
        Create a new tokenizer with this instance's settings unless
        overridden with a non-null parameter.
        :param split_props1: New properties for identifying splits.
        :param block_props: New properties identifying spans to mask based
            on initial characters (and ending at whitespace).
        :param split_props2: New remaining split token properties, or
            exceptions to blocks (ending at whitespace) -- e.g., trailing
            symbols on blocks.
        :param abstract_feature_specs: A new list of FeatureSpec instances for
            abstract features with which to augment featurized tokens.
        :param abstract_token_replacements: A new dictionary from abstract
            feature spec name to replacement text for tokens having the
            abstract feature.
        :param specs_and_repls: A new list of (FeatureSpec, repl_str) tuples for
            defining the abstract_feature_specs and abstract_token_replacements
            map.
        :param to_lower: True to lowercase token text when tokenizing.
        :param drop_symbols: True to drop symbols when tokenizing.
        :param keep_emojis: True to keep emojis when dropping symbols.
        :param relace_abstract_tokens: True to always replace abstract tokens
            by default when tokenizing; False to not replace by default; None
            to set to True when specs are present or False when absent
        '''
        return DefaultTokenizer(
            split_props1=(split_props1 if split_props1 is not None
                          else self._split_props1),
            block_props=(block_props if block_props is not None
                         else self._block_props),
            split_props2=(split_props2 if split_props2 is not None
                          else self._split_props2),
            abstract_feature_specs=(
                abstract_feature_specs if abstract_feature_specs is not None
                else self.abstract_feature_specs),
            abstract_token_replacements=(
                abstract_token_replacements if abstract_token_replacements is not None
                else self.abstract_token_replacements),
            specs_and_repls=specs_and_repls,
            to_lower=(to_lower if to_lower is not None
                      else self.to_lower),
            drop_symbols=(drop_symbols if drop_symbols is not None
                          else self.drop_symbols),
            keep_emojis=(keep_emojis if keep_emojis is not None
                         else self.keep_emojis),
            replace_abstract_tokens=(
                replace_abstract_tokens if replace_abstract_tokens is not None
                else self.replace_abstract_tokens))

    def gen_split_mask(self, text: str):
        '''
        Generate the feature matrix, m, for the text and the split mask
        array that identifies character positions at which to split by having
        non-zero entries.
        :param text: The text to parse
        :return: (m, splits) where m is the feature matrix and splits the split
            array.
        '''
        m0 = _gen_parse_matrix(text)
        m = m0.T  # Transpose to view features as rows instead of columns
    
        splits = (
            # split on e.g., whitespace and symbols
            _combine_matrix_rows(m, self._c_split1) *
    
            # block out e.g., urls, emails, twitter specials
            gen_block_mask(
                _combine_matrix_rows(m, self._c_block),
                m[oft.SPACE_IDX]))
    
        # split on e.g., terminating symbols after applying masks
        splits += _combine_matrix_rows(m, self._c_split2)
    
        # start of string is always a boundary
        if len(splits) > 0:
            splits[0] = 1
    
        return m0, splits

    def tokenize(self, text: str, replace_override=None,
                 abstract_token_replacement_overrides: Dict[str, str] = None,
                 abstract_feature_spec_overrides: Sequence[FeatureSpec] = None,
                 specs_and_repls_overrides=None, to_lower_override=None,
                 drop_symbols_override=None, keep_emojis_override=None):
        '''
        Tokenize the text, optionally replacing abstract tokens with a common
        string based on type.
    
        :param text: The input text to tokenize
        :param replace_override: Override for replace_abstract_tokens. When None,
            auto-set to replace when specs are present. When True or False, turn
            on or off replacement.
        :param abstract_token_replacement_overrides: Overrides for this
            instance's abstract token replacements
        :param abstract_feature_spec_overrides: The abstract feature specs
            to use instead of this instance's current specs.
        :param specs_and_repls_overrides: A list of (FeatureSpec, repl_str)
            tuples for defining the abstract_feature_specs and
            abstract_token_replacements map.
        :param to_lower_override: Override for whether to lowercase tokens
        :param drop_symbols_override: Override for dropping symbols.
        :param keep_emojis_override: Override for keeping emojis.
        :return: generated (string) tokens
        '''
        drop_syms = self.drop_symbols
        if drop_symbols_override is not None:
            drop_syms = drop_symbols_override
        replace = self.replace_abstract_tokens
        if replace_override is None:
            if (not replace and
                (abstract_feature_spec_overrides is not None
                 or specs_and_repls_overrides is not None)):
                replace = True
        else:
            replace = replace_override
        if replace or drop_syms:
            if replace and (specs_and_repls_overrides is not None):
                abstract_feature_spec_overrides, abstract_token_replacement_overrides = \
                    get_specs_and_repls(specs_and_repls_overrides)
            if replace:
                repls = (abstract_token_replacement_overrides
                         if abstract_token_replacement_overrides is not None
                         else self.abstract_token_replacements)
            else:
                repls = None
            keep_emojis = self.keep_emojis
            if keep_emojis_override is not None:
                keep_emojis = keep_emojis_override
            if repls is not None or drop_syms is True:
                for token in self.featurize(
                        text, add_abstract_features=True,
                        abstract_feature_spec_overrides=abstract_feature_spec_overrides):
                    if repls is not None and token.abstract_features is not None:
                        yield repls.get(token.abstract_features[0],
                                        self._normalize(token.text,
                                                        to_lower_override))
                    elif drop_syms and token.features[oft.SYMBOL_IDX] == token.size:
                        if keep_emojis and np.count_nonzero(token.features * C.EMOJIS_MASK):
                            yield self._normalize(token.text, to_lower_override)
                    else:
                        yield self._normalize(token.text, to_lower_override)
            else:
                yield from self._tokenize(
                    text, to_lower_override=to_lower_override)
        else:
            yield from self._tokenize(
                text, to_lower_override=to_lower_override)

    def _normalize(self, token_text, to_lower_override):
        to_lower = self.to_lower
        if to_lower_override is not None:
            to_lower = to_lower_override
        return token_text if not to_lower else token_text.lower()

    def _tokenize(self, text: str, to_lower_override=None):
        '''
        Tokenize text, yielding each token.
    
        :param text: The input text to tokenize
        :param to_lower_override: Override for whether to lowercase tokens
        :return: generated (string) tokens
        '''
        _, splits = self.gen_split_mask(text)
        non_zero = np.nonzero(splits)[0]
        if len(non_zero) > 0:
            to_lower = self.to_lower
            if to_lower_override is not None:
                to_lower = to_lower_override
            str_idx, end_idx = non_zero[0], 0
            for end_idx in non_zero[1:]:
                token = text[str_idx:end_idx].strip()
                if token:
                    yield token.lower() if to_lower else token
                str_idx = end_idx
            last_token = text[end_idx:].strip()
            if last_token:
                yield last_token.lower() if to_lower else last_token
        else:
            yield ''

    def featurize(self, text: str, add_abstract_features=None,
                  abstract_feature_spec_overrides: Sequence[FeatureSpec] = None
    ):
        '''
        Tokenize text using the given split mask generation function, yielding
        each token tagged with its features.
    
        :param text: The input text to tokenize
        :param add_abstract_features: When True, also add abstract features
            according to this instance's abstract feature specs or using the
            overrides if provided. When None, add abstract features if
            feature specs are present.
        :param abstract_feature_spec_overrides: The abstract feature specs
            to use instead of this instance's current specs.
        :return: generated LaToken instances
        '''
        specs = (abstract_feature_spec_overrides
                 if abstract_feature_spec_overrides is not None
                 else self.abstract_feature_specs)
        if add_abstract_features is None:
            add_abstract_features = (specs is not None)
        if add_abstract_features:
            if specs is not None:
                tokens = list(self._featurize(text))
                self._add_abstract_features(tokens, specs)
                yield from tokens
            else:
                yield from self._featurize(text)
        else:
            yield from self._featurize(text)
    
    def _featurize(self, text: str):
        '''
        Tokenize text using, yielding each token tagged with its features.
    
        :param text: The input text to tokenize
        :return: generated LaToken instances
        '''
        m, splits = self.gen_split_mask(text)
        non_zero = np.nonzero(splits)[0]
        textlen = len(text)
        if len(non_zero) > 0:
            str_idx, end_idx = non_zero[0], 0
            for end_idx in non_zero[1:]:
                token = text[str_idx:end_idx].strip()
                if token:
                    yield LaToken(
                        token, str_idx, end_idx,
                        np.sum(m[np.arange(str_idx, end_idx)], axis=0),
                        m, None
                    )
                str_idx = end_idx
            last_token = text[end_idx:].strip()
            if last_token:
                yield LaToken(
                    last_token, end_idx, textlen,
                    np.sum(m[np.arange(str_idx, end_idx)], axis=0),
                    m, None
                )
    
    def _add_abstract_features(self, la_tokens, feature_specs):
        for la_token in la_tokens:
            for feature_spec in feature_specs:
                if feature_spec.matches(la_token):
                    la_token.add_abstract_feature(feature_spec.name)
