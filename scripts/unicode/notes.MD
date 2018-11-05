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