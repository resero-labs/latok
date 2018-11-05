/*
   Create the parse matrix for a input text string.

   Written by Dan Rapp (drapp@proofpoint.com)

   Copyright (c) Proofpoint, Inc.

*/

#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>
#include "latok.h"

static const _TtUnicode_TypeRecord *
gettyperecord(Py_UCS4 code)
{
    int index;

    if (code >= 0x110000)
        index = 0;
    else
    {
        index = index1[(code>>SHIFT)];
        index = index2[(index<<SHIFT)+(code&((1<<SHIFT)-1))];
    }

    return &_TtUnicode_TypeRecords[index];
}

static PyObject *
gen_parse_matrix(PyObject *self, PyObject *args)
{
    Py_ssize_t i, length;
    Py_UNICODE *arg0;
    PyArrayObject *rtn;
    int kind;
    void *data;

    if (PyTuple_GET_SIZE(args) < 1) {
        PyErr_SetString(PyExc_ValueError, "must specify string to generate the parse matrix for");
        return NULL;
    }

    // ensure the string is ready to be parsed
    arg0 = PyTuple_GET_ITEM(args, 0);
    if (PyUnicode_READY(arg0) == -1) {
        PyErr_SetString(PyExc_ValueError, "Input string not in 'ready' state");
        return NULL;
    }

    // get the length, data and kind of string this is
    length = PyUnicode_GET_LENGTH(arg0);
    kind = PyUnicode_KIND(arg0);
    data = PyUnicode_DATA(arg0);

    // get the matrix to parse into
    npy_intp dims[2] = {length, FEATURE_COUNT};
    rtn = PyArray_SimpleNew(2, dims, NPY_BYTE);
    unsigned char *m = (int *)PyArray_DATA(rtn);
    unsigned char *lower_boundary = m;
    unsigned char *upper_boundary = m + FEATURE_COUNT * length;
    unsigned char *prev; // This pointer points to the previous character's row
    unsigned char *before_prev; // This pointer points to the row before the previous character's row
    unsigned char *next; // This pointer points to the next character's row
    unsigned char *after_next; // This pointer points to the row after the next character's row

    // Initialize all of the PREV columns to 0 as there are no previous characters
    *(m + PREV_ALPHA_IDX    ) = 0;
    *(m + PREV_ALPHA_NUM_IDX) = 0;
    *(m + PREV_LOWER_IDX    ) = 0;
    *(m + PREV_SPACE_IDX    ) = 1;
    *(m + PREV_SYMBOL_IDX   ) = 0;

    // now iterate through the string character by character and get the type record for
    // each char
    for (i = 0; i < length; i++)
    {
        const _TtUnicode_TypeRecord *type_record = gettyperecord(PyUnicode_READ(kind, data, i));
        // with the type record flags, set the appropriate columns in the parse matrix
        const unsigned int flags = type_record->flags;
        prev = m - FEATURE_COUNT;
        before_prev = m - 2 * FEATURE_COUNT;
        next = m + FEATURE_COUNT;
        after_next = m + 2 * FEATURE_COUNT;

        *(m + ALPHA_IDX      ) = flags & ALPHA_MASK       ? 1 : 0;
        *(m + ALPHA_NUM_IDX  ) = flags & ALPHA_MASK || flags & NUMERIC_MASK ? 1 : 0;
        *(m + NUM_IDX        ) = flags & NUMERIC_MASK     ? 1 : 0;
        *(m + LOWER_IDX      ) = flags & LOWER_MASK       ? 1 : 0;
        *(m + UPPER_IDX      ) = flags & UPPER_MASK       ? 1 : 0;
        *(m + SPACE_IDX      ) = flags & SPACE_MASK       ? 1 : 0;
        *(m + SYMBOL_IDX     ) = flags & PRINTABLE_MASK && !*(m + ALPHA_NUM_IDX) && !*(m + SPACE_IDX) ? 1 : 0;
        *(m + TWITTER_IDX    ) = flags & SPECIALS_MASK    ? 1 : 0;
        *(m + CHAR_AT_IDX    ) = flags & CHAR_AT_MASK     ? 1 : 0;
        *(m + CHAR_COLON_IDX ) = flags & CHAR_COLON_MASK  ? 1 : 0;
        *(m + CHAR_SLASH_IDX ) = flags & CHAR_SLASH_MASK  ? 1 : 0;
        *(m + CHAR_PERIOD_IDX) = flags & CHAR_PERIOD_MASK ? 1 : 0;
        if (prev >= lower_boundary) {
            // propagate the relevant features from this row into the previous character's row in the "next character" columns
            *(prev + NEXT_ALPHA_IDX    ) = *(m + ALPHA_IDX);
            *(prev + NEXT_ALPHA_NUM_IDX) = *(m + ALPHA_NUM_IDX);
            *(prev + NEXT_LOWER_IDX    ) = *(m + LOWER_IDX);
            *(prev + NEXT_SPACE_IDX    ) = *(m + SPACE_IDX);
            *(prev + NEXT_AT_IDX       ) = *(m + CHAR_AT_IDX);
            *(prev + NEXT_SLASH_IDX    ) = *(m + CHAR_SLASH_IDX);
            // Pull the relevant features from the previous character's row into the "prev character" column of this row
            *(m + PREV_ALPHA_IDX    ) = *(prev + ALPHA_IDX);
            *(m + PREV_ALPHA_NUM_IDX) = *(prev + ALPHA_NUM_IDX);
            *(m + PREV_LOWER_IDX    ) = *(prev + LOWER_IDX);
            *(m + PREV_SPACE_IDX    ) = *(prev + SPACE_IDX);
            *(m + PREV_SYMBOL_IDX   ) = *(prev + SYMBOL_IDX);
        }
        else {
            // Start of string behaves as a space
            *(m + PREV_SPACE_IDX    ) = 1;
        }
        if (before_prev >= lower_boundary) {
            *(before_prev + AFTER_NEXT_ALPHA_IDX) = *(m + ALPHA_IDX);
            *(before_prev + AFTER_NEXT_SLASH_IDX) = *(m + CHAR_SLASH_IDX);
        }
        if (next >= upper_boundary) {
            // set all next columns to 0
            *(m + NEXT_ALPHA_IDX    ) = 0;
            *(m + NEXT_ALPHA_NUM_IDX) = 0;
            *(m + NEXT_AT_IDX       ) = 0;
            *(m + NEXT_LOWER_IDX    ) = 0;
            *(m + NEXT_SLASH_IDX    ) = 0;
            *(m + NEXT_SPACE_IDX    ) = 1;  // End of string behaves as a space
        }
        if (after_next >= upper_boundary) {
            *(m + AFTER_NEXT_SLASH_IDX) = 0;
            *(m + AFTER_NEXT_ALPHA_IDX) = 0;
        }
        m += FEATURE_COUNT;
    }
    return rtn;
}

static PyObject *
gen_block_mask(PyObject *self, PyObject *args)
{
    // create a mask of 1's with 0's between a2 1's where a1 has a 1
    // args: a1, a2 -- 2 aligning one-dimensional numpy arrays with matching length
    // returns the block mask

    Py_ssize_t i, idx2;
    long midx;
    PyArrayObject *rtn;

    if (PyTuple_GET_SIZE(args) < 2) {
        PyErr_SetString(PyExc_ValueError, "must specify two aligning 1d numpy array args");
        return NULL;
    }

    PyArrayObject *a1 = PyTuple_GET_ITEM(args, 0);
    PyArrayObject *a2 = PyTuple_GET_ITEM(args, 1);

    if (PyArray_NDIM(a1) != 1 || PyArray_NDIM(a2) != 1) {
        PyErr_SetString(PyExc_ValueError, "must specify 1d numpy array args");
        return NULL;
    }

    npy_intp *dims = PyArray_DIMS(a1);
    //int dtype = PyArray_TYPE(a1);
    npy_intp len = PyArray_SIZE(a1);

    if (len != PyArray_SIZE(a2)) {
        PyErr_SetString(PyExc_ValueError, "must specify 1d numpy arrays of matching length");
        return NULL;
    }

    // build the result mask
    rtn = PyArray_SimpleNew(1, dims, NPY_BYTE);
    unsigned char *mask_data = (int *)PyArray_DATA(rtn);
    //unsigned char mask_data[len];

    PyObject *a1_nz_tuple = PyArray_Nonzero(a1);
    PyArrayObject *a1_nz_array = PyTuple_GET_ITEM(a1_nz_tuple, 0);
    npy_intp a1_nz_len = PyArray_SIZE(a1_nz_array);
    long *a1_nz_data = (long *)PyArray_DATA(a1_nz_array);

    //debugging...
    //printf("got a1 size %d\n", a1_nz_len);
    //printf("\ta1_nz:");
    //for (i = 0; i < a1_nz_len; ++i) {
    //    printf(" %ld", a1_nz_data[i]);
    //}
    //printf("\n");

    if (a1_nz_len == 0) {
        // Nothing to mask
        for (i = 0; i < len; ++i) {
            mask_data[i] = 1;
        }
    }
    else {
        PyObject *a2_nz_tuple = PyArray_Nonzero(a2);
        PyArrayObject *a2_nz_array = PyTuple_GET_ITEM(a2_nz_tuple, 0);
        npy_intp a2_nz_len = PyArray_SIZE(a2_nz_array);
        long *a2_nz_data = (long *)PyArray_DATA(a2_nz_array);

        //debugging...
        //printf("got a2 size %d\n", a2_nz_len);
        //printf("\ta2_nz:");
        //for (i = 0; i < a2_nz_len; ++i) {
        //    printf(" %ld", a2_nz_data[i]);
        //}
        //printf("\n");

        if (a2_nz_len == 0) {
            // Everything to mask
            for (i = 0; i < len; ++i) {
                mask_data[i] = 0;
            }
        }
        else {
            // Initialize mask to all 1's
            for (i = 0; i < len; ++i) {
                mask_data[i] = 1;
            }
            int idx1 = 0;
            long val1 = a1_nz_data[idx1];
            long prev_val2 = 0;  // treat beginning of a2 as a 1
            for (idx2 = 0; idx2 < a2_nz_len; ++idx2) {
                long val2 = a2_nz_data[idx2];
                if (val2 >= val1) {
                    for (midx = prev_val2+1; midx < val2; ++midx) {
                      mask_data[midx] = 0;
                    }
                    idx1 += 1;
                    if (idx1 >= a1_nz_len) {
                      break;
                    }
                    val1 = a1_nz_data[idx1];
                }
                prev_val2 = val2;
            }
            // treat end of a2 as a 1
            if (idx1 < a1_nz_len) {
                for (midx = prev_val2+1; midx < len; ++midx) {
                    mask_data[midx] = 0;
                }
            }
        }
    }

    //debugging...
    //printf("mask data:\n");
    //for (i = 0; i < len; ++i) {
    //    printf(" %d", mask_data[i]);
    //}
    //printf("\n");

    // return the result array
    //rtn = PyArray_SimpleNewFromData(1, dims, dtype, mask_data);
    return rtn;
}

static PyArrayObject *
convert_to_byte_array(PyArrayObject *arr)
{
    // convert the given array to a byte array
    int typenum = PyArray_TYPE(arr);
    if (typenum != NPY_BYTE) {
        PyArrayObject* arr2 =
            (PyArrayObject*)PyArray_FromArray(arr, PyArray_DescrFromType(NPY_BYTE),
                                              NPY_ARRAY_ALIGNED);
        Py_DECREF(arr);
        arr = arr2;
    }
    return arr;
}

static PyObject *
combine_matrix_rows(PyObject *self, PyObject *args)
{
    // element-wise combine the identified rows of the matrix 
    // args:
    //     m -- a 2d matrix whose selected rows to multiply and add
    //     idxs -- the 2d indexes of the matrix rows to "and" (multiply) and "or" (add),
    //             where each idx row's column indexes identify values to be "anded" (multiplied)
    //             and each idx row result is to be "or'd" (added).
    //             NOTE: idx values of -1 are ignored.
    //             OR
    //             the 1d indexes of the matrix rows to "or" (add)
    // returns the row result of the operations

    Py_ssize_t i, j, k;
    PyArrayObject *rtn;

    if (PyTuple_GET_SIZE(args) < 2) {
        PyErr_SetString(PyExc_ValueError, "must specify 2d m and idxs matrices");
        return NULL;
    }

    PyArrayObject *m = convert_to_byte_array(PyTuple_GET_ITEM(args, 0));
    unsigned char *m_data = (int *)PyArray_DATA(m);
    npy_intp  *mstrides = PyArray_STRIDES(m);
    npy_intp *mdims = PyArray_DIMS(m);
    int mcols = mdims[1];

    PyArrayObject *idxs = convert_to_byte_array(PyTuple_GET_ITEM(args, 1));
    unsigned char *idxs_data = (int *)PyArray_DATA(idxs);
    npy_intp  *istrides = PyArray_STRIDES(idxs);
    npy_intp *idims = PyArray_DIMS(idxs);
    int nidims = PyArray_NDIM(idxs);

    if (PyArray_NDIM(m) != 2 || nidims > 2) {
        PyErr_SetString(PyExc_ValueError, "must specify 2d numpy array args");
        return NULL;
    }

    unsigned char result[mcols];
    for (i = 0; i < mcols; ++i) result[i] = 0;  // initialize result to 0's
    unsigned char row[mcols];

    if (nidims == 2) {
      // "and" and "or"
      int irows = idims[0];
      int icols = idims[1];
      for (i = 0; i < irows; ++i) {
        for (j = 0; j < icols; ++j) {
          unsigned char m_row = *(unsigned char*)&idxs_data[ i*istrides[0] + j*istrides[1] ];
          if (m_row < 255) {  //NOTE: 255 == -1 (unsigned char)
            for (k = 0; k < mcols; ++k) {
              unsigned char mval = *(unsigned char*)&m_data[ m_row*mstrides[0] + k*mstrides[1] ];
              if (j == 0) {
                row[k] = mval;
              }
              else {
                row[k] *= mval;
              }
            }
          }
        }
        for (k = 0; k < mcols; ++k) {
          result[k] += row[k];
        }
      }
    }
    else {  // ndims == 1
      // just "or"
      int icols = idims[0];
      for (j = 0; j < icols; ++j) {
        unsigned char m_row = idxs_data[j];
        if (m_row < 255) {  //NOTE: 255 == -1 (unsigned char)
          for (k = 0; k < mcols; ++k) {
            unsigned char mval = *(unsigned char*)&m_data[ m_row*mstrides[0] + k*mstrides[1] ];
            result[k] += mval;
          }
        }
      }
    }

    npy_intp rdims[] = {mcols};
    rtn = PyArray_SimpleNew(1, rdims, NPY_BYTE);
    unsigned char *r_data = (int *)PyArray_DATA(rtn);
    for (i = 0; i < mcols; ++i) r_data[i] = result[i];

    //debugging...
    //printf("combined data:");
    //for (i = 0; i < mcols; ++i) {
    //    printf(" %d", result[i]);
    //}
    //printf("\n");

    // return the result array
    return rtn;
}

/* ==== Set up the methods table ====================== */
static PyMethodDef _C_latokMethods[] = {
	{"_gen_parse_matrix", gen_parse_matrix, METH_VARARGS},
  {"_gen_block_mask", gen_block_mask, METH_VARARGS},
  {"_combine_matrix_rows", combine_matrix_rows, METH_VARARGS},
	{NULL, NULL}     /* Sentinel - marks the end of this structure */
};

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "latok",
        NULL,
        -1,
        _C_latokMethods,
        NULL,
        NULL,
        NULL,
        NULL
};

/* Initialization function for the module */
#define RETVAL m
PyMODINIT_FUNC PyInit_latok(void) {
    PyObject *m;

    /* Create the module and add the functions */
    m = PyModule_Create(&moduledef);
    if (!m) {
        goto err;
    }

    import_array();

    if (PyErr_Occurred()) {
        goto err;
    }

    return RETVAL;

 err:
    if (!PyErr_Occurred()) {
        PyErr_SetString(PyExc_RuntimeError, "cannot load latok module.");
    }
    return RETVAL;
}

