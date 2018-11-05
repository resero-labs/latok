import numpy as np


def genmask(a1, a2):
    '''
    Given two aligning arrays of 1's and 0's,
    generate a mask of ones with zeros between a2 1's where a1 has a 1
    '''
    result = np.ones(len(a2), dtype=np.int32)
    a1_nz = np.flatnonzero(a1)
    if len(a1_nz) == 0:
        return result
    a2_nz = np.flatnonzero(a2)
    idx1 = 0
    val1 = a1_nz[idx1]
    prev_val2 = 0
    for val2 in a2_nz:
        if val2 >= val1:
            result[prev_val2+1:val2] = 0
            idx1 += 1
            if idx1 >= len(a1_nz):
                break
            val1 = a1_nz[idx1]
        prev_val2 = val2
    return result


class NumpyTokenizer:

    def __init__(self, text):
        # create a matrix of text where rows are individual characters and columns are the features ([0, 1])
        self.text = text
        self.twitter_specials = set('#@$^')

        nchars = len(text)

        chars = np.zeros(nchars+1, dtype=np.str)

        # ord, alnum, alpha, numeric, lower, upper, space
        num_character_features = 7

        # added features:
        # symbols, twitter_specials, atset, colon, forward_slash, period
        num_added_features = 6

        # rolled features
        num_rolled_features = 13

        tot_feature_count = num_character_features + num_added_features + num_rolled_features

        a = np.zeros((nchars + 1, tot_feature_count), dtype=np.int32)

        prev_row = pprev_row = a[-1]
        next_row = a[0]
        idx = 0
        for c in text:
            row = next_row
            next_row = a[idx+1]
            self._update_feature_array(row, prev_row, pprev_row, next_row, c, idx, chars)
            pprev_row = prev_row
            prev_row = row
            idx += 1

        # add sp to end of string for rolling
        last_row = a[nchars]
        last_row[6] = 1
        #last_row[0] = 32
        a[nchars-1][24] = 1  # before_white: roll space
        chars[nchars] = ' '

        # Transpose for more efficient row access
        self.a = a.T
        self.chars = chars
        self.nchars = nchars

    def _update_feature_array(self, row, prev_row, pprev_row, next_row, c, idx, chars):
        #row = a[idx]
        #prev_row = a[idx-1]
        #if idx == 0:
        #    pprev_row = a[-1]
        #else:
        #    pprev_row = a[idx-2]
        #next_row = a[idx+1]

        # character features
        ##o = ord(c)
        #an = c.isalnum()
        #al = c.isalpha()
        #n = c.isnumeric()
        #l = c.islower()
        #u = c.isupper()
        #sp = c.isspace()
        an = al = n = l = u = sp = sym = False
        if c.isalpha():
            al = an = True
            if c.islower():
                l = True
            else:
                u = True
        elif c.isnumeric():
            n = an = True
        elif c.isspace():
            sp = True
        else:
            sym = True
            

        #sym = (not an and not sp)
        chars[idx] = c if not sp else ' '  # convert all whitespace to ' '
        ##row[0] = o                        # but don't lose original ord
        #row[1] = an
        #row[2] = al
        #row[3] = n
        #row[4] = l
        #row[5] = u
        #row[6] = sp
        if an:
            row[1] = 1
            next_row[19] = 1
            prev_row[20] = 1
        if al:
            row[2] = 1
            prev_row[16] = 1
            pprev_row[18] = 1
            next_row[23] = 1
        if n:
            row[3] = 1
        if l:
            row[4] = 1
            prev_row[14] = 1
            next_row[15] = 1
        if u:
            row[5] = 1
        if sp:
            row[6] = 1
            next_row[13] = 1
            prev_row[24] = 1
            
        # added features
        if sym:
            row[7] = 1
            next_row[25] = 1
            #row[8] = (c in self.twitter_specials)
            #row[9] = (c == '@')
            #row[10] = (c == ':')
            #row[11] = (c == '/')
            #row[12] = (c == '.')
            if (c in self.twitter_specials):
                row[8] = 1
            if (c == '@'):
                row[9] = 1
                prev_row[17] = 1
            if (c == ':'):
                row[10] = 1
            if (c == '/'):
                row[11] = 1
                prev_row[21] = 1
                pprev_row[22] = 1
            if (c == '.'):
                row[12] = 1
        
        # rolled features
        #next_row[13] = sp          # after_white
        #prev_row[14] = l           # before_lower
        #next_row[15] = l           # after_lower
        #prev_row[16] = al          # before_alpha
        #prev_row[17] = (c == '@')  # before_atset
        #pprev_row[18] = al         # two_before_alpha
        #next_row[19] = an          # after_alnum
        #prev_row[20] = an          # before_alnum
        #prev_row[21] = (c == '/')  # before_slash
        #pprev_row[22] = (c == '/') # two_before_slash
        #next_row[23] = al          # after_alpha
        #prev_row[24] = sp          # before_white
        #next_row[25] = sym         # after_symbols

    def tokenize(self):
        a = self.a

        whitespace = a[6]
        ##alnum = a[1]
        ##alpha = a[2]
        uppercase = a[5]
        ##lowercase = a[4]
        symbols = a[7]
        #twitter_specials = a[8]
        #atset = a[9]
        #colon = a[10]
        #slash = a[11]
        #dot = a[12]

        after_white = a[13]  # np.roll(whitespace, 1)
        #before_lower = a[14]  # np.roll(lowercase, -1)
        #after_lower = a[15]  # np.roll(lowercase, 1)
        #before_alpha = a[16]  # np.roll(alpha, -1)
        #before_atset = a[17]  # np.roll(atset, -1)
        #two_before_alpha = a[18]  # np.roll(alpha, -2)
        #after_alnum = a[19]  # np.roll(alnum, 1)
        #before_alnum = a[20]  # np.roll(alnum, -1)
        #before_slash = a[21]  # np.roll(slash, -1)
        #two_before_slash = a[22]  # np.roll(slash, -2)
        #after_alpha = a[23]  # np.roll(alpha, 1)
        #before_white = a[24]  # np.roll(whitespace, -1)
        #after_symbols = a[25]  # np.roll(symbols, 1)

        #camelcase_lower_before_cap = (uppercase & before_lower)
        #camelcase_cap_after_lower = (uppercase & after_lower)
        #twitter_start = (
        #    # twitter special after whitespace and before alpha
        #    (twitter_specials & after_white & before_alpha) +
        #
        #    # account for '.@' as well: dot after whitespace before atset + alpha
        #    (dot & after_white & before_atset & two_before_alpha)
        #)
        #twitter_start = twitter_specials * after_white
        twitter_start = a[8] * after_white
        #twitter_start *= before_alpha
        twitter_start *= a[16]
        #tmp1 = dot * after_white
        tmp1 = a[12] * after_white
        #tmp1 *= before_atset
        tmp1 *= a[17]
        #tmp1 *= two_before_alpha
        tmp1 *= a[18]
        twitter_start += tmp1

        #email_start = (atset & after_alnum & before_alnum)
        #email_start = atset * after_alnum
        email_start = a[9] * a[19]
        #email_start *= before_alnum
        email_start *= a[20]
        #url_start = (colon & before_slash & two_before_slash & after_alpha)
        #url_start = colon * before_slash
        url_start = a[10] * a[21]
        #url_start *= two_before_slash
        url_start *= a[22]
        #url_start *= after_alpha
        url_start *= a[23]

        # split on whitespace, symbols and camelcase
        #splits = (
        #    whitespace + symbols +
        #    (uppercase & before_lower) +  # camelcase_lower_before_cap +
        #    (uppercase & after_lower)     # camelcase_cap_after_lower
        #)
        #splits = uppercase * before_lower
        splits = uppercase * a[14]
        #splits += uppercase * after_lower
        splits += uppercase * a[15]
        splits += whitespace
        splits += symbols
        splits += a[25]  # after_symbols  # np.roll(symbols, 1)

        # apply block masks for twitter specials, emails, urls
        #tw_mask = genmask(twitter_start, whitespace)   # twitter specials mask
        #email_mask = genmask(email_start, whitespace)  # email mask
        #url_mask = genmask(url_start, whitespace)      # url mask
        #splits = (splits & tw_mask & email_mask & url_mask)
        #splits &= genmask(twitter_start + email_start + url_start, whitespace)
        masks = twitter_start + email_start
        masks += url_start
        splits *= genmask(masks, whitespace)

        # todo: account for quotes and parentheses

        # apply trailing symbol splits after block masks
        #splits += (symbols * before_white)  # trailing symbol
        splits += (symbols * a[24])  # trailing symbol
        # todo: account for valid trailing chars in urls '/#'

        self.splits = splits

    def split(self):
        result = list()
        for b in np.hsplit(self.chars,
                           np.flatnonzero(
                               self.splits
                           )):
            z = ''.join(c for c in b if c != ' ')
            if z:
                result.append(z)
        return result


if __name__ == "__main__":
    tokenizer = NumpyTokenizer("This is a #test! Testing, Testing, 1 2 3")
    tokenizer.tokenize()
    print(tokenizer.splits)
    print(tokenizer.split())
