import latok.core.default_tokenizer as tokenizer


def test_default_tokenization_expectations():
    text = '''This is a1 test don't http://foo.com?bar=123 @user abc@xyz.com camelCaseOne, CamelCaseTwo, camelCase1, CamelCase2, 123 $123,456.78'''

    # Token text
    expected_token_texts = [
        'This', 'is', 'a1', 'test',
        "don't",
        'http://foo.com?bar=123',
        '@user',
        'abc@xyz.com',
        'camel', 'Case', 'One', ',', 'Camel', 'Case', 'Two', ',',
        'camelCase1', ',', 'CamelCase2',  # NOTE: Not split because these have digits
        ',', '123', '$123,456.78'
    ]
    token_texts = list(tokenizer.tokenize(text))
    assert token_texts == expected_token_texts

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
    tokenizer.add_abstract_features(tokens, [
        tokenizer.TWITTER_FEATURE, tokenizer.EMAIL_FEATURE,
        tokenizer.URL_FEATURE, tokenizer.CAMEL_CASE_FEATURE,
        tokenizer.NUMERIC_FEATURE, tokenizer.EMBEDDED_APOS_FEATURE,
        tokenizer.SYMBOLS_ONLY_FEATURE,
    ])
    features = [(token.text, token.abstract_features) for token in tokens]
    assert features == expected_features
