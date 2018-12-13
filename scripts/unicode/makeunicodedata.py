#
# This file was copied from the Python 3.7.1 source distribution and modified to add flags
# for special characers (#@, etc.)
#
# (re)generate unicode property and type databases
#
# This script converts Unicode database files to Modules/unicodedata_db.h,
# Modules/unicodename_db.h, and Objects/unicodetype_db.h
#
# history:
# 2000-09-24 fl   created (based on bits and pieces from unidb)
# 2000-09-25 fl   merged tim's splitbin fixes, separate decomposition table
# 2000-09-25 fl   added character type table
# 2000-09-26 fl   added LINEBREAK, DECIMAL, and DIGIT flags/fields (2.0)
# 2000-11-03 fl   expand first/last ranges
# 2001-01-19 fl   added character name tables (2.1)
# 2001-01-21 fl   added decomp compression; dynamic phrasebook threshold
# 2002-09-11 wd   use string methods
# 2002-10-18 mvl  update to Unicode 3.2
# 2002-10-22 mvl  generate NFC tables
# 2002-11-24 mvl  expand all ranges, sort names version-independently
# 2002-11-25 mvl  add UNIDATA_VERSION
# 2004-05-29 perky add east asian width information
# 2006-03-10 mvl  update to Unicode 4.1; add UCD 3.2 delta
# 2008-06-11 gb   add PRINTABLE_MASK for Atsuo Ishimoto's ascii() patch
# 2011-10-21 ezio add support for name aliases and named sequences
# 2012-01    benjamin add full case mappings
# 2018-10-26 rappdw "steal" from python implementation for the purpose of latok
#
# written by Fredrik Lundh (fredrik@pythonware.com)
#

import os
import sys
import zipfile

from textwrap import dedent

SCRIPT = sys.argv[0]
VERSION = "3.3"

# The Unicode Database
# --------------------
# When changing UCD version please update
#   * Doc/library/stdtypes.rst, and
#   * Doc/library/unicodedata.rst
#   * Doc/reference/lexical_analysis.rst (two occurrences)
UNIDATA_VERSION = "11.0.0"
UNICODE_DATA = "UnicodeData%s.txt"
COMPOSITION_EXCLUSIONS = "CompositionExclusions%s.txt"
EASTASIAN_WIDTH = "EastAsianWidth%s.txt"
UNIHAN = "Unihan%s.zip"
DERIVED_CORE_PROPERTIES = "DerivedCoreProperties%s.txt"
DERIVEDNORMALIZATION_PROPS = "DerivedNormalizationProps%s.txt"
LINE_BREAK = "LineBreak%s.txt"
NAME_ALIASES = "NameAliases%s.txt"
NAMED_SEQUENCES = "NamedSequences%s.txt"
SPECIAL_CASING = "SpecialCasing%s.txt"
CASE_FOLDING = "CaseFolding%s.txt"

# Private Use Areas -- in planes 1, 15, 16
PUA_1 = range(0xE000, 0xF900)
PUA_15 = range(0xF0000, 0xFFFFE)
PUA_16 = range(0x100000, 0x10FFFE)

# we use this ranges of PUA_15 to store name aliases and named sequences
NAME_ALIASES_START = 0xF0000
NAMED_SEQUENCES_START = 0xF0200

old_versions = ["3.2.0"]

CATEGORY_NAMES = [ "Cn", "Lu", "Ll", "Lt", "Mn", "Mc", "Me", "Nd",
    "Nl", "No", "Zs", "Zl", "Zp", "Cc", "Cf", "Cs", "Co", "Cn", "Lm",
    "Lo", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk",
    "So" ]

BIDIRECTIONAL_NAMES = [ "", "L", "LRE", "LRO", "R", "AL", "RLE", "RLO",
    "PDF", "EN", "ES", "ET", "AN", "CS", "NSM", "BN", "B", "S", "WS",
    "ON", "LRI", "RLI", "FSI", "PDI" ]

EASTASIANWIDTH_NAMES = [ "F", "H", "W", "Na", "A", "N" ]

MANDATORY_LINE_BREAKS = [ "BK", "CR", "LF", "NL" ]

# note: should match definitions in Objects/unicodectype.c
ALPHA_MASK = 0x01
DECIMAL_MASK = 0x02
DIGIT_MASK = 0x04
LOWER_MASK = 0x08
LINEBREAK_MASK = 0x10
SPACE_MASK = 0x20
TITLE_MASK = 0x40
UPPER_MASK = 0x80
XID_START_MASK = 0x100
XID_CONTINUE_MASK = 0x200
PRINTABLE_MASK = 0x400
NUMERIC_MASK = 0x800
CASE_IGNORABLE_MASK = 0x1000
CASED_MASK = 0x2000
EXTENDED_CASE_MASK = 0x4000
TWITTER_SPECIALS_MASK = 0x8000 # one of (#, @, $, ^)
CHAR_AT_MASK = 0x010000
CHAR_COLON_MASK = 0x020000
CHAR_SLASH_MASK = 0x040000
CHAR_PERIOD_MASK = 0x080000
CHAR_APOS_MASK = 0x0100000

# NOTE: adjust sizing masks if adding more masks above!
SIZING_MASK = 0x1000000
DESIZING_MASK = 0x0FFFFFF

# these ranges need to match unicodedata.c:is_unified_ideograph
cjk_ranges = [
    ('3400', '4DB5'),
    ('4E00', '9FEF'),
    ('20000', '2A6D6'),
    ('2A700', '2B734'),
    ('2B740', '2B81D'),
    ('2B820', '2CEA1'),
    ('2CEB0', '2EBE0'),
]

def maketables(trace=0):

    print("--- Reading", UNICODE_DATA % "", "...")

    version = ""
    unicode = UnicodeData(UNIDATA_VERSION)

    print(len(list(filter(None, unicode.table))), "characters")

    for version in old_versions:
        print("--- Reading", UNICODE_DATA % ("-"+version), "...")
        old_unicode = UnicodeData(version, cjk_check=False)
        print(len(list(filter(None, old_unicode.table))), "characters")
        merge_old_version(version, unicode, old_unicode)

    makeunicodetype(unicode, trace)

# --------------------------------------------------------------------
# unicode character type tables

def makeunicodetype(unicode, trace):

    FILE = "../../latok/core/src/latok/latok.h"

    print("--- Preparing", FILE, "...")

    # extract unicode types
    dummy = (0, 0, 0, 0, 0, 0)
    table = [dummy]
    cache = {0: dummy}
    index = [0] * len(unicode.chars)
    numeric = {}
    spaces = []
    linebreaks = []
    extra_casing = []

    for char in unicode.chars:
        record = unicode.table[char]
        if record:
            # extract database properties
            category = record[2]
            bidirectional = record[4]
            properties = record[16]
            flags = SIZING_MASK  # Set an extra high bit to establish the size of the flags
            delta = True
            if category in ["Lm", "Lt", "Lu", "Ll", "Lo"]:
                flags |= ALPHA_MASK
            if "Lowercase" in properties:
                flags |= LOWER_MASK
            if 'Line_Break' in properties or bidirectional == "B":
                flags |= LINEBREAK_MASK
                linebreaks.append(char)
            if category == "Zs" or bidirectional in ("WS", "B", "S"):
                flags |= SPACE_MASK
                spaces.append(char)
            if category == "Lt":
                flags |= TITLE_MASK
            if "Uppercase" in properties:
                flags |= UPPER_MASK
            if char == ord(" ") or category[0] not in ("C", "Z"):
                flags |= PRINTABLE_MASK
            if "XID_Start" in properties:
                flags |= XID_START_MASK
            if "XID_Continue" in properties:
                flags |= XID_CONTINUE_MASK
            if "Cased" in properties:
                flags |= CASED_MASK
            if "Case_Ignorable" in properties:
                flags |= CASE_IGNORABLE_MASK
            if char in (0x0040, 0x0023, 0x0024, 0x005E):
                flags |= TWITTER_SPECIALS_MASK
            if char == 0x0040:
                flags |= CHAR_AT_MASK
            if char == 0x003A:
                flags |= CHAR_COLON_MASK
            if char == 0x002F:
                flags |= CHAR_SLASH_MASK
            if char == 0x002E:
                flags |= CHAR_PERIOD_MASK
            if char == 0x0027 or char == 0x2019:
                flags |= CHAR_APOS_MASK
            sc = unicode.special_casing.get(char)
            cf = unicode.case_folding.get(char, [char])
            if record[12]:
                upper = int(record[12], 16)
            else:
                upper = char
            if record[13]:
                lower = int(record[13], 16)
            else:
                lower = char
            if record[14]:
                title = int(record[14], 16)
            else:
                title = upper
            if sc is None and cf != [lower]:
                sc = ([lower], [title], [upper])
            if sc is None:
                if upper == lower == title:
                    upper = lower = title = 0
                else:
                    upper = upper - char
                    lower = lower - char
                    title = title - char
                    assert (abs(upper) <= 2147483647 and
                            abs(lower) <= 2147483647 and
                            abs(title) <= 2147483647)
            else:
                # This happens either when some character maps to more than one
                # character in uppercase, lowercase, or titlecase or the
                # casefolded version of the character is different from the
                # lowercase. The extra characters are stored in a different
                # array.
                flags |= EXTENDED_CASE_MASK
                lower = len(extra_casing) | (len(sc[0]) << 24)
                extra_casing.extend(sc[0])
                if cf != sc[0]:
                    lower |= len(cf) << 20
                    extra_casing.extend(cf)
                upper = len(extra_casing) | (len(sc[2]) << 24)
                extra_casing.extend(sc[2])
                # Title is probably equal to upper.
                if sc[1] == sc[2]:
                    title = upper
                else:
                    title = len(extra_casing) | (len(sc[1]) << 24)
                    extra_casing.extend(sc[1])
            # decimal digit, integer digit
            decimal = 0
            if record[6]:
                flags |= DECIMAL_MASK
                decimal = int(record[6])
            digit = 0
            if record[7]:
                flags |= DIGIT_MASK
                digit = int(record[7])
            if record[8]:
                flags |= NUMERIC_MASK
                numeric.setdefault(record[8], []).append(char)
            flags &= DESIZING_MASK  # remove the original "extra high" bit
            item = (
                upper, lower, title, decimal, digit, flags
                )
            # add entry to index and item tables
            i = cache.get(item)
            if i is None:
                cache[item] = i = len(table)
                table.append(item)
            index[char] = i

    print(len(table), "unique character type entries")
    print(sum(map(len, numeric.values())), "numeric code points")
    print(len(spaces), "whitespace code points")
    print(len(linebreaks), "linebreak code points")
    print(len(extra_casing), "extended case array")

    print("--- Writing", FILE, "...")

    fp = open(FILE, "w")
    print("/* this file was generated by ./scripts/unicode/makeunicodedata.py %s */" % (VERSION), file=fp)

    print(file=fp)

    ### If you make a change here, please make sure you make the corresponding change in the python
    ### offsets.py file generation below
    print("#define ALPHA_MASK 0x01", file=fp)
    print("#define DECIMAL_MASK 0x02", file=fp)
    print("#define DIGIT_MASK 0x04", file=fp)
    print("#define LOWER_MASK 0x08", file=fp)
    print("#define LINEBREAK_MASK 0x10", file=fp)
    print("#define SPACE_MASK 0x20", file=fp)
    print("#define TITLE_MASK 0x40", file=fp)
    print("#define UPPER_MASK 0x80", file=fp)
    print("#define XID_START_MASK 0x100", file=fp)
    print("#define XID_CONTINUE_MASK 0x200", file=fp)
    print("#define PRINTABLE_MASK 0x400", file=fp)
    print("#define NUMERIC_MASK 0x800", file=fp)
    print("#define CASE_IGNORABLE_MASK 0x1000", file=fp)
    print("#define CASED_MASK 0x2000", file=fp)
    print("#define EXTENDED_CASE_MASK 0x4000", file=fp)
    print("#define SPECIALS_MASK 0x8000", file=fp)
    print("#define CHAR_AT_MASK 0x010000", file=fp)
    print("#define CHAR_COLON_MASK 0x020000", file=fp)
    print("#define CHAR_SLASH_MASK 0x040000", file=fp)
    print("#define CHAR_PERIOD_MASK 0x080000", file=fp)
    print("#define CHAR_APOS_MASK 0x0100000", file=fp)

    print(file=fp)

    ### If you make a change here, please make sure you make the corresponding change in the python
    ### offsets.py file generation below
    print("#define ALPHA_IDX 0", file=fp)
    print("#define ALPHA_NUM_IDX 1", file=fp)
    print("#define NUM_IDX 2", file=fp)
    print("#define LOWER_IDX 3", file=fp)
    print("#define UPPER_IDX 4", file=fp)
    print("#define SPACE_IDX 5", file=fp)
    print("#define SYMBOL_IDX 6", file=fp)
    print("#define TWITTER_IDX 7", file=fp)
    print("#define CHAR_AT_IDX 8", file=fp)
    print("#define CHAR_COLON_IDX 9", file=fp)
    print("#define CHAR_SLASH_IDX 10", file=fp)
    print("#define CHAR_PERIOD_IDX 11", file=fp)
    print("#define PREV_ALPHA_IDX 12", file=fp)
    print("#define NEXT_ALPHA_IDX 13", file=fp)
    print("#define PREV_ALPHA_NUM_IDX 14", file=fp)
    print("#define NEXT_ALPHA_NUM_IDX 15", file=fp)
    print("#define PREV_LOWER_IDX 16", file=fp)
    print("#define NEXT_LOWER_IDX 17", file=fp)
    print("#define PREV_SPACE_IDX 18", file=fp)
    print("#define NEXT_SPACE_IDX 19", file=fp)
    print("#define PREV_SYMBOL_IDX 20", file=fp)
    print("#define NEXT_AT_IDX 21", file=fp)
    print("#define NEXT_SLASH_IDX 22", file=fp)
    print("#define AFTER_NEXT_ALPHA_IDX 23", file=fp)
    print("#define AFTER_NEXT_SLASH_IDX 24", file=fp)
    print("#define CHAR_APOS_IDX 25", file=fp)
    print("#define FEATURE_COUNT 26", file=fp)


    print(file=fp)
    print("typedef struct {", file=fp)
    print("   /*", file=fp)
    print("      These are either deltas to the character or offsets in", file=fp)
    print("      _TtUnicode_ExtendedCase.", file=fp)
    print("   */", file=fp)
    print("   const int upper;", file=fp)
    print("   const int lower;", file=fp)
    print("   const int title;", file=fp)
    print("   /* Note if more flag space is needed, decimal and digit could be unified. */", file=fp)
    print("   const unsigned char decimal;", file=fp)
    print("   const unsigned char digit;", file=fp)
    print("   const unsigned int flags;", file=fp)
    print("} _TtUnicode_TypeRecord;", file=fp)
    print(file=fp)
    print("/* a list of unique character type descriptors */", file=fp)
    print("const _TtUnicode_TypeRecord _TtUnicode_TypeRecords[] = {", file=fp)
    for item in table:
        print("    {%d, %d, %d, %d, %d, %d}," % item, file=fp)
    print("};", file=fp)
    print(file=fp)

    print("/* extended case mappings */", file=fp)
    print(file=fp)
    print("const Py_UCS4 _TtUnicode_ExtendedCase[] = {", file=fp)
    for c in extra_casing:
        print("    %d," % c, file=fp)
    print("};", file=fp)
    print(file=fp)

    # split decomposition index table
    index1, index2, shift = splitbins(index, trace)

    print("/* type indexes */", file=fp)
    print("#define SHIFT", shift, file=fp)
    Array("index1", index1).dump(fp, trace)
    Array("index2", index2).dump(fp, trace)

    # # Generate code for _PyUnicode_ToNumeric()
    # numeric_items = sorted(numeric.items())
    # print('/* Returns the numeric value as double for Unicode characters', file=fp)
    # print(' * having this property, -1.0 otherwise.', file=fp)
    # print(' */', file=fp)
    # print('double _PyUnicode_ToNumeric(Py_UCS4 ch)', file=fp)
    # print('{', file=fp)
    # print('    switch (ch) {', file=fp)
    # for value, codepoints in numeric_items:
    #     # Turn text into float literals
    #     parts = value.split('/')
    #     parts = [repr(float(part)) for part in parts]
    #     value = '/'.join(parts)
    #
    #     codepoints.sort()
    #     for codepoint in codepoints:
    #         print('    case 0x%04X:' % (codepoint,), file=fp)
    #     print('        return (double) %s;' % (value,), file=fp)
    # print('    }', file=fp)
    # print('    return -1.0;', file=fp)
    # print('}', file=fp)
    # print(file=fp)

    # # Generate code for _PyUnicode_IsWhitespace()
    # print("/* Returns 1 for Unicode characters having the bidirectional", file=fp)
    # print(" * type 'WS', 'B' or 'S' or the category 'Zs', 0 otherwise.", file=fp)
    # print(" */", file=fp)
    # print('int _PyUnicode_IsWhitespace(const Py_UCS4 ch)', file=fp)
    # print('{', file=fp)
    # print('    switch (ch) {', file=fp)
    #
    # for codepoint in sorted(spaces):
    #     print('    case 0x%04X:' % (codepoint,), file=fp)
    # print('        return 1;', file=fp)
    #
    # print('    }', file=fp)
    # print('    return 0;', file=fp)
    # print('}', file=fp)
    # print(file=fp)

    # # Generate code for _PyUnicode_IsLinebreak()
    # print("/* Returns 1 for Unicode characters having the line break", file=fp)
    # print(" * property 'BK', 'CR', 'LF' or 'NL' or having bidirectional", file=fp)
    # print(" * type 'B', 0 otherwise.", file=fp)
    # print(" */", file=fp)
    # print('int _PyUnicode_IsLinebreak(const Py_UCS4 ch)', file=fp)
    # print('{', file=fp)
    # print('    switch (ch) {', file=fp)
    # for codepoint in sorted(linebreaks):
    #     print('    case 0x%04X:' % (codepoint,), file=fp)
    # print('        return 1;', file=fp)
    #
    # print('    }', file=fp)
    # print('    return 0;', file=fp)
    # print('}', file=fp)
    # print(file=fp)

    fp.close()
    
    FILE = "../../latok/core/offsets.py"

    print("--- Preparing", FILE, "...")
    fp = open(FILE, "w")
    print("# this file was generated by ./scripts/unicode/makeunicodedata.py %s" % (VERSION), file=fp)

    print(file=fp)

    ### If you make a change here, please make sure you make the corresponding change in the c
    ### latok.h file generation above
    print("ALPHA_MASK = 0x01", file=fp)
    print("DECIMAL_MASK = 0x02", file=fp)
    print("DIGIT_MASK = 0x04", file=fp)
    print("LOWER_MASK = 0x08", file=fp)
    print("LINEBREAK_MASK = 0x10", file=fp)
    print("SPACE_MASK = 0x20", file=fp)
    print("TITLE_MASK = 0x40", file=fp)
    print("UPPER_MASK = 0x80", file=fp)
    print("XID_START_MASK = 0x100", file=fp)
    print("XID_CONTINUE_MASK = 0x200", file=fp)
    print("PRINTABLE_MASK = 0x400", file=fp)
    print("NUMERIC_MASK = 0x800", file=fp)
    print("CASE_IGNORABLE_MASK = 0x1000", file=fp)
    print("CASED_MASK = 0x2000", file=fp)
    print("EXTENDED_CASE_MASK = 0x4000", file=fp)
    print("SPECIALS_MASK = 0x8000", file=fp)
    print("CHAR_AT_MASK = 0x010000", file=fp)
    print("CHAR_COLON_MASK = 0x020000", file=fp)
    print("CHAR_SLASH_MASK = 0x040000", file=fp)
    print("CHAR_PERIOD_MASK = 0x080000", file=fp)
    print("CHAR_APOS_MASK = 0x0100000", file=fp)

    print(file=fp)

    ### If you make a change here, please make sure you make the corresponding change in the c
    ### latok.h file generation above
    print("ALPHA_IDX = 0", file=fp)
    print("ALPHA_NUM_IDX = 1", file=fp)
    print("NUM_IDX = 2", file=fp)
    print("LOWER_IDX = 3", file=fp)
    print("UPPER_IDX = 4", file=fp)
    print("SPACE_IDX = 5", file=fp)
    print("SYMBOL_IDX = 6", file=fp)
    print("TWITTER_IDX = 7", file=fp)
    print("CHAR_AT_IDX = 8", file=fp)
    print("CHAR_COLON_IDX = 9", file=fp)
    print("CHAR_SLASH_IDX = 10", file=fp)
    print("CHAR_PERIOD_IDX = 11", file=fp)
    print("PREV_ALPHA_IDX = 12", file=fp)
    print("NEXT_ALPHA_IDX = 13", file=fp)
    print("PREV_ALPHA_NUM_IDX = 14", file=fp)
    print("NEXT_ALPHA_NUM_IDX = 15", file=fp)
    print("PREV_LOWER_IDX = 16", file=fp)
    print("NEXT_LOWER_IDX = 17", file=fp)
    print("PREV_SPACE_IDX = 18", file=fp)
    print("NEXT_SPACE_IDX = 19", file=fp)
    print("PREV_SYMBOL_IDX = 20", file=fp)
    print("NEXT_AT_IDX = 21", file=fp)
    print("NEXT_SLASH_IDX = 22", file=fp)
    print("AFTER_NEXT_ALPHA_IDX = 23", file=fp)
    print("AFTER_NEXT_SLASH_IDX = 24", file=fp)
    print("CHAR_APOS_IDX = 25", file=fp)
    print("FEATURE_COUNT = 26", file=fp)
    print(file=fp)
    fp.close()


def merge_old_version(version, new, old):
    # Changes to exclusion file not implemented yet
    if old.exclusions != new.exclusions:
        raise NotImplementedError("exclusions differ")

    # In these change records, 0xFF means "no change"
    bidir_changes = [0xFF]*0x110000
    category_changes = [0xFF]*0x110000
    decimal_changes = [0xFF]*0x110000
    mirrored_changes = [0xFF]*0x110000
    east_asian_width_changes = [0xFF]*0x110000
    # In numeric data, 0 means "no change",
    # -1 means "did not have a numeric value
    numeric_changes = [0] * 0x110000
    # normalization_changes is a list of key-value pairs
    normalization_changes = []
    for i in range(0x110000):
        if new.table[i] is None:
            # Characters unassigned in the new version ought to
            # be unassigned in the old one
            assert old.table[i] is None
            continue
        # check characters unassigned in the old version
        if old.table[i] is None:
            # category 0 is "unassigned"
            category_changes[i] = 0
            continue
        # check characters that differ
        if old.table[i] != new.table[i]:
            for k in range(len(old.table[i])):
                if old.table[i][k] != new.table[i][k]:
                    value = old.table[i][k]
                    if k == 1 and i in PUA_15:
                        # the name is not set in the old.table, but in the
                        # new.table we are using it for aliases and named seq
                        assert value == ''
                    elif k == 2:
                        #print "CATEGORY",hex(i), old.table[i][k], new.table[i][k]
                        category_changes[i] = CATEGORY_NAMES.index(value)
                    elif k == 4:
                        #print "BIDIR",hex(i), old.table[i][k], new.table[i][k]
                        bidir_changes[i] = BIDIRECTIONAL_NAMES.index(value)
                    elif k == 5:
                        #print "DECOMP",hex(i), old.table[i][k], new.table[i][k]
                        # We assume that all normalization changes are in 1:1 mappings
                        assert " " not in value
                        normalization_changes.append((i, value))
                    elif k == 6:
                        #print "DECIMAL",hex(i), old.table[i][k], new.table[i][k]
                        # we only support changes where the old value is a single digit
                        assert value in "0123456789"
                        decimal_changes[i] = int(value)
                    elif k == 8:
                        # print "NUMERIC",hex(i), `old.table[i][k]`, new.table[i][k]
                        # Since 0 encodes "no change", the old value is better not 0
                        if not value:
                            numeric_changes[i] = -1
                        else:
                            numeric_changes[i] = float(value)
                            assert numeric_changes[i] not in (0, -1)
                    elif k == 9:
                        if value == 'Y':
                            mirrored_changes[i] = '1'
                        else:
                            mirrored_changes[i] = '0'
                    elif k == 11:
                        # change to ISO comment, ignore
                        pass
                    elif k == 12:
                        # change to simple uppercase mapping; ignore
                        pass
                    elif k == 13:
                        # change to simple lowercase mapping; ignore
                        pass
                    elif k == 14:
                        # change to simple titlecase mapping; ignore
                        pass
                    elif k == 15:
                        # change to east asian width
                        east_asian_width_changes[i] = EASTASIANWIDTH_NAMES.index(value)
                    elif k == 16:
                        # derived property changes; not yet
                        pass
                    elif k == 17:
                        # normalization quickchecks are not performed
                        # for older versions
                        pass
                    else:
                        class Difference(Exception):pass
                        raise Difference(hex(i), k, old.table[i], new.table[i])
    new.changed.append((version, list(zip(bidir_changes, category_changes,
                                          decimal_changes, mirrored_changes,
                                          east_asian_width_changes,
                                          numeric_changes)),
                        normalization_changes))

def open_data(template, version):
    local = template % ('-'+version,)
    if not os.path.exists(local):
        import urllib.request
        if version == '3.2.0':
            # irregular url structure
            url = 'http://www.unicode.org/Public/3.2-Update/' + local
        else:
            url = ('http://www.unicode.org/Public/%s/ucd/'+template) % (version, '')
        urllib.request.urlretrieve(url, filename=local)
    if local.endswith('.txt'):
        return open(local, encoding='utf-8')
    else:
        # Unihan.zip
        return open(local, 'rb')

# --------------------------------------------------------------------
# the following support code is taken from the unidb utilities
# Copyright (c) 1999-2000 by Secret Labs AB

# load a unicode-data file from disk

class UnicodeData:
    # Record structure:
    # [ID, name, category, combining, bidi, decomp,  (6)
    #  decimal, digit, numeric, bidi-mirrored, Unicode-1-name, (11)
    #  ISO-comment, uppercase, lowercase, titlecase, ea-width, (16)
    #  derived-props] (17)

    def __init__(self, version,
                 linebreakprops=False,
                 expand=1,
                 cjk_check=True):
        self.changed = []
        table = [None] * 0x110000
        with open_data(UNICODE_DATA, version) as file:
            while 1:
                s = file.readline()
                if not s:
                    break
                s = s.strip().split(";")
                char = int(s[0], 16)
                table[char] = s

        cjk_ranges_found = []

        # expand first-last ranges
        if expand:
            field = None
            for i in range(0, 0x110000):
                s = table[i]
                if s:
                    if s[1][-6:] == "First>":
                        s[1] = ""
                        field = s
                    elif s[1][-5:] == "Last>":
                        if s[1].startswith("<CJK Ideograph"):
                            cjk_ranges_found.append((field[0],
                                                     s[0]))
                        s[1] = ""
                        field = None
                elif field:
                    f2 = field[:]
                    f2[0] = "%X" % i
                    table[i] = f2
            if cjk_check and cjk_ranges != cjk_ranges_found:
                raise ValueError("CJK ranges deviate: have %r" % cjk_ranges_found)

        # public attributes
        self.filename = UNICODE_DATA % ''
        self.table = table
        self.chars = list(range(0x110000)) # unicode 3.2

        # check for name aliases and named sequences, see #12753
        # aliases and named sequences are not in 3.2.0
        if version != '3.2.0':
            self.aliases = []
            # store aliases in the Private Use Area 15, in range U+F0000..U+F00FF,
            # in order to take advantage of the compression and lookup
            # algorithms used for the other characters
            pua_index = NAME_ALIASES_START
            with open_data(NAME_ALIASES, version) as file:
                for s in file:
                    s = s.strip()
                    if not s or s.startswith('#'):
                        continue
                    char, name, abbrev = s.split(';')
                    char = int(char, 16)
                    self.aliases.append((name, char))
                    # also store the name in the PUA 1
                    self.table[pua_index][1] = name
                    pua_index += 1
            assert pua_index - NAME_ALIASES_START == len(self.aliases)

            self.named_sequences = []
            # store named sequences in the PUA 1, in range U+F0100..,
            # in order to take advantage of the compression and lookup
            # algorithms used for the other characters.

            assert pua_index < NAMED_SEQUENCES_START
            pua_index = NAMED_SEQUENCES_START
            with open_data(NAMED_SEQUENCES, version) as file:
                for s in file:
                    s = s.strip()
                    if not s or s.startswith('#'):
                        continue
                    name, chars = s.split(';')
                    chars = tuple(int(char, 16) for char in chars.split())
                    # check that the structure defined in makeunicodename is OK
                    assert 2 <= len(chars) <= 4, "change the Py_UCS2 array size"
                    assert all(c <= 0xFFFF for c in chars), ("use Py_UCS4 in "
                        "the NamedSequence struct and in unicodedata_lookup")
                    self.named_sequences.append((name, chars))
                    # also store these in the PUA 1
                    self.table[pua_index][1] = name
                    pua_index += 1
            assert pua_index - NAMED_SEQUENCES_START == len(self.named_sequences)

        self.exclusions = {}
        with open_data(COMPOSITION_EXCLUSIONS, version) as file:
            for s in file:
                s = s.strip()
                if not s:
                    continue
                if s[0] == '#':
                    continue
                char = int(s.split()[0],16)
                self.exclusions[char] = 1

        widths = [None] * 0x110000
        with open_data(EASTASIAN_WIDTH, version) as file:
            for s in file:
                s = s.strip()
                if not s:
                    continue
                if s[0] == '#':
                    continue
                s = s.split()[0].split(';')
                if '..' in s[0]:
                    first, last = [int(c, 16) for c in s[0].split('..')]
                    chars = list(range(first, last+1))
                else:
                    chars = [int(s[0], 16)]
                for char in chars:
                    widths[char] = s[1]

        for i in range(0, 0x110000):
            if table[i] is not None:
                table[i].append(widths[i])

        for i in range(0, 0x110000):
            if table[i] is not None:
                table[i].append(set())

        with open_data(DERIVED_CORE_PROPERTIES, version) as file:
            for s in file:
                s = s.split('#', 1)[0].strip()
                if not s:
                    continue

                r, p = s.split(";")
                r = r.strip()
                p = p.strip()
                if ".." in r:
                    first, last = [int(c, 16) for c in r.split('..')]
                    chars = list(range(first, last+1))
                else:
                    chars = [int(r, 16)]
                for char in chars:
                    if table[char]:
                        # Some properties (e.g. Default_Ignorable_Code_Point)
                        # apply to unassigned code points; ignore them
                        table[char][-1].add(p)

        with open_data(LINE_BREAK, version) as file:
            for s in file:
                s = s.partition('#')[0]
                s = [i.strip() for i in s.split(';')]
                if len(s) < 2 or s[1] not in MANDATORY_LINE_BREAKS:
                    continue
                if '..' not in s[0]:
                    first = last = int(s[0], 16)
                else:
                    first, last = [int(c, 16) for c in s[0].split('..')]
                for char in range(first, last+1):
                    table[char][-1].add('Line_Break')

        # We only want the quickcheck properties
        # Format: NF?_QC; Y(es)/N(o)/M(aybe)
        # Yes is the default, hence only N and M occur
        # In 3.2.0, the format was different (NF?_NO)
        # The parsing will incorrectly determine these as
        # "yes", however, unicodedata.c will not perform quickchecks
        # for older versions, and no delta records will be created.
        quickchecks = [0] * 0x110000
        qc_order = 'NFD_QC NFKD_QC NFC_QC NFKC_QC'.split()
        with open_data(DERIVEDNORMALIZATION_PROPS, version) as file:
            for s in file:
                if '#' in s:
                    s = s[:s.index('#')]
                s = [i.strip() for i in s.split(';')]
                if len(s) < 2 or s[1] not in qc_order:
                    continue
                quickcheck = 'MN'.index(s[2]) + 1 # Maybe or No
                quickcheck_shift = qc_order.index(s[1])*2
                quickcheck <<= quickcheck_shift
                if '..' not in s[0]:
                    first = last = int(s[0], 16)
                else:
                    first, last = [int(c, 16) for c in s[0].split('..')]
                for char in range(first, last+1):
                    assert not (quickchecks[char]>>quickcheck_shift)&3
                    quickchecks[char] |= quickcheck
        for i in range(0, 0x110000):
            if table[i] is not None:
                table[i].append(quickchecks[i])

        with open_data(UNIHAN, version) as file:
            zip = zipfile.ZipFile(file)
            if version == '3.2.0':
                data = zip.open('Unihan-3.2.0.txt').read()
            else:
                data = zip.open('Unihan_NumericValues.txt').read()
        for line in data.decode("utf-8").splitlines():
            if not line.startswith('U+'):
                continue
            code, tag, value = line.split(None, 3)[:3]
            if tag not in ('kAccountingNumeric', 'kPrimaryNumeric',
                           'kOtherNumeric'):
                continue
            value = value.strip().replace(',', '')
            i = int(code[2:], 16)
            # Patch the numeric field
            if table[i] is not None:
                table[i][8] = value
        sc = self.special_casing = {}
        with open_data(SPECIAL_CASING, version) as file:
            for s in file:
                s = s[:-1].split('#', 1)[0]
                if not s:
                    continue
                data = s.split("; ")
                if data[4]:
                    # We ignore all conditionals (since they depend on
                    # languages) except for one, which is hardcoded. See
                    # handle_capital_sigma in unicodeobject.c.
                    continue
                c = int(data[0], 16)
                lower = [int(char, 16) for char in data[1].split()]
                title = [int(char, 16) for char in data[2].split()]
                upper = [int(char, 16) for char in data[3].split()]
                sc[c] = (lower, title, upper)
        cf = self.case_folding = {}
        if version != '3.2.0':
            with open_data(CASE_FOLDING, version) as file:
                for s in file:
                    s = s[:-1].split('#', 1)[0]
                    if not s:
                        continue
                    data = s.split("; ")
                    if data[1] in "CF":
                        c = int(data[0], 16)
                        cf[c] = [int(char, 16) for char in data[2].split()]

    def uselatin1(self):
        # restrict character range to ISO Latin 1
        self.chars = list(range(256))

# hash table tools

# this is a straight-forward reimplementation of Python's built-in
# dictionary type, using a static data structure, and a custom string
# hash algorithm.

def myhash(s, magic):
    h = 0
    for c in map(ord, s.upper()):
        h = (h * magic) + c
        ix = h & 0xff000000
        if ix:
            h = (h ^ ((ix>>24) & 0xff)) & 0x00ffffff
    return h

SIZES = [
    (4,3), (8,3), (16,3), (32,5), (64,3), (128,3), (256,29), (512,17),
    (1024,9), (2048,5), (4096,83), (8192,27), (16384,43), (32768,3),
    (65536,45), (131072,9), (262144,39), (524288,39), (1048576,9),
    (2097152,5), (4194304,3), (8388608,33), (16777216,27)
]

class Hash:
    def __init__(self, name, data, magic):
        # turn a (key, value) list into a static hash table structure

        # determine table size
        for size, poly in SIZES:
            if size > len(data):
                poly = size + poly
                break
        else:
            raise AssertionError("ran out of polynomials")

        print(size, "slots in hash table")

        table = [None] * size

        mask = size-1

        n = 0

        hash = myhash

        # initialize hash table
        for key, value in data:
            h = hash(key, magic)
            i = (~h) & mask
            v = table[i]
            if v is None:
                table[i] = value
                continue
            incr = (h ^ (h >> 3)) & mask;
            if not incr:
                incr = mask
            while 1:
                n = n + 1
                i = (i + incr) & mask
                v = table[i]
                if v is None:
                    table[i] = value
                    break
                incr = incr << 1
                if incr > mask:
                    incr = incr ^ poly

        print(n, "collisions")
        self.collisions = n

        for i in range(len(table)):
            if table[i] is None:
                table[i] = 0

        self.data = Array(name + "_hash", table)
        self.magic = magic
        self.name = name
        self.size = size
        self.poly = poly

    def dump(self, file, trace):
        # write data to file, as a C array
        self.data.dump(file, trace)
        file.write("#define %s_magic %d\n" % (self.name, self.magic))
        file.write("#define %s_size %d\n" % (self.name, self.size))
        file.write("#define %s_poly %d\n" % (self.name, self.poly))

# stuff to deal with arrays of unsigned integers

class Array:

    def __init__(self, name, data):
        self.name = name
        self.data = data

    def dump(self, file, trace=0):
        # write data to file, as a C array
        size = getsize(self.data)
        if trace:
            print(self.name+":", size*len(self.data), "bytes", file=sys.stderr)
        file.write("static ")
        if size == 1:
            file.write("unsigned char")
        elif size == 2:
            file.write("unsigned short")
        else:
            file.write("unsigned int")
        file.write(" " + self.name + "[] = {\n")
        if self.data:
            s = "    "
            for item in self.data:
                i = str(item) + ", "
                if len(s) + len(i) > 78:
                    file.write(s.rstrip() + "\n")
                    s = "    " + i
                else:
                    s = s + i
            if s.strip():
                file.write(s.rstrip() + "\n")
        file.write("};\n\n")

def getsize(data):
    # return smallest possible integer size for the given array
    maxdata = max(data)
    if maxdata < 256:
        return 1
    elif maxdata < 65536:
        return 2
    else:
        return 4

def splitbins(t, trace=0):
    """t, trace=0 -> (t1, t2, shift).  Split a table to save space.

    t is a sequence of ints.  This function can be useful to save space if
    many of the ints are the same.  t1 and t2 are lists of ints, and shift
    is an int, chosen to minimize the combined size of t1 and t2 (in C
    code), and where for each i in range(len(t)),
        t[i] == t2[(t1[i >> shift] << shift) + (i & mask)]
    where mask is a bitmask isolating the last "shift" bits.

    If optional arg trace is non-zero (default zero), progress info
    is printed to sys.stderr.  The higher the value, the more info
    you'll get.
    """

    if trace:
        def dump(t1, t2, shift, bytes):
            print("%d+%d bins at shift %d; %d bytes" % (
                len(t1), len(t2), shift, bytes), file=sys.stderr)
        print("Size of original table:", len(t)*getsize(t), \
                            "bytes", file=sys.stderr)
    n = len(t)-1    # last valid index
    maxshift = 0    # the most we can shift n and still have something left
    if n > 0:
        while n >> 1:
            n >>= 1
            maxshift += 1
    del n
    bytes = sys.maxsize  # smallest total size so far
    t = tuple(t)    # so slices can be dict keys
    for shift in range(maxshift + 1):
        t1 = []
        t2 = []
        size = 2**shift
        bincache = {}
        for i in range(0, len(t), size):
            bin = t[i:i+size]
            index = bincache.get(bin)
            if index is None:
                index = len(t2)
                bincache[bin] = index
                t2.extend(bin)
            t1.append(index >> shift)
        # determine memory size
        b = len(t1)*getsize(t1) + len(t2)*getsize(t2)
        if trace > 1:
            dump(t1, t2, shift, b)
        if b < bytes:
            best = t1, t2, shift
            bytes = b
    t1, t2, shift = best
    if trace:
        print("Best:", end=' ', file=sys.stderr)
        dump(t1, t2, shift, bytes)
    if __debug__:
        # exhaustively verify that the decomposition is correct
        mask = ~((~0) << shift) # i.e., low-bit mask of shift bits
        for i in range(len(t)):
            assert t[i] == t2[(t1[i >> shift] << shift) + (i & mask)]
    return best

if __name__ == "__main__":
    maketables(1)
    # This is a test of the power mode

