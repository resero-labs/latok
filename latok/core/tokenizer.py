'''
Tokenization wrapper(s) around the latok split mask generator cores.
'''
import numpy as np
import latok.core.constants as C
import latok.core.latok_utils as latok_utils
import latok.core.offsets as oft
import latok.core.split_mask_generator as split_mask_generator
#pylint: disable=no-name-in-module
from latok.latok import _gen_parse_matrix


class BaseSplitter:
    '''
    The base splitter is for common components between splitting and
    tokenization.
    '''
    def __init__(self, smg):
        self.smg = smg

    def gen_split_mask(self, text: str):
        '''
        Generate the feature matrix, m, for the text and the split mask
        array that identifies character positions at which to split by having
        non-zero entries.
        :param text: The text to parse
        :return: (m, splits) where m is the feature matrix and splits the split
            array.
        '''
        m = _gen_parse_matrix(text)
        splits = self.smg.process(m)
        return m, splits


class Splitter(BaseSplitter):
    '''
    Class without the bells and whistles (or convenience options) for optimally
    performant tokenization through splitting.
    '''
    def __init__(self,
                 smg=split_mask_generator.SIMPLE_SMG):
        '''
        Initialize with the given split_mask_generator and featurization
        parameters.
        :param smg: A SplitMaskGenerator ("core") for generating the
            tokenization split mask. Defaults to a SIMPLE_SMG.
        '''
        super().__init__(smg)

    def split(self, text: str):
        '''
        Split text, yielding each token.
    
        :param text: The input text to tokenize
        :return: generated (string) tokens
        '''
        _, splits = self.gen_split_mask(text)
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


class Tokenizer(BaseSplitter):
    '''
    Class for tokenizing and featurizing text.
    '''
    def __init__(self,
                 smg=split_mask_generator.SIMPLE_SMG,
                 specs_and_repls=None, to_lower=False, drop_symbols=False,
                 keep_emojis=True):
        '''
        Initialize with the given split_mask_generator and featurization
        parameters.
        :param smg: A SplitMaskGenerator ("core") for generating the
            tokenization split mask. Defaults to a SIMPLE_SMG.
        :param specs_and_repls: A list of (FeatureSpec, repl_str) tuples for
            defining the abstract features with which to augmented featurized
            tokens and the corresponding token replacement, which can be None
            to prevent token replacement while retaining the abstract feature.
            Note that for tokens having multiple feature_spec matches, this
            list specifies priority replacement order.
        :param to_lower: True to lowercase token text when tokenizing.
        :param drop_symbols: True to drop symbols when tokenizing.
        :param keep_emojis: True to keep emojis when dropping symbols.
        '''
        super().__init__(smg)
        if specs_and_repls is not None:
            self.specs, self.repls = latok_utils.get_specs_and_repls(specs_and_repls)
        else:
            self.specs = self.repls = None
        self.to_lower = to_lower
        self.drop_symbols = drop_symbols
        self.keep_emojis = keep_emojis

    def tokenize(self, text: str, disable_abstract_features=False,
                 specs_and_repls_overrides=None,
                 to_lower_override=None, drop_symbols_override=None,
                 keep_emojis_override=None):
        '''
        Tokenize the text, optionally replacing abstract tokens with a common
        string based on type.
    
        :param text: The input text to tokenize
        :param disable_abstract_features: True to disable adding abstract features.
            Note that this also disables token replacement of abstract features.
        :param specs_and_repls_overrides: A list of (FeatureSpec, repl_str) tuples
            for defining the abstract features with which to augmented featurized
            tokens and the corresponding token replacement, which can be None
            to prevent token replacement while retaining the abstract feature.
            Note that for tokens having multiple feature_spec matches, this
            list specifies priority replacement order.
        :param to_lower_override: Override for whether to lowercase tokens
        :param drop_symbols_override: Override for dropping symbols.
        :param keep_emojis_override: Override for keeping emojis.
        :return: generated (string) tokens
        '''
        drop_syms = self.drop_symbols
        if drop_symbols_override is not None:
            drop_syms = drop_symbols_override
        specs, repls = self._determine_specs_and_repls(
            disable_abstract_features, specs_and_repls_overrides)
        if repls is not None or drop_syms:
            keep_emojis = self.keep_emojis
            if keep_emojis_override is not None:
                keep_emojis = keep_emojis_override
            if repls is not None or drop_syms is True:
                for token in self._determined_featurize(text, specs, repls):
                    if token.repl is not None:
                        yield token.repl
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

    def featurize(self, text: str, disable_abstract_features=False,
                  specs_and_repls_overrides=None):
        '''
        Tokenize text using the given split mask generation function, yielding
        each token tagged with its features.
    
        :param text: The input text to tokenize
        :param disable_abstract_features: True to disable adding abstract features
        :param specs_and_repls_overrides: A list of (FeatureSpec, repl_str) tuples
            for defining the abstract features with which to augmented featurized
            tokens and the corresponding token replacement, which can be None
            to prevent token replacement while retaining the abstract feature.
            Note that for tokens having multiple feature_spec matches, this
            list specifies priority replacement order.
        :return: generated LaToken instances
        '''
        specs, repls = self._determine_specs_and_repls(
            disable_abstract_features, specs_and_repls_overrides)
        yield from self._determined_featurize(text, specs, repls)
    
    def _determined_featurize(self, text: str, specs, repls):
        '''
        Do the self.featurize work when key params have been determined.
        '''
        if specs is not None:
            tokens = list(self._featurize(text))
            self._add_abstract_features(tokens, specs, repls)
            yield from tokens
        else:
            yield from self._featurize(text)

    def _determine_specs_and_repls(self, disable_abstract_features,
                                   specs_and_repls_overrides):
        if not disable_abstract_features:
            if specs_and_repls_overrides is not None:
                return latok_utils.get_specs_and_repls(specs_and_repls_overrides)
            else:
                return self.specs, self.repls
        return None, None

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
                    yield latok_utils.LaToken(
                        token, str_idx, end_idx,
                        np.sum(m[np.arange(str_idx, end_idx)], axis=0),
                        m, None, None
                    )
                str_idx = end_idx
            last_token = text[end_idx:].strip()
            if last_token:
                yield latok_utils.LaToken(
                    last_token, end_idx, textlen,
                    np.sum(m[np.arange(end_idx, textlen)], axis=0),
                    m, None, None
                )
    
    def _add_abstract_features(self, la_tokens, feature_specs, repls=None):
        for la_token in la_tokens:
            repl = None
            for feature_spec in feature_specs:
                if feature_spec.matches(la_token):
                    la_token.add_abstract_feature(feature_spec.name)
                    if repls is not None and repl is None:
                        repl = repls.get(feature_spec.name, None)
                        if repl:
                            la_token.repl = repl


#def build_tokenizer(smg=split_mask_generator.SIMPLE_SMG,
#                    to_lower=True, drop_symbols=True, keep_emojis=False,
#                    specs_and_repls=None):
