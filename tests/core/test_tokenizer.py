import sys
import latok.core.constants as C
import latok.core.general_cores as general_cores
import latok.core.split_mask_generator as split_mask_generator
import latok.core.tokenizer as tokenizer
import latok.core.twitter_cores as twitter_cores


def do_split_test(splitter, texts, expectations, verify=True):
    for idx, text in enumerate(texts):
        expected_tokens = expectations[idx] if verify else None
        tokens = list(splitter.split(text))
        if verify:
            assert tokens == expected_tokens
        else:
            print(f'# {idx}: {text}"\n\t{tokens},', file=sys.stderr)
    if not verify:
        # Fail so we get the output
        assert True == False


def do_tokenization_test(
        tokenizer, texts, tokenized_expectations, tokens_text_expectations,
        disable_abstract_features=False, specs_and_repls_overrides=None,
        to_lower_override=None, drop_symbols_override=None,
        keep_emojis_override=None, verify=True):
    for idx, text in enumerate(texts):
        expected_tokenized = tokenized_expectations[idx] if verify else None
        tokenized = list(tokenizer.tokenize(
            text, disable_abstract_features=disable_abstract_features,
            specs_and_repls_overrides=specs_and_repls_overrides,
            to_lower_override=to_lower_override,
            drop_symbols_override=drop_symbols_override,
            keep_emojis_override=keep_emojis_override))
        if verify:
            assert tokenized == expected_tokenized
        else:
            print(f'# (tokens) {idx}: "{text}"\n\t{tokenized},', file=sys.stderr)
    for idx, text in enumerate(texts):
        expected_tokens_text = tokens_text_expectations[idx] if verify else None
        tokens = [
            t.text
            for t in tokenizer.featurize(
                    text, disable_abstract_features=disable_abstract_features,
                    specs_and_repls_overrides=specs_and_repls_overrides)
        ]
        if verify:
            assert tokens == expected_tokens_text
        else:
            print(f'# (features) {idx}: "{text}"\n\t{tokens},', file=sys.stderr)
    if not verify:
        # Fail so we get the output
        assert True == False


TEST_TEXTS = [
    '',
    ' ',
    '.',
    ' . ',
    'test',
    'test!',
    'CamelCase and camelCase!',
    '@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser',
    '@123.456',
    '"@123.456"',
    "#HashTag's",
    '''"#HashTag's"''',
    '''"It's problematic"''',
    '''@123.456 #HashTag's "It's a problem"''',
    '''@AbcDef #HashTag "It isn't a problem"''',
    '''@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce"''',
    '''@SomeUser and ("@SomeMention")''',
    '''@Some_Mention''',
    '''This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78''',
]


def test_default_simple_splitter():
    splitter = tokenizer.Splitter(split_mask_generator.SIMPLE_SMG)
    do_split_test(
        splitter, TEST_TEXTS, [
            # 0: "
	    [],
            # 1:  "
	    [],
            # 2: ."
	    ['.'],
            # 3:  . "
	    ['.'],
            # 4: test"
	    ['test'],
            # 5: test!"
	    ['test', '!'],
            # 6: CamelCase and camelCase!"
	    ['CamelCase', 'and', 'camelCase', '!'],
            # 7: @TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['@', 'TwitterUser', 'Hey', 'foo', '@', 'bar', '.', 'com', '!', '#',
             'ParseTweets', 'http', ':', '/', '/', 'foobar', '.', 'com', '/',
             'tweet', '_', 'parser'],
            # 8: @123.456"
	    ['@', '123', '.', '456'],
            # 9: "@123.456""
	    ['"', '@', '123', '.', '456', '"'],
            # 10: #HashTag's"
	    ['#', 'HashTag', "'", 's'],
            # 11: "#HashTag's""
	    ['"', '#', 'HashTag', "'", 's', '"'],
            # 12: "It's problematic""
	    ['"', 'It', "'", 's', 'problematic', '"'],
            # 13: @123.456 #HashTag's "It's a problem""
	    ['@', '123', '.', '456', '#', 'HashTag', "'", 's', '"', 'It', "'",
             's', 'a', 'problem', '"'],
            # 14: @AbcDef #HashTag "It isn't a problem""
	    ['@', 'AbcDef', '#', 'HashTag', '"', 'It', 'isn', "'", 't', 'a',
             'problem', '"'],
            # 15: @SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
	    ['@', 'SomeUser', 'and', '"', '@', 'AnotherMention', '"', 'see',
             '"', 'http', ':', '/', '/', 'foobar', '.', 'baz', '/', 'entry',
             '"', 'and', 'tell', '"', 'user', '@', 'foo', '.', 'com', '"',
             'about', 'your', '"', '"', '#', 'AwesomeSauce', '"'],
            # 16: @SomeUser and ("@SomeMention")"
	    ['@', 'SomeUser', 'and', '(', '"', '@', 'SomeMention', '"', ')'],
            # 17: @Some_Mention"
	    ['@', 'Some', '_', 'Mention'],
            # 18: This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', 'a1', 'test', 'don', "'", 't', 'http', ':', '/',
             '/', 'foo', '.', 'com', '?', 'bar', '=', '123', '@', 'user',
             'abc', '@', 'xyz', '.', 'com', 'camelCaseOne', ',',
             'CamelCaseTwo', ',', 'camelCase1', ',', 'CamelCase2', ',', '123',
             '$', '123', ',', '456', '.', '78'],
        ])
    

def test_default_general_splitter():
    smg = general_cores.build_general_split_mask_generator()
    splitter = tokenizer.Splitter(smg)
    do_split_test(
        splitter, TEST_TEXTS, [
            # 0: "
	    [],
            # 1:  "
	    [],
            # 2: ."
	    ['.'],
            # 3:  . "
	    ['.'],
            # 4: test"
	    ['test'],
            # 5: test!"
	    ['test', '!'],
            # 6: CamelCase and camelCase!"
	    ['Camel', 'Case', 'and', 'camel', 'Case', '!'],
            # 7: @TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['@', 'Twitter', 'User', 'Hey', 'foo@bar.com', '!', '#', 'Parse',
             'Tweets', 'http://foobar.com/tweet_parser'],
            # 8: @123.456"
	    ['@123.456'],
            # 9: "@123.456""
	    ['"', '@123.456', '"'],
            # 10: #HashTag's"
	    ["#HashTag's"],
            # 11: "#HashTag's""
	    ['"', '#', "HashTag's", '"'],
            # 12: "It's problematic""
	    ['"It\'s', 'problematic', '"'],
            # 13: @123.456 #HashTag's "It's a problem""
	    ['@123.456', '#', "HashTag's", '"', "It's", 'a', 'problem', '"'],
            # 14: @AbcDef #HashTag "It isn't a problem""
	    ['@', 'Abc', 'Def', '#', 'Hash', 'Tag', '"', 'It', "isn't", 'a',
             'problem', '"'],
            # 15: @SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
            # *** TODO: Fix trimming double-quote in front of URL and E-MAIL ***
	    ['@', 'Some', 'User', 'and', '"', '@', 'Another', 'Mention', '"',
             'see', '"http://foobar.baz/entry', '"', 'and', 'tell',
             '"user@foo.com', '"', 'about', 'your', '"', '"', '#',
             'Awesome', 'Sauce', '"'],
            # 16: @SomeUser and ("@SomeMention")"
	    ['@', 'Some', 'User', 'and', '(', '"', '@', 'Some', 'Mention',
             '"', ')'],
            # 17: @Some_Mention"
	    ['@', 'Some', '_', 'Mention'],
            # 18: This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', 'a1', 'test', "don't", 'http://foo.com?bar=123',
             '@', 'user', 'abc@xyz.com', 'camel', 'Case', 'One', ',', 'Camel',
             'Case', 'Two', ',', 'camelCase1', ',', 'CamelCase2', ',', '123',
             '$123,456.78'],
        ])
    

def test_modified_general_tokenizer():
    smg = general_cores.build_general_split_mask_generator()
    tok = tokenizer.Tokenizer(
        smg=smg,
        specs_and_repls=[
            (C.EMAIL_FEATURE, '_EMAIL'),
            (C.URL_FEATURE, '_URL'),
            (C.NUMERIC_FEATURE, '_NUM'),
        ],
        to_lower=True,
        drop_symbols=True,
        keep_emojis=False
    )
    do_tokenization_test(
        tok, TEST_TEXTS, [
            # (tokens) 0: ""
	    [],
            # (tokens) 1: " "
	    [],
            # (tokens) 2: "."
	    [],
            # (tokens) 3: " . "
	    [],
            # (tokens) 4: "test"
	    ['test'],
            # (tokens) 5: "test!"
	    ['test'],
            # (tokens) 6: "CamelCase and camelCase!"
	    ['camel', 'case', 'and', 'camel', 'case'],
            # (tokens) 7: "@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['twitter', 'user', 'hey', '_EMAIL', 'parse', 'tweets', '_URL'],
            # (tokens) 8: "@123.456"
	    ['_NUM'],
            # (tokens) 9: ""@123.456""
	    ['_NUM'],
            # (tokens) 10: "#HashTag's"
	    ["#hashtag's"],
            # (tokens) 11: ""#HashTag's""
	    ["hashtag's"],
            # (tokens) 12: ""It's problematic""
	    ['"it\'s', 'problematic'],
            # (tokens) 13: "@123.456 #HashTag's "It's a problem""
	    ['_NUM', "hashtag's", "it's", 'a', 'problem'],
            # (tokens) 14: "@AbcDef #HashTag "It isn't a problem""
	    ['abc', 'def', 'hash', 'tag', 'it', "isn't", 'a', 'problem'],
            # (tokens) 15: "@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
	    ['some', 'user', 'and', 'another', 'mention', 'see', '_URL', 'and',
             'tell', '_EMAIL', 'about', 'your', 'awesome', 'sauce'],
            # (tokens) 16: "@SomeUser and ("@SomeMention")"
	    ['some', 'user', 'and', 'some', 'mention'],
            # (tokens) 17: "@Some_Mention"
	    ['some', 'mention'],
            # (tokens) 18: "This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['this', 'is', '_NUM', 'test', "don't", '_URL', 'user', '_EMAIL',
             'camel', 'case', 'one', 'camel', 'case', 'two', '_NUM', '_NUM',
             '_NUM', '_NUM'],
        ], [
            # (features) 0: ""
	    [],
            # (features) 1: " "
	    [],
            # (features) 2: "."
	    ['.'],
            # (features) 3: " . "
	    ['.'],
            # (features) 4: "test"
	    ['test'],
            # (features) 5: "test!"
	    ['test', '!'],
            # (features) 6: "CamelCase and camelCase!"
	    ['Camel', 'Case', 'and', 'camel', 'Case', '!'],
            # (features) 7: "@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['@', 'Twitter', 'User', 'Hey', 'foo@bar.com', '!', '#', 'Parse',
             'Tweets', 'http://foobar.com/tweet_parser'],
            # (features) 8: "@123.456"
	    ['@123.456'],
            # (features) 9: ""@123.456""
	    ['"', '@123.456', '"'],
            # (features) 10: "#HashTag's"
	    ["#HashTag's"],
            # (features) 11: ""#HashTag's""
	    ['"', '#', "HashTag's", '"'],
            # (features) 12: ""It's problematic""
	    ['"It\'s', 'problematic', '"'],
            # (features) 13: "@123.456 #HashTag's "It's a problem""
	    ['@123.456', '#', "HashTag's", '"', "It's", 'a', 'problem', '"'],
            # (features) 14: "@AbcDef #HashTag "It isn't a problem""
	    ['@', 'Abc', 'Def', '#', 'Hash', 'Tag', '"', 'It', "isn't", 'a',
             'problem', '"'],
            # (features) 15: "@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
            # *** TODO: Fix trimming double-quote in front of URL and E-MAIL ***
	    ['@', 'Some', 'User', 'and', '"', '@', 'Another', 'Mention', '"',
             'see', '"http://foobar.baz/entry', '"', 'and', 'tell',
             '"user@foo.com', '"', 'about', 'your', '"', '"', '#', 'Awesome',
             'Sauce', '"'],
            # (features) 16: "@SomeUser and ("@SomeMention")"
	    ['@', 'Some', 'User', 'and', '(', '"', '@', 'Some', 'Mention', '"',
             ')'],
            # (features) 17: "@Some_Mention"
	    ['@', 'Some', '_', 'Mention'],
            # (features) 18: "This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', 'a1', 'test', "don't", 'http://foo.com?bar=123',
             '@', 'user', 'abc@xyz.com', 'camel', 'Case', 'One', ',', 'Camel',
             'Case', 'Two', ',', 'camelCase1', ',', 'CamelCase2', ',', '123',
             '$123,456.78'],
        ])


def test_tweet_aware_tokenizer():
    tok = tokenizer.Tokenizer(
        smg=twitter_cores.TWEET_SMG,
        specs_and_repls=[
            (C.TWITTER_MENTION_FEATURE, '_MENTION'),
            (C.TWITTER_HASHTAG_FEATURE, '_HASHTAG'),
            (C.EMAIL_FEATURE, '_EMAIL'),
            (C.URL_FEATURE, '_URL'),
            (C.NUMERIC_FEATURE, '_NUM'),
        ],
        to_lower=False,
        drop_symbols=True,
        keep_emojis=True
    )
    do_tokenization_test(
        tok, TEST_TEXTS, [
            # (tokens) 0: ""
	    [],
            # (tokens) 1: " "
	    [],
            # (tokens) 2: "."
	    [],
            # (tokens) 3: " . "
	    [],
            # (tokens) 4: "test"
	    ['test'],
            # (tokens) 5: "test!"
	    ['test'],
            # (tokens) 6: "CamelCase and camelCase!"
	    ['Camel', 'Case', 'and', 'camel', 'Case'],
            # (tokens) 7: "@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['_MENTION', 'Hey', '_EMAIL', '_HASHTAG', '_URL'],
            # (tokens) 8: "@123.456"
	    ['_MENTION'],
            # (tokens) 9: ""@123.456""
	    ['_MENTION'],
            # (tokens) 10: "#HashTag's"
	    ['_HASHTAG'],
            # (tokens) 11: ""#HashTag's""
	    ['_HASHTAG'],
            # (tokens) 12: ""It's problematic""
	    ['"It\'s', 'problematic'],
            # (tokens) 13: "@123.456 #HashTag's "It's a problem""
	    ['_MENTION', '_HASHTAG', "It's", 'a', 'problem'],
            # (tokens) 14: "@AbcDef #HashTag "It isn't a problem""
	    ['_MENTION', '_HASHTAG', 'It', "isn't", 'a', 'problem'],
            # (tokens) 15: "@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
	    ['_MENTION', 'and', '_MENTION', 'see', '_URL', 'and', 'tell',
             '_EMAIL', 'about', 'your', '_HASHTAG'],
            # (tokens) 16: "@SomeUser and ("@SomeMention")"
	    ['_MENTION', 'and', '_MENTION'],
            # (tokens) 17: "@Some_Mention"
	    ['_MENTION'],
            # (tokens) 18: "This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', '_NUM', 'test', "don't", '_URL', '_MENTION',
             '_EMAIL', 'camel', 'Case', 'One', 'Camel', 'Case', 'Two', '_NUM',
             '_NUM', '_NUM', '_NUM'],
        ], [
            # (features) 0: ""
	    [],
            # (features) 1: " "
	    [],
            # (features) 2: "."
	    ['.'],
            # (features) 3: " . "
	    ['.'],
            # (features) 4: "test"
	    ['test'],
            # (features) 5: "test!"
	    ['test', '!'],
            # (features) 6: "CamelCase and camelCase!"
	    ['Camel', 'Case', 'and', 'camel', 'Case', '!'],
            # (features) 7: "@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['@TwitterUser', 'Hey', 'foo@bar.com', '!', '#ParseTweets',
             'http://foobar.com/tweet_parser'],
            # (features) 8: "@123.456"
	    ['@123.456'],
            # (features) 9: ""@123.456""
	    ['"', '@123.456', '"'],
            # (features) 10: "#HashTag's"
	    ["#HashTag's"],
            # (features) 11: ""#HashTag's""
	    ['"', "#HashTag's", '"'],
            # (features) 12: ""It's problematic""
	    ['"It\'s', 'problematic', '"'],
            # (features) 13: "@123.456 #HashTag's "It's a problem""
	    ['@123.456', "#HashTag's", '"', "It's", 'a', 'problem', '"'],
            # (features) 14: "@AbcDef #HashTag "It isn't a problem""
	    ['@AbcDef', '#HashTag', '"', 'It', "isn't", 'a', 'problem', '"'],
            # (features) 15: "@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
	    ['@SomeUser', 'and', '"', '@AnotherMention', '"', 'see',
             '"http://foobar.baz/entry', '"', 'and', 'tell', '"user@foo.com',
             '"', 'about', 'your', '""', '#AwesomeSauce', '"'],
            # (features) 16: "@SomeUser and ("@SomeMention")"
	    ['@SomeUser', 'and', '("', '@SomeMention"', ')'],
            # (features) 17: "@Some_Mention"
	    ['@Some_Mention'],
            # (features) 18: "This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', 'a1', 'test', "don't", 'http://foo.com?bar=123',
             '@user', 'abc@xyz.com', 'camel', 'Case', 'One', ',', 'Camel',
             'Case', 'Two', ',', 'camelCase1', ',', 'CamelCase2', ',', '123',
             '$123,456.78'],
        ])
    

def test_mention_aware_tokenizer():
    tok = tokenizer.Tokenizer(
        smg=twitter_cores.MENTION_SMG,
        specs_and_repls=[
            (C.TWITTER_MENTION_FEATURE, '_MENTION'),
            (C.TWITTER_HASHTAG_FEATURE, '_HASHTAG'),
            (C.EMAIL_FEATURE, '_EMAIL'),
            (C.URL_FEATURE, '_URL'),
            (C.NUMERIC_FEATURE, '_NUM'),
        ],
        to_lower=False,
        drop_symbols=True,
        keep_emojis=True
    )
    do_tokenization_test(
        tok, TEST_TEXTS, [
            # (tokens) 0: ""
	    [],
            # (tokens) 1: " "
	    [],
            # (tokens) 2: "."
	    [],
            # (tokens) 3: " . "
	    [],
            # (tokens) 4: "test"
	    ['test'],
            # (tokens) 5: "test!"
	    ['test'],
            # (tokens) 6: "CamelCase and camelCase!"
	    ['Camel', 'Case', 'and', 'camel', 'Case'],
            # (tokens) 7: "@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['_MENTION', 'Hey', '_EMAIL', '_HASHTAG', 'Parse', 'Tweets',
             '_URL'],
            # (tokens) 8: "@123.456"
	    ['_MENTION'],
            # (tokens) 9: ""@123.456""
	    ['_MENTION'],
            # (tokens) 10: "#HashTag's"
	    ['_HASHTAG'],
            # (tokens) 11: ""#HashTag's""
	    ['_HASHTAG', "HashTag's"],
            # (tokens) 12: ""It's problematic""
	    ['"It\'s', 'problematic'],
            # (tokens) 13: "@123.456 #HashTag's "It's a problem""
	    ['_MENTION', '_HASHTAG', "HashTag's", "It's", 'a', 'problem'],
            # (tokens) 14: "@AbcDef #HashTag "It isn't a problem""
	    ['_MENTION', '_HASHTAG', 'Hash', 'Tag', 'It', "isn't", 'a',
             'problem'],
            # (tokens) 15: "@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
	    ['_MENTION', 'and', '_MENTION', 'see', '_URL', 'and', 'tell',
             '_EMAIL', 'about', 'your', '_HASHTAG', 'Awesome', 'Sauce'],
            # (tokens) 16: "@SomeUser and ("@SomeMention")"
	    ['_MENTION', 'and', '_MENTION'],
            # (tokens) 17: "@Some_Mention"
	    ['_MENTION'],
            # (tokens) 18: "This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', '_NUM', 'test', "don't", '_URL', '_MENTION',
             '_EMAIL', 'camel', 'Case', 'One', 'Camel', 'Case', 'Two', '_NUM',
             '_NUM', '_NUM', '_NUM'],
        ], [
            # (features) 0: ""
	    [],
            # (features) 1: " "
	    [],
            # (features) 2: "."
	    ['.'],
            # (features) 3: " . "
	    ['.'],
            # (features) 4: "test"
	    ['test'],
            # (features) 5: "test!"
	    ['test', '!'],
            # (features) 6: "CamelCase and camelCase!"
	    ['Camel', 'Case', 'and', 'camel', 'Case', '!'],
            # (features) 7: "@TwitterUser Hey foo@bar.com! #ParseTweets http://foobar.com/tweet_parser"
	    ['@TwitterUser', 'Hey', 'foo@bar.com', '!', '#', 'Parse', 'Tweets',
             'http://foobar.com/tweet_parser'],
            # (features) 8: "@123.456"
	    ['@123.456'],
            # (features) 9: ""@123.456""
	    ['"', '@123.456', '"'],
            # (features) 10: "#HashTag's"
	    ["#HashTag's"],
            # (features) 11: ""#HashTag's""
	    ['"', '#', "HashTag's", '"'],
            # (features) 12: ""It's problematic""
	    ['"It\'s', 'problematic', '"'],
            # (features) 13: "@123.456 #HashTag's "It's a problem""
	    ['@123.456', '#', "HashTag's", '"', "It's", 'a', 'problem', '"'],
            # (features) 14: "@AbcDef #HashTag "It isn't a problem""
	    ['@AbcDef', '#', 'Hash', 'Tag', '"', 'It', "isn't", 'a', 'problem',
             '"'],
            # (features) 15: "@SomeUser and "@AnotherMention" see "http://foobar.baz/entry" and tell "user@foo.com" about your ""#AwesomeSauce""
	    ['@SomeUser', 'and', '"', '@AnotherMention', '"', 'see',
             '"http://foobar.baz/entry', '"', 'and', 'tell', '"user@foo.com',
             '"', 'about', 'your', '"', '"', '#', 'Awesome', 'Sauce', '"'],
            # (features) 16: "@SomeUser and ("@SomeMention")"
	    ['@SomeUser', 'and', '("', '@SomeMention"', ')'],
            # (features) 17: "@Some_Mention"
	    ['@Some_Mention'],
            # (features) 18: "This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78"
	    ['This', 'is', 'a1', 'test', "don't", 'http://foo.com?bar=123',
             '@user', 'abc@xyz.com', 'camel', 'Case', 'One', ',', 'Camel',
             'Case', 'Two', ',', 'camelCase1', ',', 'CamelCase2', ',', '123',
             '$123,456.78'],
        ])


#def test_the_next_smg_core():
#    tok = tokenizer.Tokenizer(
#        smg=twitter_cores.TWEET_SMG,
#        specs_and_repls=[
#            (C.TWITTER_MENTION_FEATURE, '_MENTION'),
#            (C.TWITTER_HASHTAG_FEATURE, '_HASHTAG'),
#            (C.EMAIL_FEATURE, '_EMAIL'),
#            (C.URL_FEATURE, '_URL'),
#            (C.NUMERIC_FEATURE, '_NUM'),
#        ],
#        to_lower=False,
#        drop_symbols=True,
#        keep_emojis=True
#    )
#    do_tokenization_test(
#        tok, TEST_TEXTS, [
#        ], [
#        ],
#        verify=False)
