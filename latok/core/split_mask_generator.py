'''
Core classes and implementations for generating split masks.
'''

import numpy as np
import pandas as pd
from collections import deque
from dataclasses import dataclass
import latok.core.offsets as oft
import latok.core.latok_utils as latok_utils
#pylint: disable=no-name-in-module
from latok.latok import _gen_parse_matrix, _combine_matrix_rows


class FastMask:
    '''
    Container for defining a simple (and fast) mask for character features.
    '''
    def __init__(self, mask_properties, combo_flag=None, name=None):
        '''
        Initialize this mask.
        :param mask_properties: The list of lists of character feature numbers
            identifying points at which to mask
        :param combo_flag: The way to combine this with a prior mask ('and',
            'or', 'xor', 'and-not', 'or-not', 'xor-not') or logical operation
            on this mask's computed features ('not')
        :param name: A name for this mask instance
        '''
        self.mask_properties = mask_properties
        self.combo_matrix = latok_utils.build_combo_matrix(mask_properties)
        self.combo_flag = combo_flag
        self.name = name

    def get_features(self, features_matrix):
        '''
        Get this mask's features with respect to the given input features
        matrix.
        '''
        return _combine_matrix_rows(features_matrix, self.combo_matrix)
        
    def combine(self, fvec1, fvec2):
        return latok_utils.combine(fvec1, fvec2, self.combo_flag)

    def describe(self):
        name = self.name if self.name else 'Mask'
        return {
            'name': name,
            'features': latok_utils.feature_names(self.combo_matrix),
            'combo_flag': self.combo_flag,
        }


class Mask:
    '''
    Container for defining a complex mask for character features using rolls
    and/or chains of masks.
    '''
    def __init__(self, mask_properties, features_roll=0, features_op=None,
                 combo_flag=None, pre_combo_roll1=0, pre_combo_roll2=0,
                 post_combo_roll=0, post_combo_op=None, next_mask=None,
                 name=None):
        '''
        Initialize this mask.
        :param mask_properties: The list of lists of character feature numbers
            identifying points at which to mask
        :param features_roll: Amount to roll this mask's computed features
        :param features_op: An operation to apply to this mask's computed
            features (after features_roll)
        :param combo_flag: The way to combine this with a prior mask ('and',
            'or', 'xor', 'and-not', 'or-not', 'xor-not') or logical operation
            on this mask's computed features ('not')
        :param pre_combo_roll1: Amount to roll prior features before combining
            with this mask's features
        :param pre_combo_roll2: Amount to roll this mask's features before
            prior features are combined with them
        :param post_combo_roll: Amount to roll the result after combining
        :param post_combo_op: An operation to apply after combining and
            applying any post roll
        :param next_mask: The next mask to apply in this chain of masks
        :param name: A name for this mask instance
        '''
        self.mask_properties = mask_properties
        self.combo_matrix = latok_utils.build_combo_matrix(mask_properties)
        self.features_roll = features_roll
        self.features_op = features_op
        self.combo_flag = combo_flag  #NOTE: ignored for first mask in chain unless=="not"
        self.pre_combo_roll1 = pre_combo_roll1  #NOTE: ignored for first mask in chain
        self.pre_combo_roll2 = pre_combo_roll2  #NOTE: ignored for first mask in chain
        self.post_combo_roll = post_combo_roll  #NOTE: ignored for first mask in chain
        self.post_combo_op = post_combo_op  #NOTE: ignored for first mask in chain
        self.next_mask = next_mask
        self.name = name

    def set_next_mask(self, mask):
        '''
        Set the next mask to apply. Note that masks after the first need to
        have the combo_flag defined.
        '''
        self.next_mask = mask
        return mask

    def get_features(self, features_matrix):
        '''
        Get this mask's features with respect to the given input features
        matrix.
        '''
        result = _combine_matrix_rows(features_matrix, self.combo_matrix)
        if self.features_roll:
            result = np.roll(result, self.features_roll)
        if self.features_op is not None:
            result = self.features_op(result)
        if self.combo_flag == "not":
            result = np.logical_not(result)
        next_mask = self.next_mask
        while next_mask is not None:
            next_result = next_mask.get_features(features_matrix)
            result = next_mask.combine(result, next_result)
            next_mask = next_mask.next_mask
        return result
        
    def combine(self, fvec1, fvec2):
        result = None
        if self.pre_combo_roll1:
            fvec1 = np.roll(fvec1, self.pre_combo_roll1)
        if self.pre_combo_roll2:
            fvec2 = np.roll(fvec2, self.pre_combo_roll2)
        result = latok_utils.combine(fvec1, fvec2, self.combo_flag)
        if self.post_combo_roll:
            result = np.roll(result, self.post_combo_roll)
        if self.post_combo_op is not None:
            result = self.post_combo_op(result)
        return result

    def describe(self):
        name = self.name if self.name else 'Mask'
        next_mask = self.next_mask.describe() if self.next_mask is not None else None
        return {
            'name': name,
            'features': latok_utils.feature_names(self.combo_matrix),
            'features_roll': self.features_roll,
            'features_op': self.features_op != None,
            'combo_flag': self.combo_flag,
            'pre_combo_roll1': self.pre_combo_roll1,
            'pre_combo_roll2': self.pre_combo_roll2,
            'post_combo_roll': self.post_combo_roll,
            'post_combo_op': self.post_combo_op != None,
            'next_mask': next_mask,
        }


class MaskStage:
    '''
    Container for defining a masking stage.
    '''
    def __init__(self, name, mask):
        '''
        Initialize this mask stage.
        :param name: The name of this stage
        :param mask: The Mask instance to use in this stage.
        '''
        self.name = name
        self.mask = mask

    def operate(self, features_matrix):
        '''
        Generate a mask vector by applying this stage's mask to the input
        features matrix, taking applicable stage rolls and operations into
        account.
        :param features_matrix: The input feature matrix to mask
        :return: The resultant mask vector
        '''
        return self.mask.get_features(features_matrix)

    def describe(self):
        return {
            'name': self.name,
            'mask': self.mask.describe(),
        }
        
    def get_features(self, m):
        '''
        Convenience/debugging method for generating features against an input
        feature matrix.
        '''
        return [
            ('mask', self.mask.get_features(m)),  #todo: get full mask chain
        ]


class BlockStage(MaskStage):
    '''
    Container for defining a block masking stage, where a block is defined by
    an internal point and endpoint feature properties.
    '''
    def __init__(self, name, point_mask, end_mask=None):
        '''
        Initialize this block mask stage.
        :param name: The name of this stage
        :param point_mask: The point Mask instance for identifying "inner"
           points to find a block
        :param end_mask: The ends Mask instance identifying points outside of
            the block
        '''
        super().__init__(name, point_mask)
        self.end_mask = end_mask

    def operate(self, features_matrix):
        '''
        Generate a block mask vector by applying this stage's point mask to the
        input features matrix, finding the end points, and blocking out the
        characters (as 0's) to not split.
        :param features_matrix: The input feature matrix to mask
        :return: The resultant mask vector
        '''
        block_pts = super().operate(features_matrix)
        return self._gen_block_mask(features_matrix, block_pts)

    def describe(self):
        if self.end_mask is not None:
            end_mask = self.end_mask.describe()
        else:
            end_mask = latok_utils.feature_names(
                latok_utils.build_combo_matrix([[oft.SPACE_IDX]]))
        return {
            'name': self.name,
            'point_mask': self.mask.describe(),
            'end_mask': end_mask,
        }

    def get_features(self, m):
        '''
        Convenience/debugging method for generating features against an input
        feature matrix.
        '''
        if self.end_mask is None:
            end_mask_features = _combine_matrix_rows(
                m, latok_utils.build_combo_matrix([[oft.SPACE_IDX]]))
        else:
            end_mask_features = self.end_mask.get_features(m)  #todo: get full mask chain
        return [
            ('point', self.mask.get_features(m)),  #todo: get full mask chain
            ('ends', end_mask_features)
        ]

    def _gen_block_mask(self, features, block_pts):
        if self.end_mask is None:
            # Default external block endpoints are spaces
            block_ends = features[oft.SPACE_IDX]
        else:
            block_ends = (
                # Exclude block trigger points themselves as endpoints
                np.logical_not(block_pts) *
                # Current block ends
                self.end_mask.get_features(features)
            )
        # Squeeze in front of block end to set split point on 1st block char
        squeeze_mask = block_ends[1:-1]
        block_ends[np.where(np.roll(squeeze_mask, 1) - squeeze_mask > 0)[0] + 1] = 1
        return latok_utils.gen_block_mask(block_pts, block_ends)


@dataclass
class MaskStep:
    '''
    Structure for a mask plan step.
    '''
    output_name: str
    input_name: str
    combine_with: str
    operation: str


class SplitMaskGenerator:
    '''
    '''
    def __init__(self):
        '''
        Initialize an empty instance to which stages and a plan can be added.
        '''
        # split plan stores groups of stages toggling between split and block
        self.stages = dict()
        self.plan = list()

    def add_stage(self, stage):
        '''
        '''
        self.stages[stage.name] = stage
        return self

    def add_plan_step(self, output_name, input_name=None,
                      combine_with=None, operation=None):
        '''
        Add a plan step to process the named input to be referenced by the
        output name after either computing from the input features matrix
        or combining with another named output as designated.

        Processing procedes using the following rules with respect to a plan
        step:

        If input_name is None, then output_name refers to the stage of the
        same name, which will be applied to the input matrix.

        If input_name matches an already computed output_name, that output
        will be used; otherwise, the result of the stage matching the input_name
        will be used as input.

        If combine_with has not yet been computed, its matching stage will
        first be computed against the input matrix.
        '''
        if input_name is None:
            input_name = output_name
        self.plan.append(
            MaskStep(output_name, input_name, combine_with, operation))
        return self

    def _get_split_vector(self, splits, m, name):
        vec = splits.get(name, None)
        if vec is None:
            stage = self.stages.get(name)
            vec = splits[name] = stage.operate(m)
        return vec

    def process(self, m):
        '''
        Generate a split mask for the given parse matrix.
        :param m: A parse matrix as returned by _gen_parse_matrix
        :return: A split mask vector
        '''
        m = m.T  # Transpose to view features as rows instead of columns
        vec = None
        splits = dict()
        for mask_step in self.plan:
            vec = self._get_split_vector(splits, m, mask_step.input_name)
            if mask_step.combine_with and mask_step.operation:
                vec2 = self._get_split_vector(splits, m, mask_step.combine_with)
                vec = splits[mask_step.output_name] = latok_utils.combine(
                    vec, vec2, mask_step.operation)
            elif mask_step.output_name != mask_step.input_name:
                splits[mask_step.output_name] = vec
        # start of string is always a boundary
        if vec is not None and len(vec) > 0:
            vec[0] = 1
        return vec

    def trace(self, m):
        '''
        Same as self.process() except tracks and preserves each stage's mask
        for tracing the split mask generation.
        NOTE: This code will need to be kept in sync with that of self.process
              but is not being combined so that the tracing overhead is not
              incurred during normal processing.
        :param m: A parse matrix as returned by _gen_parse_matrix
        :return: A list of (stage_name, split_mask_vector) tuples
            Where the items in the list are ordered from the final to initial
            split masks through all stages.
        '''
        m = m.T  # Transpose to view features as rows instead of columns
        result = deque()
        splits = dict()
        for step_idx, mask_step in enumerate(self.plan):
            got_vec = mask_step.output_name in splits
            vec = self._get_split_vector(splits, m, mask_step.input_name)
            if not got_vec:
                result.appendleft(
                    (f'{mask_step.input_name}.{step_idx}', vec))
            if mask_step.combine_with and mask_step.operation:
                got_vec2 = mask_step.combine_with in splits
                vec2 = self._get_split_vector(splits, m, mask_step.combine_with)
                if not got_vec2:
                    result.appendleft(
                        (f'{mask_step.combine_with}.{step_idx}', vec2))
                got_combo = mask_step.output_name in splits
                vec = splits[mask_step.output_name] = latok_utils.combine(
                    vec, vec2, mask_step.operation)
                if not got_combo:
                    result.appendleft(
                        (f'{mask_step.output_name}={mask_step.input_name}.{mask_step.operation}.{mask_step.combine_with}',
                         vec))
            elif mask_step.output_name != mask_step.input_name:
                splits[mask_step.output_name] = vec
                result.appendleft(
                    (f'{mask_step.output_name}.{step_idx}', vec))
        # start of string is always a boundary
        if vec is not None and len(vec) > 0:
            vec[0] = 1
        return result

    def build_dataframe(self, text: str):
        '''
        Build a pandas dataframe describing the tokenization of the text
        where each row is a letter of the text and columns show the masks
        and features for each letter.
        '''
        if not text:
            return None
        columns = [pd.Series([c for c in text], name='Chars')]
        m = _gen_parse_matrix(text)
        splits = self.trace(m)
        if splits is not None:
            columns.extend([
                pd.Series(mask, name=stage_name)
                for stage_name, mask in splits
            ])
        columns.append(pd.DataFrame(m, columns=latok_utils.FEATURE_NAMES))
        df = pd.concat(columns, axis=1)
        return df

    def describe_split_plan(self):
        '''
        Utility method to describe the split plan in terms of feature
        names.
        usage example: print(json.dumps(smg.describe_split_plan(), indent=2))
        '''
        return {
            'steps': {
                f'step_{step_idx}': {
                    'input_name': step.input_name,
                    'output_name': step.output_name,
                    'combine_with': step.combine_with,
                    'operation': step.operation,
                }
                for step_idx, step in enumerate(self.plan)
            },
            'stages': {
                f'{stage_name}_{stage_idx}': stage.describe()
                for stage_idx, (stage_name, stage) in enumerate(self.stages.items())
            }
        }


def build_simple_smg():
    smg = SplitMaskGenerator()
    smg.add_stage(
        MaskStage(
            'split',
            FastMask([
                [oft.SPACE_IDX],
                [oft.SYMBOL_IDX],
                [oft.PREV_SYMBOL_IDX],
            ], name='non-alnum')))
    smg.add_plan_step('split')
    return smg


# A split mask generator for splitting just on whitespace and symbols
SIMPLE_SMG = build_simple_smg()
