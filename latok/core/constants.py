import numpy as np
import latok.core.offsets as oft
from latok.core.latok_utils import OffsetSpec, FeatureSpec


# Emojis Feature Mask
EMOJIS_MASK = np.zeros(oft.FEATURE_COUNT, dtype=np.int8)
EMOJIS_MASK[[
    oft.CHAR_EMOJI_IDX, oft.CHAR_EMOJI_PRESENTATION_IDX,
    oft.CHAR_EMOJI_MODIFIER_BASE_IDX, oft.CHAR_EMOJI_COMPONENT_IDX,
    oft.CHAR_EXTENDED_PICTOGRAPHIC_IDX]] = 1

#
# Define common offset combinations for tokens
#
TWITTER_OFFSETS_1A = [oft.TWITTER_IDX, oft.PREV_SPACE_IDX, oft.NEXT_ALPHA_NUM_IDX]
TWITTER_OFFSETS_1B = [oft.TWITTER_IDX, oft.PREV_SYMBOL_IDX, oft.NEXT_ALPHA_NUM_IDX]
TWITTER_OFFSETS_2A = [oft.CHAR_PERIOD_IDX, oft.PREV_SPACE_IDX, oft.NEXT_AT_IDX, oft.AFTER_NEXT_ALPHA_IDX]
TWITTER_OFFSETS_2B = [oft.CHAR_PERIOD_IDX, oft.PREV_SYMBOL_IDX, oft.NEXT_AT_IDX, oft.AFTER_NEXT_ALPHA_IDX]
TWITTER_MENTION_OFFSETS_1A = [oft.CHAR_AT_IDX, oft.PREV_SPACE_IDX, oft.NEXT_ALPHA_NUM_IDX]
TWITTER_MENTION_OFFSETS_1B = [oft.CHAR_AT_IDX, oft.PREV_SYMBOL_IDX, oft.NEXT_ALPHA_NUM_IDX]
TWITTER_MENTION_OFFSETS_2A = TWITTER_OFFSETS_2A
TWITTER_MENTION_OFFSETS_2B = TWITTER_OFFSETS_2B
TWITTER_HASHTAG_OFFSETS_A = [oft.CHAR_HASH_IDX, oft.PREV_SPACE_IDX, oft.NEXT_ALPHA_NUM_IDX]
TWITTER_HASHTAG_OFFSETS_B = [oft.CHAR_HASH_IDX, oft.PREV_SYMBOL_IDX, oft.NEXT_ALPHA_NUM_IDX]
EMAIL_OFFSETS = [oft.CHAR_AT_IDX, oft.PREV_ALPHA_NUM_IDX, oft.NEXT_ALPHA_NUM_IDX]
URL_OFFSETS = [oft.CHAR_COLON_IDX, oft.NEXT_SLASH_IDX, oft.AFTER_NEXT_SLASH_IDX, oft.PREV_ALPHA_IDX]
NUMERIC_OFFSETS = [oft.NUM_IDX]
EMBEDDED_APOS_OFFSETS = [oft.CHAR_APOS_IDX, oft.PREV_ALPHA_IDX, oft.NEXT_ALPHA_IDX]
CAMEL_CASE_OFFSETS1 = [oft.UPPER_IDX, oft.NEXT_LOWER_IDX]
CAMEL_CASE_OFFSETS2 = [oft.UPPER_IDX, oft.PREV_LOWER_IDX]
SYMBOLS_OFFSETS = [oft.SYMBOL_IDX]

#
# Define common abstracted token features
#
TWITTER_FEATURE = FeatureSpec('twitter',
                              [OffsetSpec(present=TWITTER_OFFSETS_1A),
                               OffsetSpec(present=TWITTER_OFFSETS_1B),
                               OffsetSpec(present=TWITTER_OFFSETS_2A),
                               OffsetSpec(present=TWITTER_OFFSETS_2B)],
                              None, None, None)
TWITTER_MENTION_FEATURE = FeatureSpec('mention',
                              [OffsetSpec(present=TWITTER_MENTION_OFFSETS_1A),
                               OffsetSpec(present=TWITTER_MENTION_OFFSETS_1B),
                               OffsetSpec(present=TWITTER_MENTION_OFFSETS_2A),
                               OffsetSpec(present=TWITTER_MENTION_OFFSETS_2B)],
                              None, None, None)
TWITTER_HASHTAG_FEATURE = FeatureSpec('hashtag',
                              [OffsetSpec(present=TWITTER_HASHTAG_OFFSETS_A),
                               OffsetSpec(present=TWITTER_HASHTAG_OFFSETS_B)],
                              None, None, None)
EMOJI_FEATURE = FeatureSpec('emoji',
                            [OffsetSpec(present=[oft.CHAR_EMOJI_IDX]),
                             OffsetSpec(present=[oft.CHAR_EMOJI_PRESENTATION_IDX]),
                             OffsetSpec(present=[oft.CHAR_EMOJI_MODIFIER_BASE_IDX]),
                             OffsetSpec(present=[oft.CHAR_EMOJI_COMPONENT_IDX]),
                             OffsetSpec(present=[oft.CHAR_EXTENDED_PICTOGRAPHIC_IDX])],
                            None, None, None)
EMAIL_FEATURE = FeatureSpec('email',
                            [OffsetSpec(present=EMAIL_OFFSETS)],
                            None, None, None)
URL_FEATURE = FeatureSpec('url',
                          [OffsetSpec(present=URL_OFFSETS)],
                          None, None, None)
NUMERIC_FEATURE = FeatureSpec('numeric',
                              [OffsetSpec(present=NUMERIC_OFFSETS)],
                              None, None, None)
CAMEL_CASE_FEATURE = FeatureSpec('camelcase',
                                 [OffsetSpec(present=CAMEL_CASE_OFFSETS2)],
                                 None, None, None)
EMBEDDED_APOS_FEATURE = FeatureSpec('apos',
                                    [OffsetSpec(present=EMBEDDED_APOS_OFFSETS)],
                                    None, None, None)
SYMBOLS_ONLY_FEATURE = FeatureSpec('symbols',
                                   None,
                                   [OffsetSpec(present=SYMBOLS_OFFSETS,
                                               absent=[[oft.ALPHA_IDX], [oft.NUM_IDX]])],
                                   None, None)
