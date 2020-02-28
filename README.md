LaTok
=============================

Linear Algebraic Tokenizer


## Description

A customizable, fast NLP tokenizer based on linear algebraic operations.

### Key Points:

#### Usage

* Default tokenization:

```python
import latok.core.default_tokenizer as tokenizer
tokens = list(tokenizer.tokenize('''This isn't a test; but this is!'''))
```

* Customized tokenization:
    * Use ```latok.core.default_tokenizer``` as a pattern
    * See ```notebooks/tutorial``` for more information

#### Classification

* Provides token-level classification features based on the character-level features
    * See ```latok.core.default_tokenizer.*_FEATURE```

```python
import latok.core.default_tokenizer as tokenizer
tokens = tokenizer.featurize(text)
tokenizer.add_abstract_features(tokens, feature_list)
```

#### Algorithm:

* Construct a matrix, representing each letter in a string as a vector of features.
   * Where features are, e.g.,
      * unicode character characteristics like alpha, numeric, uppercase, lowercase, etc.
      * context information such as preceding or following character characteristics, etc.
* Apply relevant linear operations on the feature matrix to generate a tokenization mask
   * Where non-zero entries in the final mask identify character locations on which to split the string into tokens.

#### Performance:

* As a primary design and implementation goal, ensure that tokenization is
   * Performant in terms of strings tokenized over time
   * Memory efficient in terms of memory consumed for tokenization
* Implemented where necessary as C extensions to NumPy and Python

## Project Setup

* Through docker:
    * ```pip3 -U install dockerutils```
    * Development:
        * Scripts/Shell
            * ```bin/dev```
        * Notebook
            * ```run-notebook```
        * Run tests
            * ```bin/test```
* Through a virtual environment:
    * If you have ops/bin in your path, please remove it, it has been deprecated.
    * Ensure that you have python installed. 3.5 or 3.6 is required at this point. 3.7 should be supported shortly.
    * Ensure that you have docker installed and /data configured as a file share
    * Ensure that your python bin directory is in your path (likely /Library/Frameworks/Python.framework/Versions/3.6/bin)
    * Ensure that your pip.conf (~/.pip/pip.conf) includes our internal pypi servers (see pip.conf.template in this repo)
    * bin/setup-dev to install environment
    * activate virtual environment (source activate)
    * run unit test (bin/test -ud)
