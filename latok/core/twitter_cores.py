'''
Definitions for various twitter tokenizers.
'''
import latok.core.constants as C
import latok.core.general_cores as general_cores
import latok.core.offsets as oft
import latok.core.split_mask_generator as split_mask_generator


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
TWEET_BLOCK_PROPS = split_mask_generator.FastMask([
    # Twitter specials
    C.TWITTER_OFFSETS_1A,
    C.TWITTER_OFFSETS_1B,
    # twitter .@
    C.TWITTER_OFFSETS_2A,
    C.TWITTER_OFFSETS_2B,

    # email
    C.EMAIL_OFFSETS,
    # url
    C.URL_OFFSETS,
    # numeric
    C.NUMERIC_OFFSETS,
], name='tblock1')


# Same as TWEET_BLOCK_PROPS above, but just for mentions.
# Using MENTION_BLOCK_PROPS instead of TWEET_BLOCK_PROPS will retain mentions
# as single featurized tokens while essentially ignoring hashtags, thereby
# allowing hashtags to be split on camelcase into tokens with the hashtag
# removed.
MENTION_BLOCK_PROPS = split_mask_generator.FastMask([
    # Twitter specials
    C.TWITTER_MENTION_OFFSETS_1A,
    C.TWITTER_MENTION_OFFSETS_1B,
    # twitter .@
    C.TWITTER_MENTION_OFFSETS_2A,
    C.TWITTER_MENTION_OFFSETS_2B,

    # email
    C.EMAIL_OFFSETS,
    # url
    C.URL_OFFSETS,
    # numeric
    C.NUMERIC_OFFSETS,
], name='mblock1')


# Define a combo matrix that will identify block boundaries
# * Where a space marks a block boundary
# NOTE: this is the default block end behavior when None
TWEET_BLOCK_END_PROPS = None


# Define a combo matrix that will split on:
# * A symbol followed by whitespace
#    * e.g., a symbol at the end of a token
#    * NOTE: This trims just one trailing symbol, still need to work out
#            something to trim multiple trailing symbols.
# * At a twitter symbol, effectively trimming preceding symbols
TWEET_SPLIT_PROPS2 = split_mask_generator.FastMask([
    # Symbol followed by whitespace
    [oft.SYMBOL_IDX, oft.NEXT_SPACE_IDX],

    # Twitter specials
    C.TWITTER_OFFSETS_1A,
    C.TWITTER_OFFSETS_1B,
    # twitter .@
    C.TWITTER_OFFSETS_2A,
    C.TWITTER_OFFSETS_2B,
], name='tsplit2')


def build_twitter_split_mask_generator(preserve_only_mentions=True):
    tweet_block_props = TWEET_BLOCK_PROPS
    if preserve_only_mentions:
        tweet_block_props = MENTION_BLOCK_PROPS

    smg = split_mask_generator.SplitMaskGenerator()
    smg.add_stage(split_mask_generator.MaskStage(
        'split1', general_cores.SPLIT_PROPS1))
    smg.add_stage(
        split_mask_generator.BlockStage(
            'a_blocks', general_cores.APOS_BLOCK_PROPS,
            end_mask=general_cores.APOS_BLOCK_END_PROPS))
    smg.add_stage(
        split_mask_generator.BlockStage(
            'blocks1', tweet_block_props,
            end_mask=TWEET_BLOCK_END_PROPS))
    smg.add_stage(split_mask_generator.MaskStage('split2', TWEET_SPLIT_PROPS2))

    smg.add_plan_step('blocks', 'a_blocks', 'blocks1', 'and')
    smg.add_plan_step('stage1', 'split1', 'blocks', 'and')
    smg.add_plan_step('trim1', 'stage1', 'split2', 'or')

    return smg


# A split mask generator for tweet-aware splitting that preserves blocks
# with all twitter specials (mentions, hashtags, etc.)
TWEET_SMG = build_twitter_split_mask_generator(False)


# A split mask generator for mention-aware splitting that preserves blocks
# with all twitter mentions, but splits the others (hashtags, etc.)
MENTION_SMG = build_twitter_split_mask_generator(True)
