import latok.core.constants as C
import latok.core.default_tokenizer as latok


def test_get_specs_and_repls():
    assert latok.get_specs_and_repls(None) == (None, None)
    assert latok.get_specs_and_repls([]) == (None, None)
    specs, repls = latok.get_specs_and_repls([(C.URL_FEATURE, None)])
    assert (specs, repls) == ([C.URL_FEATURE], None)
    specs, repls = latok.get_specs_and_repls([(None, '???')])
    assert (specs, repls) == (None, None)
    specs, repls = latok.get_specs_and_repls([(C.URL_FEATURE, '_URL')])
    assert (specs, repls) == ([C.URL_FEATURE], {C.URL_FEATURE.name: '_URL'})


def test_default_tokenization_expectations1():
    tokenizer = latok.DefaultTokenizer()
    assert tokenizer.split_props1 == latok.DEFAULT_SPLIT_PROPS1
    assert tokenizer.block_props == latok.DEFAULT_BLOCK_PROPS
    assert tokenizer.split_props2 == latok.DEFAULT_SPLIT_PROPS2
    t2 = tokenizer.copy(to_lower=(not tokenizer.to_lower))
    assert t2.to_lower != tokenizer.to_lower

def test_default_tokenization_expectations2():
    text = '''This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78'''

    # Token text
    expected_plain_token_texts = [
        'This', 'is', 'a1', 'test',
        "don't",
        'http://foo.com?bar=123',
        '@user',
        'abc@xyz.com',
        'camel', 'Case', 'One', ',', 'Camel', 'Case', 'Two', ',',
        'camelCase1', ',', 'CamelCase2',  # NOTE: Not split because these have digits
        ',', '123', '$123,456.78'
    ]
    expected_repl_token_texts = [
        'This', 'is', '_NUM', 'test',
        "don't",
        '_URL',
        '@user',
        '_EMAIL',
        'camel', 'Case', 'One', '_SYM', 'Camel', 'Case', 'Two', '_SYM',
        'camelCase1', '_SYM', 'CamelCase2',  # NOTE: Not split because these have digits
        '_SYM', '_NUM', '_NUM'
    ]
    tokenizer = latok.DefaultTokenizer(
        specs_and_repls=[
            (C.TWITTER_FEATURE, None),
            (C.EMAIL_FEATURE, '_EMAIL'),
            (C.URL_FEATURE, '_URL'),
            (C.CAMEL_CASE_FEATURE, None),
            (C.NUMERIC_FEATURE, '_NUM'),
            (C.EMBEDDED_APOS_FEATURE, None),
            (C.SYMBOLS_ONLY_FEATURE, '_SYM'),
        ])
    token_repl_texts = list(tokenizer.tokenize(text))
    assert token_repl_texts == expected_repl_token_texts
    token_plain_texts = list(tokenizer.tokenize(text, replace_override=False))
    assert token_plain_texts == expected_plain_token_texts

    # Token features
    expected_features = [
        ('This', None), ('is', None), ('a1', ['numeric']), ('test', None),
        ("don't", ['apos']),
        ('http://foo.com?bar=123', ['url', 'numeric']),
        ('@user', ['twitter']),
        ('abc@xyz.com', ['email']),
        ('camel', None), ('Case', ['camelcase']), ('One', ['camelcase']),
        (',', ['symbols']),
        ('Camel', None), ('Case', ['camelcase']), ('Two', ['camelcase']),
        (',', ['symbols']),
        ('camelCase1', ['camelcase', 'numeric']), (',', ['symbols']),
        ('CamelCase2', ['camelcase', 'numeric']), (',', ['symbols']),
        ('123', ['numeric']), ('$123,456.78', ['numeric'])
    ]
    tokens = list(tokenizer.featurize(text))
    features = [(token.text, token.abstract_features) for token in tokens]
    assert features == expected_features
