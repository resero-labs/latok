'''
Definitions for various general tokenizers.
'''
import latok.core.constants as C
import latok.core.offsets as oft
import latok.core.split_mask_generator as split_mask_generator


# Define a combo matrix that will split on:
# * Whitespace  OR
# * Symbol OR
# * Prev-Symbol (effectively, each symbol becomes its own token) OR
# * CamelCase:
#    * at an Upper-case letter followed by a Lower-case letter OR
#    * at an Upper-case letter preceded by a Lower-case letter
SPLIT_PROPS1 = split_mask_generator.FastMask([
    [oft.SPACE_IDX],
    [oft.SYMBOL_IDX],
    [oft.PREV_SYMBOL_IDX],
    C.CAMEL_CASE_OFFSETS1,
    C.CAMEL_CASE_OFFSETS2,
], name='split1')


# Define a combo matrix that will identify blocks for embedded apostrophes
# so that such tokens will not be split. For example "isn't" would stay as
# "isn't" and not split to "isn" and "t" or "isn" and "'t":
# * Embedded apostrophe tokens
#    * an apostrophe character
#    * preceded by an alphabetic letter and
#    * followed by an alphabetic letter
APOS_BLOCK_PROPS = split_mask_generator.FastMask([
    # embedded apostrophe
    C.EMBEDDED_APOS_OFFSETS,
], name='a_blocks')

# Define a combo matrix that will identify embedded apostrophe block boundaries
# * Where a SPACE or SYMBOL marks a block boundary
APOS_BLOCK_END_PROPS = split_mask_generator.FastMask([
    # Space characters
    [oft.SPACE_IDX],
    # Symbol characters
    [oft.SYMBOL_IDX],
], name='a_blockend')


# Define a combo matrix that will split on:
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
GENERAL_BLOCK_PROPS = split_mask_generator.FastMask([
    # email
    C.EMAIL_OFFSETS,
    # url
    C.URL_OFFSETS,
    # numeric
    C.NUMERIC_OFFSETS,
], name='gblock1')


# Define a combo matrix that will identify block boundaries
# * Where a space marks a block boundary
# NOTE: this is the default block end behavior when None
GENERAL_BLOCK_END_PROPS = None


# Define a combo matrix that will split on:
# * A symbol followed by whitespace
#    * e.g., a symbol at the end of a token
#    * NOTE: This trims just one trailing symbol, still need to work out
#            something to trim multiple trailing symbols.
# * At a twitter symbol, effectively trimming preceding symbols
SPLIT_PROPS2 = split_mask_generator.FastMask([
    # Symbol followed by whitespace
    [oft.SYMBOL_IDX, oft.NEXT_SPACE_IDX],

    # Twitter specials
    C.TWITTER_OFFSETS_1A,
    C.TWITTER_OFFSETS_1B,
    # twitter .@
    C.TWITTER_OFFSETS_2A,
    C.TWITTER_OFFSETS_2B,
], name='split2')


def build_general_split_mask_generator(
        split_props1=SPLIT_PROPS1,
        block_props=GENERAL_BLOCK_PROPS,
        block_end_props=GENERAL_BLOCK_END_PROPS,
        split_props2=SPLIT_PROPS2,
        keep_embedded_apos=True):
    '''
    The general split mask generator allows for
    * Definition for initial splits (split_props1) (required)
    * Definition of blocks to prevent from splitting (optional)
    * Definition for additional splits (split_props2) (optional)

    If embedded apostrophes are to be kept within their tokens,
    these end up folding into (or becoming) the blocks to preserve.
    :param split_props1: The initial split mask (required)
    :param block_props: The (optional) block mask (not including embedded
        apostrophes, which are treated differently wrt block endpoints)
    :param block_end_props: The end block mask to accompany block_props
        If None and block_props are present, this will default to SPACE.
    :param split_props2: An additional final split mask (optional)
        Applied after the block (including embedded apostrophe) mask.
    :param keep_embedded_apos: When True, keep embedded apostrophes with
        their surrounding token text with block ends including symbols as
        well as spaces.
    '''
    smg = split_mask_generator.SplitMaskGenerator()
    smg.add_stage(split_mask_generator.MaskStage(
        'split1', split_props1))
    has_block_stage = False
    if keep_embedded_apos:
        smg.add_stage(
            split_mask_generator.BlockStage(
                'a_blocks', APOS_BLOCK_PROPS,
                end_mask=APOS_BLOCK_END_PROPS))
        has_block_stage = True
    if block_props is not None:
        smg.add_stage(
            split_mask_generator.BlockStage(
                'blocks1', block_props,
                end_mask=block_end_props))
        has_block_stage = True
    if split_props2 is not None:
        smg.add_stage(split_mask_generator.MaskStage('split2', split_props2))

    # Plan a step to mask defined blocks
    need_split_1 = True
    if has_block_stage:
        if keep_embedded_apos:
            smg.add_plan_step('blocks', 'a_blocks', 'blocks1', 'and')
            smg.add_plan_step('stage1', 'split1', 'blocks', 'and')
        else:
            smg.add_plan_step('stage1', 'split1', 'blocks', 'and')
        need_split_1 = False

    # Plan a step for a final trim, if present
    if split_props2 is not None:
        split1 = 'split1' if need_split_1 else 'stage1'
        smg.add_plan_step('trim1', split1, 'split2', 'or')
    elif need_split_1:
        # If we get here, there is only an initial split in the plan
        smg.add_plan_step('split1')

    return smg
