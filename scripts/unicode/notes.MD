# Notes on a fast matrix tokenizer

For a good background on python strings and unicode, see: [How Python Does Unicode](https://www.b-list.org/weblog/2017/sep/05/how-python-does-unicode/)

Looking at the numpy code, it appears that numpy unicode arrays are ucs-4
(From `buffer.c`)
```
        case NPY_UNICODE: {
            /* NumPy Unicode is always 4-byte */
            char buf[128];
            assert(descr->elsize % 4 == 0);
            PyOS_snprintf(buf, sizeof(buf), "%dw", descr->elsize / 4);
            if (_append_str(str, buf) < 0) return -1;
            break;
        }

```
Because of this, we shouldn't allocate a numpy array of strings.

See [pep 393](https://www.python.org/dev/peps/pep-0393/) to understand string access from c extension

See [C Extensions for Using NumPy Arrays](https://scipy-cookbook.readthedocs.io/items/C_Extensions_NumPy_arrays.html) for a good writeup on writing numpy c extensions

# Implementation notes

## Original implementation

makeunicodedata.py version 11.0.0 was copied from the Python 3.7.1 source distribution and modified to add flags for special characters to be recognized by the tokenizer.

Note that the script automatically pulls its required unicode data files from unicode.org and the pulled datafiles are not added to this git repository.

## Maintenance

For new recognition classes,
* add a unique mask to the _MASK definitions and update the SIZING_ and DESIZING_ MASKs
* in makeunicodetype(), add
   * recognizing the new character class(es) and updating the flags
   * adding the #define for the mask(s) to latok.h
   * adding the mask variable(s) to offsets.py
   * adding the index variable(s) to offsets.py

### Upgrading unicode versions

To upgrade makeunicodedata.py for capturing the latest unicode updates including emoji data, an update copy of makeunicodedata.py was copied from https://github.com/python/cpython/tree/master/Tools/unicode and modified to include the original modifications in addition to loading emoji data.

With these changes, the number of flags increased beyond 32 and will require 64 bits.

### Incorporating modifications into latok

Once makeunicodedata.py has been updated for desired modifications, the following steps can be taken:

* Run the makeunicodedata.py script to generate latok.h and offsets.py:
```
pushd scripts/unicode
python3 ./makeunicodedata.py
popd
```

* Edit latok.c to update the parse matrix with the new flag(s)

* Edit latok_utils.py to add a feature name for the new flag(s)

* Rebuild through "pip install -e ." in the docker container or virtual env
