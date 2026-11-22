# English technical-workbench annotation review

Dataset: `english-technical-v2`

Dataset SHA-256: `a0cda0ce5a3e1e1d1c2190d7e935af2a86d0a578c249f523f35802440666c5f6`

Quoted display omits trailing whitespace; canonical source bytes and labelled offsets remain unchanged.

All annotations are authored drafts. An independent reviewer must check the question, answerability, required facts, each complete alternative, source revision and offsets, category and grouping. Check surrounding source context, not just the excerpt. Record disagreements and resolve them before approval. Do not infer correctness from a successful loader check or approve unseen questions.

To approve reviewed labels, set each dataset query review.status to approved and review.reviewer to your identity. Keep the author identity. Add review notes for disputed or revised labels. Update the dataset version when facts/splits change; rerun recorded comparisons against the new manifest hash. No runner auto-approves annotations.

## json-dumps

development / json+pickle / exact_api / draft

Which json function returns a JSON string rather than writing to a stream?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the worked example that names json.dumps and shows its returned JSON string.

Fact `json-dumps`:

json.dumps returns the serialized JSON representation as a string, rather than writing it to a stream.

Alternative `json-dumps`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [8462, 8467)
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [8692, 8861)

Labelled source text:

> dumps

Surrounding canonical source context:

> : 3.4
>       Use ``(',', ': ')`` as default if *indent* is not ``None``.
>
>    .. versionchanged:: 3.6
>       All optional parameters are now :ref:`keyword-only <keyword-only_parameter>`.
>
>
> .. function:: dumps(obj, *, skipkeys=False, ensure_ascii=True, \
>                     check_circular=True, allow_nan=True, cls=None, \
>                     indent=None, separators=None, default=None, \
>

Labelled source text:

>    Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
>    table <py-to-json-table>`.  The arguments have the same meaning as in
>    :func:`dump`.

Surrounding canonical source context:

> ensure_ascii=True, \
>                     check_circular=True, allow_nan=True, cls=None, \
>                     indent=None, separators=None, default=None, \
>                     sort_keys=False, **kw)
>
>    Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
>    table <py-to-json-table>`.  The arguments have the same meaning as in
>    :func:`dump`.
>
>    .. note::
>
>       Keys in key/value pairs of JSON are always of the type :class:`str`. When
>       a dictionary is converted into JSON, all the keys of the dictionary are
>       coerced to strings.

Alternative `json-dumps-worked-example`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [1366, 1471)

Labelled source text:

>     >>> json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
>     '["foo", {"bar": ["baz", null, 1.0, 2]}]'

Surrounding canonical source context:

> parsed is recommended.
>
> This module exposes an API familiar to users of the standard library
> :mod:`marshal` and :mod:`pickle` modules.
>
> Encoding basic Python object hierarchies::
>
>     >>> import json
>     >>> json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
>     '["foo", {"bar": ["baz", null, 1.0, 2]}]'
>     >>> print(json.dumps("\"foo\bar"))
>     "\"foo\bar"
>     >>> print(json.dumps('\u1234'))
>     "\u1234"
>     >>> print(json.dumps('\\'))
>     "\\"
>     >>> print(json.dumps({"c": 0, "b": 0, "a": 0}, sor

Review decision / disagreements / resolution: **pending**

## json-load

development / json+pickle / paraphrase / draft

How does json.load read a serialized value?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the file/read contract needed to explain how the value is read.

Fact `json-load`:

json.load reads a JSON document from a .read()-supporting text or binary file and deserializes it into a Python object.

Alternative `json-load`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [9294, 9298)
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [9462, 9572)
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [9577, 9752)

Labelled source text:

> load

Surrounding canonical source context:

> ary is converted
>       into JSON and then back into a dictionary, the dictionary may not equal
>       the original one. That is, ``loads(dumps(x)) != x`` if x has non-string
>       keys.
>
> .. function:: load(fp, *, cls=None, object_hook=None, parse_float=None, \
>                    parse_int=None, parse_constant=None, \
>                    object_pairs_hook=None, **kw)
>
>    Deserialize *fp* to a Python obje

Labelled source text:

>    Deserialize *fp* to a Python object
>    using the :ref:`JSON-to-Python conversion table <json-to-py-table>`.

Surrounding canonical source context:

> ring
>       keys.
>
> .. function:: load(fp, *, cls=None, object_hook=None, parse_float=None, \
>                    parse_int=None, parse_constant=None, \
>                    object_pairs_hook=None, **kw)
>
>    Deserialize *fp* to a Python object
>    using the :ref:`JSON-to-Python conversion table <json-to-py-table>`.
>
>    :param fp:
>       A ``.read()``-supporting :term:`text file` or :term:`binary file`
>       containing the JSON document to be deserialized.
>    :type fp: :term:`file-like object`
>
>    :param cls:
>

Labelled source text:

> :param fp:
>       A ``.read()``-supporting :term:`text file` or :term:`binary file`
>       containing the JSON document to be deserialized.
>    :type fp: :term:`file-like object`

Surrounding canonical source context:

> e_int=None, parse_constant=None, \
>                    object_pairs_hook=None, **kw)
>
>    Deserialize *fp* to a Python object
>    using the :ref:`JSON-to-Python conversion table <json-to-py-table>`.
>
>    :param fp:
>       A ``.read()``-supporting :term:`text file` or :term:`binary file`
>       containing the JSON document to be deserialized.
>    :type fp: :term:`file-like object`
>
>    :param cls:
>       If set, a custom JSON decoder.
>       Additional keyword arguments to :func:`!load`
>       will be passed to the constructor of *cls*.
>       If ``None`` (the default), :class:`!JS

Review decision / disagreements / resolution: **pending**

## json-JSONDecoder

development / json+pickle / exact_api / draft

What job does JSONDecoder perform?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `json-JSONDecoder`:

json.JSONDecoder is a simple JSON decoder.

Alternative `json-JSONDecoder`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [13504, 13515)
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [13630, 13653)

Labelled source text:

> JSONDecoder

Surrounding canonical source context:

> e
>       input encoding should be UTF-8, UTF-16 or UTF-32.
>
>    .. versionchanged:: 3.9
>       The keyword argument *encoding* has been removed.
>
>
> Encoders and Decoders
> ---------------------
>
> .. class:: JSONDecoder(*, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, strict=True, object_pairs_hook=None)
>
>    Simple JSON decoder.
>
>    Performs the following translations in decoding by defaul

Labelled source text:

>    Simple JSON decoder.

Surrounding canonical source context:

> s been removed.
>
>
> Encoders and Decoders
> ---------------------
>
> .. class:: JSONDecoder(*, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, strict=True, object_pairs_hook=None)
>
>    Simple JSON decoder.
>
>    Performs the following translations in decoding by default:
>
>    .. _json-to-py-table:
>
>    +---------------+-------------------+
>    | JSON          | Python            |
>    +===============+======

Review decision / disagreements / resolution: **pending**

## json-JSONEncoder

development / json+pickle / paraphrase / draft

What is JSONEncoder used for?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `json-JSONEncoder`:

json.JSONEncoder is an extensible encoder for Python data structures.

Alternative `json-JSONEncoder`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [17244, 17255)
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [17393, 17447)

Labelled source text:

> JSONEncoder

Surrounding canonical source context:

> Python representation
>       and the index in *s* where the document ended.
>
>       This can be used to decode a JSON document from a string that may have
>       extraneous data at the end.
>
>
> .. class:: JSONEncoder(*, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False, indent=None, separators=None, default=None)
>
>    Extensible JSON encoder for Python data structures.
>
>    Sup

Labelled source text:

>    Extensible JSON encoder for Python data structures.

Surrounding canonical source context:

> ave
>       extraneous data at the end.
>
>
> .. class:: JSONEncoder(*, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, sort_keys=False, indent=None, separators=None, default=None)
>
>    Extensible JSON encoder for Python data structures.
>
>    Supports the following objects and types by default:
>
>    .. _py-to-json-table:
>
>    +----------------------------------------+---------------+
>    | Python                                 | JSON

Review decision / disagreements / resolution: **pending**

## csv-reader

development / csv+gzip / exact_api / draft

What does csv.reader produce from an iterable of lines?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old span described the input and reader object but omitted the returned row representation and conversion exception.

Fact `csv-reader`:

csv.reader returns a reader object yielding rows as lists of strings; QUOTE_NONNUMERIC converts unquoted fields to floats instead.

Alternative `csv-reader`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2024, 2030)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2077, 2263)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2925, 3168)

Labelled source text:

> reader

Surrounding canonical source context:

>  to Python.
>
>
> .. _csv-contents:
>
> Module Contents
> ---------------
>
> The :mod:`csv` module defines the following functions:
>
>
> .. index::
>    single: universal newlines; csv.reader function
>
> .. function:: reader(csvfile, /, dialect='excel', **fmtparams)
>
>    Return a :ref:`reader object <reader-objects>` that will process
>    lines from the given *csvfile*.  A csvfile must be an iterable of
>    strings, each in

Labelled source text:

> Return a :ref:`reader object <reader-objects>` that will process
>    lines from the given *csvfile*.  A csvfile must be an iterable of
>    strings, each in the reader's defined csv format.

Surrounding canonical source context:

> -----------
>
> The :mod:`csv` module defines the following functions:
>
>
> .. index::
>    single: universal newlines; csv.reader function
>
> .. function:: reader(csvfile, /, dialect='excel', **fmtparams)
>
>    Return a :ref:`reader object <reader-objects>` that will process
>    lines from the given *csvfile*.  A csvfile must be an iterable of
>    strings, each in the reader's defined csv format.
>    A csvfile is most commonly a file-like object or list.
>    If *csvfile* is a file object,
>    it should be opened with ``newline=''``. [1]_  An optional
>    *dialect* parameter can be given which is

Labelled source text:

> Each row read from the csv file is returned as a list of strings.  No
>    automatic data type conversion is performed unless the :data:`QUOTE_NONNUMERIC` format
>    option is specified (in which case unquoted fields are transformed into floats).

Surrounding canonical source context:

> uments
>    can be given to override individual formatting parameters in the current
>    dialect.  For full details about the dialect and formatting parameters, see
>    section :ref:`csv-fmt-params`.
>
>    Each row read from the csv file is returned as a list of strings.  No
>    automatic data type conversion is performed unless the :data:`QUOTE_NONNUMERIC` format
>    option is specified (in which case unquoted fields are transformed into floats).
>
>    A short usage example::
>
>       >>> import csv
>       >>> with open('eggs.csv', newline='') as csvfile:
>       ...     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
>       ...     fo

Review decision / disagreements / resolution: **pending**

## csv-writer

development / csv+gzip / paraphrase / draft

How does csv.writer use its output object?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `csv-writer`:

csv.writer converts data to delimited strings on the supplied file-like object, which must support write().

Alternative `csv-writer`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [3533, 3539)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [3583, 3784)

Labelled source text:

> writer

Surrounding canonical source context:

>  ', quotechar='|')
>       ...     for row in spamreader:
>       ...         print(', '.join(row))
>       Spam, Spam, Spam, Spam, Spam, Baked Beans
>       Spam, Lovely Spam, Wonderful Spam
>
>
> .. function:: writer(csvfile, /, dialect='excel', **fmtparams)
>
>    Return a writer object responsible for converting the user's data into delimited
>    strings on the given file-like object.  *csvfile* can be any object w

Labelled source text:

>    Return a writer object responsible for converting the user's data into delimited
>    strings on the given file-like object.  *csvfile* can be any object with a
>    :meth:`~io.TextIOBase.write` method.

Surrounding canonical source context:

> ader:
>       ...         print(', '.join(row))
>       Spam, Spam, Spam, Spam, Spam, Baked Beans
>       Spam, Lovely Spam, Wonderful Spam
>
>
> .. function:: writer(csvfile, /, dialect='excel', **fmtparams)
>
>    Return a writer object responsible for converting the user's data into delimited
>    strings on the given file-like object.  *csvfile* can be any object with a
>    :meth:`~io.TextIOBase.write` method.  If *csvfile* is a file object, it should be opened with
>    ``newline=''`` [1]_.  An optional *dialect*
>    parameter can be given which is used to define a set of parameters specific to a
>    particul

Review decision / disagreements / resolution: **pending**

## csv-DictReader

development / csv+gzip / exact_api / draft

How are field names determined by csv.DictReader?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Dropped unrelated dictionary-order commentary from the fieldname-selection label.

Fact `csv-DictReader`:

Omitted fieldnames come from the first row, which is excluded from data; supplied fieldnames are used instead and the first row remains data.

Alternative `csv-DictReader`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [6307, 6317)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [6606, 6903)

Labelled source text:

> DictReader

Surrounding canonical source context:

> ew_limit])
>
>    Returns the current maximum field size allowed by the parser. If *new_limit* is
>    given, this becomes the new limit.
>
>
> The :mod:`csv` module defines the following classes:
>
> .. class:: DictReader(f, fieldnames=None, restkey=None, restval=None, \
>                       dialect='excel', *args, **kwds)
>
>    Create an object that operates like a regular reader but maps the
>    information in each ro

Labelled source text:

> The *fieldnames* parameter is a :term:`sequence`.  If *fieldnames* is
>    omitted, the values in the first row of file *f* will be used as the
>    fieldnames and will be omitted from the results. If
>    *fieldnames* is provided, they will be used and the first row will be
>    included in the results.

Surrounding canonical source context:

>  *args, **kwds)
>
>    Create an object that operates like a regular reader but maps the
>    information in each row to a :class:`dict` whose keys are given by the
>    optional *fieldnames* parameter.
>
>    The *fieldnames* parameter is a :term:`sequence`.  If *fieldnames* is
>    omitted, the values in the first row of file *f* will be used as the
>    fieldnames and will be omitted from the results. If
>    *fieldnames* is provided, they will be used and the first row will be
>    included in the results.  Regardless of how the fieldnames are determined,
>    the dictionary preserves their original ordering.
>
>    If a row has more fields than fieldnames, the remaining data is put in a
>    list and stored

Review decision / disagreements / resolution: **pending**

## csv-DictWriter

development / csv+gzip / paraphrase / draft

How does csv.DictWriter map dictionaries onto output columns?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `csv-DictWriter`:

DictWriter maps dictionaries to rows using the fieldnames sequence to determine output-column order.

Alternative `csv-DictWriter`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [8083, 8093)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [8200, 8515)

Labelled source text:

> DictWriter

Surrounding canonical source context:

> :
>        ...         print(row['first_name'], row['last_name'])
>        ...
>        Eric Idle
>        John Cleese
>
>        >>> print(row)
>        {'first_name': 'John', 'last_name': 'Cleese'}
>
>
> .. class:: DictWriter(f, fieldnames, restval='', extrasaction='raise', \
>                       dialect='excel', *args, **kwds)
>
>    Create an object which operates like a regular writer but maps dictionaries
>    onto output

Labelled source text:

>    Create an object which operates like a regular writer but maps dictionaries
>    onto output rows.  The *fieldnames* parameter is a :mod:`sequence
>    <collections.abc>` of keys that identify the order in which values in the
>    dictionary passed to the :meth:`~csvwriter.writerow` method are written to file
>    *f*.

Surrounding canonical source context:

>   >>> print(row)
>        {'first_name': 'John', 'last_name': 'Cleese'}
>
>
> .. class:: DictWriter(f, fieldnames, restval='', extrasaction='raise', \
>                       dialect='excel', *args, **kwds)
>
>    Create an object which operates like a regular writer but maps dictionaries
>    onto output rows.  The *fieldnames* parameter is a :mod:`sequence
>    <collections.abc>` of keys that identify the order in which values in the
>    dictionary passed to the :meth:`~csvwriter.writerow` method are written to file
>    *f*.  The optional *restval* parameter specifies the value to be
>    written if the dictionary is missing a key in *fieldnames*.  If the
>    dictionary passed to the :meth:`~csvwriter.writerow` method conta

Review decision / disagreements / resolution: **pending**

## pickle-dump

development / json+pickle / exact_api / draft

Where does pickle.dump write its serialized representation?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pickle-dump`:

pickle.dump writes the pickled representation of obj to the supplied open file.

Alternative `pickle-dump`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9252, 9256)
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9327, 9490)

Labelled source text:

> dump

Surrounding canonical source context:

> t protocol is 4.
>
>    .. versionchanged:: 3.14
>
>       The default protocol is 5.
>
> The :mod:`pickle` module provides the following functions to make the pickling
> process more convenient:
>
> .. function:: dump(obj, file, protocol=None, *, fix_imports=True, buffer_callback=None)
>
>    Write the pickled representation of the object *obj* to the open
>    :term:`file object` *file*.  This is equivalent to
>    ``Pi

Labelled source text:

>    Write the pickled representation of the object *obj* to the open
>    :term:`file object` *file*.  This is equivalent to
>    ``Pickler(file, protocol).dump(obj)``.

Surrounding canonical source context:

> s 5.
>
> The :mod:`pickle` module provides the following functions to make the pickling
> process more convenient:
>
> .. function:: dump(obj, file, protocol=None, *, fix_imports=True, buffer_callback=None)
>
>    Write the pickled representation of the object *obj* to the open
>    :term:`file object` *file*.  This is equivalent to
>    ``Pickler(file, protocol).dump(obj)``.
>
>    Arguments *file*, *protocol*, *fix_imports* and *buffer_callback* have
>    the same meaning as in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument

Review decision / disagreements / resolution: **pending**

## pickle-dumps

development / json+pickle / paraphrase / draft

What type of result does pickle.dumps return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pickle-dumps`:

pickle.dumps returns the pickled representation as bytes rather than writing it to a file.

Alternative `pickle-dumps`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9717, 9722)
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9787, 9907)

Labelled source text:

> dumps

Surrounding canonical source context:

> tocol*, *fix_imports* and *buffer_callback* have
>    the same meaning as in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was added.
>
> .. function:: dumps(obj, protocol=None, *, fix_imports=True, buffer_callback=None)
>
>    Return the pickled representation of the object *obj* as a :class:`bytes` object,
>    instead of writing it to a file.
>
>    Arguments

Labelled source text:

>    Return the pickled representation of the object *obj* as a :class:`bytes` object,
>    instead of writing it to a file.

Surrounding canonical source context:

> s in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was added.
>
> .. function:: dumps(obj, protocol=None, *, fix_imports=True, buffer_callback=None)
>
>    Return the pickled representation of the object *obj* as a :class:`bytes` object,
>    instead of writing it to a file.
>
>    Arguments *protocol*, *fix_imports* and *buffer_callback* have the same
>    meaning as in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was add

Review decision / disagreements / resolution: **pending**

## pickle-load

development / json+pickle / exact_api / draft

What does pickle.load reconstruct from a file?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pickle-load`:

pickle.load reads a pickled representation from a file and reconstructs its object hierarchy.

Alternative `pickle-load`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [10126, 10130)
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [10208, 10417)

Labelled source text:

> load

Surrounding canonical source context:

> tocol*, *fix_imports* and *buffer_callback* have the same
>    meaning as in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was added.
>
> .. function:: load(file, *, fix_imports=True, encoding="ASCII", errors="strict", buffers=None)
>
>    Read the pickled representation of an object from the open :term:`file object`
>    *file* and return the reconstituted o

Labelled source text:

>    Read the pickled representation of an object from the open :term:`file object`
>    *file* and return the reconstituted object hierarchy specified therein.
>    This is equivalent to ``Unpickler(file).load()``.

Surrounding canonical source context:

> ass:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was added.
>
> .. function:: load(file, *, fix_imports=True, encoding="ASCII", errors="strict", buffers=None)
>
>    Read the pickled representation of an object from the open :term:`file object`
>    *file* and return the reconstituted object hierarchy specified therein.
>    This is equivalent to ``Unpickler(file).load()``.
>
>    The protocol version of the pickle is detected automatically, so no
>    protocol argument is needed.  Bytes past the pickled representation
>    of the object are ignored.
>
>    Arguments *file*, *fix

Review decision / disagreements / resolution: **pending**

## pickle-loads

development / json+pickle / paraphrase / draft

How does pickle.loads reconstruct an object from bytes?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pickle-loads`:

pickle.loads reconstructs the object hierarchy from pickled bytes-like data.

Alternative `pickle-loads`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [10823, 10828)
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [10909, 11051)

Labelled source text:

> loads

Surrounding canonical source context:

> ts*, *encoding*, *errors*, *strict* and *buffers*
>    have the same meaning as in the :class:`Unpickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffers* argument was added.
>
> .. function:: loads(data, /, *, fix_imports=True, encoding="ASCII", errors="strict", buffers=None)
>
>    Return the reconstituted object hierarchy of the pickled representation
>    *data* of an object. *data* must be a :te

Labelled source text:

>    Return the reconstituted object hierarchy of the pickled representation
>    *data* of an object. *data* must be a :term:`bytes-like object`.

Surrounding canonical source context:

> class:`Unpickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffers* argument was added.
>
> .. function:: loads(data, /, *, fix_imports=True, encoding="ASCII", errors="strict", buffers=None)
>
>    Return the reconstituted object hierarchy of the pickled representation
>    *data* of an object. *data* must be a :term:`bytes-like object`.
>
>    The protocol version of the pickle is detected automatically, so no
>    protocol argument is needed.  Bytes past the pickled representation
>    of the object are ignored.
>
>    Arguments *fix_imports

Review decision / disagreements / resolution: **pending**

## hashlib-new

held_out / base64+hashlib / exact_api / draft

How can hashlib create a hash object by algorithm name?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `hashlib-new`:

hashlib.new constructs a hash object using the desired algorithm name as its first argument.

Alternative `hashlib-new`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [4453, 4456)
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [4497, 4739)

Labelled source text:

> new

Surrounding canonical source context:

> ndensed:
>
>    >>> hashlib.sha256(b"Nobody inspects the spammish repetition").hexdigest()
>    '031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406'
>
> Constructors
> ------------
>
> .. function:: new(name[, data], *, usedforsecurity=True)
>
>    Is a generic constructor that takes the string *name* of the desired
>    algorithm as its first parameter.  It also exists to allow access to the
>    above li

Labelled source text:

>    Is a generic constructor that takes the string *name* of the desired
>    algorithm as its first parameter.  It also exists to allow access to the
>    above listed hashes as well as any other algorithms that your OpenSSL
>    library may offer.

Surrounding canonical source context:

> pects the spammish repetition").hexdigest()
>    '031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406'
>
> Constructors
> ------------
>
> .. function:: new(name[, data], *, usedforsecurity=True)
>
>    Is a generic constructor that takes the string *name* of the desired
>    algorithm as its first parameter.  It also exists to allow access to the
>    above listed hashes as well as any other algorithms that your OpenSSL
>    library may offer.
>
> Using :func:`new` with an algorithm name:
>
>    >>> h = hashlib.new('sha256')
>    >>> h.update(b"Nobody inspects the spammish repetition")
>    >>> h.hexdigest()
>    '031edd7d41651593c5fe5c006fa5752b37fdd

Review decision / disagreements / resolution: **pending**

## hashlib-update

held_out / base64+hashlib / paraphrase / draft

What happens when hash.update is called repeatedly?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `hashlib-update`:

Repeated hash.update calls are equivalent to one update with all the input bytes concatenated in order.

Alternative `hashlib-update`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7177, 7188)
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7196, 7423)

Labelled source text:

> hash.update

Surrounding canonical source context:

> s been present in CPython since its inception, but
>       until Python 3.4 was not formally specified, so may not exist on some
>       platforms.
>
> A hash object has the following methods:
>
>
> .. method:: hash.update(data)
>
>    Update the hash object with the :term:`bytes-like object`.
>    Repeated calls are equivalent to a single call with the
>    concatenation of all the arguments: ``m.update(a); m.update(b)`` is

Labelled source text:

>    Update the hash object with the :term:`bytes-like object`.
>    Repeated calls are equivalent to a single call with the
>    concatenation of all the arguments: ``m.update(a); m.update(b)`` is
>    equivalent to ``m.update(a+b)``.

Surrounding canonical source context:

> Python since its inception, but
>       until Python 3.4 was not formally specified, so may not exist on some
>       platforms.
>
> A hash object has the following methods:
>
>
> .. method:: hash.update(data)
>
>    Update the hash object with the :term:`bytes-like object`.
>    Repeated calls are equivalent to a single call with the
>    concatenation of all the arguments: ``m.update(a); m.update(b)`` is
>    equivalent to ``m.update(a+b)``.
>
>
> .. method:: hash.digest()
>
>    Return the digest of the data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole

Review decision / disagreements / resolution: **pending**

## hashlib-digest

held_out / base64+hashlib / exact_api / draft

What representation does hash.digest return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `hashlib-digest`:

hash.digest returns a bytes object of digest_size bytes containing the digest of the data processed so far.

Alternative `hashlib-digest`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7438, 7449)
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7453, 7644)

Labelled source text:

> hash.digest

Surrounding canonical source context:

> bytes-like object`.
>    Repeated calls are equivalent to a single call with the
>    concatenation of all the arguments: ``m.update(a); m.update(b)`` is
>    equivalent to ``m.update(a+b)``.
>
>
> .. method:: hash.digest()
>
>    Return the digest of the data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.
>
>
> ..

Labelled source text:

>    Return the digest of the data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.

Surrounding canonical source context:

> ct`.
>    Repeated calls are equivalent to a single call with the
>    concatenation of all the arguments: ``m.update(a); m.update(b)`` is
>    equivalent to ``m.update(a+b)``.
>
>
> .. method:: hash.digest()
>
>    Return the digest of the data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.
>
>
> .. method:: hash.hexdigest()
>
>    Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.  This may be used to
>    exchange the v

Review decision / disagreements / resolution: **pending**

## hashlib-hexdigest

held_out / base64+hashlib / paraphrase / draft

How does hash.hexdigest differ from a byte digest?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `hashlib-hexdigest`:

hash.hexdigest returns a hexadecimal string twice the byte digest length.

Alternative `hashlib-hexdigest`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7659, 7673)
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7680, 7805)

Labelled source text:

> hash.hexdigest

Surrounding canonical source context:

> urn the digest of the data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.
>
>
> .. method:: hash.hexdigest()
>
>    Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.  This may be used to
>    exchange the value safely in email or other

Labelled source text:

> Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.

Surrounding canonical source context:

>  data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.
>
>
> .. method:: hash.hexdigest()
>
>    Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.  This may be used to
>    exchange the value safely in email or other non-binary environments.
>
>
> .. method:: hash.copy()
>
>    Return a copy ("clone") of the hash object.  This can be used to efficiently

Review decision / disagreements / resolution: **pending**

## base64-b64encode

held_out / base64+hashlib / exact_api / draft

What input and output types are used by base64.b64encode?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `base64-b64encode`:

base64.b64encode accepts a bytes-like input and returns Base64-encoded bytes.

Alternative `base64-b64encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [2034, 2043)
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [2063, 2161)

Labelled source text:

> b64encode

Surrounding canonical source context:

> -----------
>
> The :rfc:`4648` encodings are suitable for encoding binary data so that it can be
> safely sent by email, used as parts of URLs, or included as part of an HTTP
> POST request.
>
> .. function:: b64encode(s, altchars=None)
>
>    Encode the :term:`bytes-like object` *s* using Base64 and return the encoded
>    :class:`bytes`.
>
>    Optional *altchars* must be a :term:`bytes-like object` of length 2 which
>

Labelled source text:

>    Encode the :term:`bytes-like object` *s* using Base64 and return the encoded
>    :class:`bytes`.

Surrounding canonical source context:

> encodings are suitable for encoding binary data so that it can be
> safely sent by email, used as parts of URLs, or included as part of an HTTP
> POST request.
>
> .. function:: b64encode(s, altchars=None)
>
>    Encode the :term:`bytes-like object` *s* using Base64 and return the encoded
>    :class:`bytes`.
>
>    Optional *altchars* must be a :term:`bytes-like object` of length 2 which
>    specifies an alternative alphabet for the ``+`` and ``/`` characters.
>    This allows an application to e.g. generate U

Review decision / disagreements / resolution: **pending**

## base64-b64decode

held_out / base64+hashlib / paraphrase / draft

How can base64.b64decode validate non-alphabet input?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `base64-b64decode`:

With validate=True, non-alphabet characters raise binascii.Error; the default validate=False discards them before the padding check.

Alternative `base64-b64decode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [2654, 2663)
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [3081, 3373)

Labelled source text:

> b64decode

Surrounding canonical source context:

> e64 alphabet is used.
>
>    May assert or raise a :exc:`ValueError` if the length of *altchars* is not 2.  Raises a
>    :exc:`TypeError` if *altchars* is not a :term:`bytes-like object`.
>
>
> .. function:: b64decode(s, altchars=None, validate=False)
>
>    Decode the Base64 encoded :term:`bytes-like object` or ASCII string
>    *s* and return the decoded :class:`bytes`.
>
>    Optional *altchars* must be a :term:`bytes-

Labelled source text:

>    If *validate* is ``False`` (the default), characters that are neither
>    in the normal base-64 alphabet nor the alternative alphabet are
>    discarded prior to the padding check.  If *validate* is ``True``,
>    these non-alphabet characters in the input result in a
>    :exc:`binascii.Error`.

Surrounding canonical source context:

> CII string
>    of length 2 which specifies the alternative alphabet used instead of the
>    ``+`` and ``/`` characters.
>
>    A :exc:`binascii.Error` exception is raised
>    if *s* is incorrectly padded.
>
>    If *validate* is ``False`` (the default), characters that are neither
>    in the normal base-64 alphabet nor the alternative alphabet are
>    discarded prior to the padding check.  If *validate* is ``True``,
>    these non-alphabet characters in the input result in a
>    :exc:`binascii.Error`.
>
>    For more information about the strict base64 check, see :func:`binascii.a2b_base64`
>
>    May assert or raise a :exc:`ValueError` if the length of *altchars* is not 2.
>
> .. function:: standard_b64en

Review decision / disagreements / resolution: **pending**

## base64-urlsafe_b64encode

held_out / base64+hashlib / exact_api / draft

Which characters does URL-safe Base64 substitute?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Scoped the substitution fact to the requested character replacements, not unrelated return type/padding commentary.

Fact `base64-urlsafe_b64encode`:

URL-safe Base64 substitutes - for + and _ for / in the standard alphabet.

Alternative `base64-urlsafe_b64encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [3887, 3904)
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [4006, 4102)

Labelled source text:

> urlsafe_b64encode

Surrounding canonical source context:

> ss:`bytes`.
>
>
> .. function:: standard_b64decode(s)
>
>    Decode :term:`bytes-like object` or ASCII string *s* using the standard
>    Base64 alphabet and return the decoded :class:`bytes`.
>
>
> .. function:: urlsafe_b64encode(s)
>
>    Encode :term:`bytes-like object` *s* using the
>    URL- and filesystem-safe alphabet, which
>    substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
>    standard Base64 alphabet,

Labelled source text:

> substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
>    standard Base64 alphabet

Surrounding canonical source context:

> andard
>    Base64 alphabet and return the decoded :class:`bytes`.
>
>
> .. function:: urlsafe_b64encode(s)
>
>    Encode :term:`bytes-like object` *s* using the
>    URL- and filesystem-safe alphabet, which
>    substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
>    standard Base64 alphabet, and return the encoded :class:`bytes`.  The result
>    can still contain ``=``.
>
>
> .. function:: urlsafe_b64decode(s)
>
>    Decode :term:`bytes-like object` or ASCII string *s*
>    using the URL- and fil

Review decision / disagreements / resolution: **pending**

## base64-b32encode

held_out / base64+hashlib / paraphrase / draft

How do I encode bytes using Base32 in Python?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `base64-b32encode`:

Use base64.b32encode to encode a bytes-like input as Base32 bytes.

Alternative `base64-b32encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [4490, 4499)
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [4504, 4602)

Labelled source text:

> b32encode

Surrounding canonical source context:

> URL- and filesystem-safe
>    alphabet, which substitutes ``-`` instead of ``+`` and ``_`` instead of
>    ``/`` in the standard Base64 alphabet, and return the decoded
>    :class:`bytes`.
>
>
> .. function:: b32encode(s)
>
>    Encode the :term:`bytes-like object` *s* using Base32 and return the
>    encoded :class:`bytes`.
>
>
> .. function:: b32decode(s, casefold=False, map01=None)
>
>    Decode the Base32 encoded :term:`by

Labelled source text:

>    Encode the :term:`bytes-like object` *s* using Base32 and return the
>    encoded :class:`bytes`.

Surrounding canonical source context:

> ystem-safe
>    alphabet, which substitutes ``-`` instead of ``+`` and ``_`` instead of
>    ``/`` in the standard Base64 alphabet, and return the decoded
>    :class:`bytes`.
>
>
> .. function:: b32encode(s)
>
>    Encode the :term:`bytes-like object` *s* using Base32 and return the
>    encoded :class:`bytes`.
>
>
> .. function:: b32decode(s, casefold=False, map01=None)
>
>    Decode the Base32 encoded :term:`bytes-like object` or ASCII string *s* and
>    return the decoded :class:`bytes`.
>
>    Optional *casefold*

Review decision / disagreements / resolution: **pending**

## gzip-open

development / csv+gzip / exact_api / draft

What file object does gzip.open return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `gzip-open`:

gzip.open returns a gzip-compressed file object opened in binary or text mode.

Alternative `gzip-open`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [1081, 1085)
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [1167, 1257)

Labelled source text:

> open

Surrounding canonical source context:

> m:`gzip` and :program:`gunzip` programs, such  as those produced by
> :program:`compress` and :program:`pack`, are not supported by this module.
>
> The module defines the following items:
>
>
> .. function:: open(filename, mode='rb', compresslevel=9, encoding=None, errors=None, newline=None)
>
>    Open a gzip-compressed file in binary or text mode, returning a :term:`file
>    object`.
>
>    The *filename* argument

Labelled source text:

>    Open a gzip-compressed file in binary or text mode, returning a :term:`file
>    object`.

Surrounding canonical source context:

> ` and :program:`pack`, are not supported by this module.
>
> The module defines the following items:
>
>
> .. function:: open(filename, mode='rb', compresslevel=9, encoding=None, errors=None, newline=None)
>
>    Open a gzip-compressed file in binary or text mode, returning a :term:`file
>    object`.
>
>    The *filename* argument can be an actual filename (a :class:`str` or
>    :class:`bytes` object), or an existing file object to read from or write to.
>
>    The *mode* argument can be any of ``'r'``,

Review decision / disagreements / resolution: **pending**

## gzip-compress

development / csv+gzip / paraphrase / draft

How do I compress bytes into gzip format without creating a file?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated configuration/performance text from a label whose question only asks the data/result behaviour.

Fact `gzip-compress`:

gzip.compress compresses data into gzip-format bytes without requiring a file.

Alternative `gzip-compress`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [7750, 7758)
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [7795, 7887)

Labelled source text:

> compress

Surrounding canonical source context:

> thout specifying the *mode*
>       argument is deprecated.
>
>    .. versionchanged:: 3.12
>       Remove the ``filename`` attribute, use the :attr:`~GzipFile.name`
>       attribute instead.
>
>
> .. function:: compress(data, compresslevel=9, *, mtime=0)
>
>    Compress the *data*, returning a :class:`bytes` object containing
>    the compressed data.  *compresslevel* and *mtime* have the same meaning as in
>    the :class

Labelled source text:

>    Compress the *data*, returning a :class:`bytes` object containing
>    the compressed data.

Surrounding canonical source context:

>  deprecated.
>
>    .. versionchanged:: 3.12
>       Remove the ``filename`` attribute, use the :attr:`~GzipFile.name`
>       attribute instead.
>
>
> .. function:: compress(data, compresslevel=9, *, mtime=0)
>
>    Compress the *data*, returning a :class:`bytes` object containing
>    the compressed data.  *compresslevel* and *mtime* have the same meaning as in
>    the :class:`GzipFile` constructor above,
>    but *mtime* defaults to 0 for reproducible output.
>
>    .. versionadded:: 3.2
>    .. versionchang

Review decision / disagreements / resolution: **pending**

## gzip-decompress

development / csv+gzip / exact_api / draft

Can gzip.decompress handle concatenated gzip members?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated configuration/performance text from a label whose question only asks the data/result behaviour.

Fact `gzip-decompress`:

gzip.decompress returns uncompressed bytes and supports concatenated gzip members.

Alternative `gzip-decompress`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [8899, 8909)
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [8917, 9127)

Labelled source text:

> decompress

Surrounding canonical source context:

> versionchanged:: 3.14
>       The *mtime* parameter now defaults to 0 for reproducible output.
>       For the previous behaviour of using the current time,
>       pass ``None`` to *mtime*.
>
> .. function:: decompress(data)
>
>    Decompress the *data*, returning a :class:`bytes` object containing the
>    uncompressed data. This function is capable of decompressing multi-member
>    gzip data (multiple gzip blocks conca

Labelled source text:

>    Decompress the *data*, returning a :class:`bytes` object containing the
>    uncompressed data. This function is capable of decompressing multi-member
>    gzip data (multiple gzip blocks concatenated together).

Surrounding canonical source context:

> .14
>       The *mtime* parameter now defaults to 0 for reproducible output.
>       For the previous behaviour of using the current time,
>       pass ``None`` to *mtime*.
>
> .. function:: decompress(data)
>
>    Decompress the *data*, returning a :class:`bytes` object containing the
>    uncompressed data. This function is capable of decompressing multi-member
>    gzip data (multiple gzip blocks concatenated together). When the data is
>    certain to contain only one member the :func:`zlib.decompress` function with
>    *wbits* set to 31 is faster.
>
>    .. versionadded:: 3.2
>    .. versionchanged:: 3.11
>       Speed is i

Review decision / disagreements / resolution: **pending**

## gzip-GzipFile

development / csv+gzip / paraphrase / draft

What does the GzipFile constructor represent?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `gzip-GzipFile`:

GzipFile provides a file-like object supporting most file-object methods, except truncate; a filename or fileobj must be supplied.

Alternative `gzip-GzipFile`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [2719, 2727)
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [2798, 3055)

Labelled source text:

> GzipFile

Surrounding canonical source context:

> exception raised for invalid gzip files.  It inherits from :exc:`OSError`.
>    :exc:`EOFError` and :exc:`zlib.error` can also be raised for invalid gzip
>    files.
>
>    .. versionadded:: 3.8
>
> .. class:: GzipFile(filename=None, mode=None, compresslevel=9, fileobj=None, mtime=None)
>
>    Constructor for the :class:`GzipFile` class, which simulates most of the
>    methods of a :term:`file object`, with the excepti

Labelled source text:

>    Constructor for the :class:`GzipFile` class, which simulates most of the
>    methods of a :term:`file object`, with the exception of the :meth:`~io.IOBase.truncate`
>    method.  At least one of *fileobj* and *filename* must be given a non-trivial
>    value.

Surrounding canonical source context:

> exc:`EOFError` and :exc:`zlib.error` can also be raised for invalid gzip
>    files.
>
>    .. versionadded:: 3.8
>
> .. class:: GzipFile(filename=None, mode=None, compresslevel=9, fileobj=None, mtime=None)
>
>    Constructor for the :class:`GzipFile` class, which simulates most of the
>    methods of a :term:`file object`, with the exception of the :meth:`~io.IOBase.truncate`
>    method.  At least one of *fileobj* and *filename* must be given a non-trivial
>    value.
>
>    The new class instance is based on *fileobj*, which can be a regular file, an
>    :class:`io.BytesIO` object, or any other object which simulates a file.  It
>    defaults to ``None``, in which case

Review decision / disagreements / resolution: **pending**

## bz2-open

held_out / bz2+sqlite3 / exact_api / draft

What modes does bz2.open support?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The original binary/text description did not enumerate the supported open modes or default.

Fact `bz2-open`:

bz2.open supports read/write/exclusive-create/append in binary or text mode (r/rb, w/wb, x/xb, a/ab; rt/wt/xt/at), defaulting to rb.

Alternative `bz2-open`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [1003, 1007)
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [1387, 1605)

Labelled source text:

> open

Surrounding canonical source context:

> ` classes for
>   incremental (de)compression.
> * The :func:`compress` and :func:`decompress` functions for one-shot
>   (de)compression.
>
>
> (De)compression of files
> ------------------------
>
> .. function:: open(filename, mode='rb', compresslevel=9, encoding=None, errors=None, newline=None)
>
>    Open a bzip2-compressed file in binary or text mode, returning a :term:`file
>    object`.
>
>    As with the constructo

Labelled source text:

> The *mode* argument can be any of ``'r'``, ``'rb'``, ``'w'``, ``'wb'``,
>    ``'x'``, ``'xb'``, ``'a'`` or ``'ab'`` for binary mode, or ``'rt'``,
>    ``'wt'``, ``'xt'``, or ``'at'`` for text mode. The default is ``'rb'``.

Surrounding canonical source context:

>  with the constructor for :class:`BZ2File`, the *filename* argument can be
>    an actual filename (a :class:`str` or :class:`bytes` object), or an existing
>    file object to read from or write to.
>
>    The *mode* argument can be any of ``'r'``, ``'rb'``, ``'w'``, ``'wb'``,
>    ``'x'``, ``'xb'``, ``'a'`` or ``'ab'`` for binary mode, or ``'rt'``,
>    ``'wt'``, ``'xt'``, or ``'at'`` for text mode. The default is ``'rb'``.
>
>    The *compresslevel* argument is an integer from 1 to 9, as for the
>    :class:`BZ2File` constructor.
>
>    For binary mode, this function is equivalent to the :class:`BZ2File`
>    constructor: ``BZ2F

Review decision / disagreements / resolution: **pending**

## bz2-compress

held_out / bz2+sqlite3 / paraphrase / draft

What input does bz2.compress compress?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bz2-compress`:

bz2.compress compresses bytes-like data.

Alternative `bz2-compress`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [9630, 9638)
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [9663, 9731)

Labelled source text:

> compress

Surrounding canonical source context:

> :`.decompress` method can provide more
>       decompressed data before requiring new uncompressed input.
>
>       .. versionadded:: 3.5
>
>
> One-shot (de)compression
> ------------------------
>
> .. function:: compress(data, compresslevel=9)
>
>    Compress *data*, a :term:`bytes-like object <bytes-like object>`.
>
>    *compresslevel*, if given, must be an integer between ``1`` and ``9``. The
>    default is ``9``.
>
>    Fo

Labelled source text:

>    Compress *data*, a :term:`bytes-like object <bytes-like object>`.

Surrounding canonical source context:

>  more
>       decompressed data before requiring new uncompressed input.
>
>       .. versionadded:: 3.5
>
>
> One-shot (de)compression
> ------------------------
>
> .. function:: compress(data, compresslevel=9)
>
>    Compress *data*, a :term:`bytes-like object <bytes-like object>`.
>
>    *compresslevel*, if given, must be an integer between ``1`` and ``9``. The
>    default is ``9``.
>
>    For incremental compression, use a :class:`BZ2Compressor` instead.
>
>
> .. function:: decompress(d

Review decision / disagreements / resolution: **pending**

## bz2-decompress

held_out / bz2+sqlite3 / exact_api / draft

What input does bz2.decompress accept?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bz2-decompress`:

bz2.decompress accepts compressed bytes-like data.

Alternative `bz2-decompress`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [9919, 9929)
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [9937, 10007)

Labelled source text:

> decompress

Surrounding canonical source context:

> ke object>`.
>
>    *compresslevel*, if given, must be an integer between ``1`` and ``9``. The
>    default is ``9``.
>
>    For incremental compression, use a :class:`BZ2Compressor` instead.
>
>
> .. function:: decompress(data)
>
>    Decompress *data*, a :term:`bytes-like object <bytes-like object>`.
>
>    If *data* is the concatenation of multiple compressed streams, decompress
>    all of the streams.
>
>    For incremental

Labelled source text:

>    Decompress *data*, a :term:`bytes-like object <bytes-like object>`.

Surrounding canonical source context:

> compresslevel*, if given, must be an integer between ``1`` and ``9``. The
>    default is ``9``.
>
>    For incremental compression, use a :class:`BZ2Compressor` instead.
>
>
> .. function:: decompress(data)
>
>    Decompress *data*, a :term:`bytes-like object <bytes-like object>`.
>
>    If *data* is the concatenation of multiple compressed streams, decompress
>    all of the streams.
>
>    For incremental decompression, use a :class:`BZ2Decompressor` instead.
>
>    .. versionchanged::

Review decision / disagreements / resolution: **pending**

## bz2-BZ2Compressor

held_out / bz2+sqlite3 / paraphrase / draft

What is the purpose of BZ2Compressor?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bz2-BZ2Compressor`:

BZ2Compressor supports incremental compression; bz2.compress is the one-shot alternative.

Alternative `bz2-BZ2Compressor`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [6498, 6511)
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [6530, 6695)

Labelled source text:

> BZ2Compressor

Surrounding canonical source context:

> le simultaneous
>       readers or writers, just like its equivalent classes in :mod:`gzip` and
>       :mod:`lzma` have always been.
>
>
> Incremental (de)compression
> ---------------------------
>
> .. class:: BZ2Compressor(compresslevel=9)
>
>    Create a new compressor object. This object may be used to compress data
>    incrementally. For one-shot compression, use the :func:`compress` function
>    instead.
>
>    *compressle

Labelled source text:

>    Create a new compressor object. This object may be used to compress data
>    incrementally. For one-shot compression, use the :func:`compress` function
>    instead.

Surrounding canonical source context:

>  writers, just like its equivalent classes in :mod:`gzip` and
>       :mod:`lzma` have always been.
>
>
> Incremental (de)compression
> ---------------------------
>
> .. class:: BZ2Compressor(compresslevel=9)
>
>    Create a new compressor object. This object may be used to compress data
>    incrementally. For one-shot compression, use the :func:`compress` function
>    instead.
>
>    *compresslevel*, if given, must be an integer between ``1`` and ``9``. The
>    default is ``9``.
>
>    .. method:: compress(data)
>
>       Provide data to the compressor object. Returns a chunk of com

Review decision / disagreements / resolution: **pending**

## lzma-open

development / lzma+zlib / exact_api / draft

What modes does lzma.open support?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The original binary/text description did not enumerate the supported open modes or default.

Fact `lzma-open`:

lzma.open supports read/write/exclusive-create/append in binary or text mode (r/rb, w/wb, x/xb, a/ab; rt/wt/xt/at), defaulting to rb.

Alternative `lzma-open`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [1235, 1239)
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [1717, 1935)

Labelled source text:

> open

Surrounding canonical source context:

> rror occurs during compression or
>    decompression, or while initializing the compressor/decompressor state.
>
>
> Reading and writing compressed files
> ------------------------------------
>
> .. function:: open(filename, mode="rb", *, format=None, check=-1, preset=None, filters=None, encoding=None, errors=None, newline=None)
>
>    Open an LZMA-compressed file in binary or text mode, returning a :term:`file
>

Labelled source text:

> The *mode* argument can be any of ``"r"``, ``"rb"``, ``"w"``, ``"wb"``,
>    ``"x"``, ``"xb"``, ``"a"`` or ``"ab"`` for binary mode, or ``"rt"``,
>    ``"wt"``, ``"xt"``, or ``"at"`` for text mode. The default is ``"rb"``.

Surrounding canonical source context:

>  as a
>    :class:`str`, :class:`bytes` or :term:`path-like <path-like object>` object), in
>    which case the named file is opened, or it can be an existing file object
>    to read from or write to.
>
>    The *mode* argument can be any of ``"r"``, ``"rb"``, ``"w"``, ``"wb"``,
>    ``"x"``, ``"xb"``, ``"a"`` or ``"ab"`` for binary mode, or ``"rt"``,
>    ``"wt"``, ``"xt"``, or ``"at"`` for text mode. The default is ``"rb"``.
>
>    When opening a file for reading, the *format* and *filters* arguments have
>    the same meanings as for :class:`LZMADecompressor`. In this case, the *check*
>    and *preset* arguments should not be

Review decision / disagreements / resolution: **pending**

## lzma-compress

development / lzma+zlib / paraphrase / draft

How does lzma.compress return compressed data?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `lzma-compress`:

lzma.compress compresses bytes and returns the compressed data as bytes.

Alternative `lzma-compress`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12613, 12621)
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12684, 12790)

Labelled source text:

> compress

Surrounding canonical source context:

> ttribute:: needs_input
>
>       ``False`` if the :meth:`.decompress` method can provide more
>       decompressed data before requiring new uncompressed input.
>
>       .. versionadded:: 3.5
>
> .. function:: compress(data, format=FORMAT_XZ, check=-1, preset=None, filters=None)
>
>    Compress *data* (a :class:`bytes` object), returning the compressed data as a
>    :class:`bytes` object.
>
>    See :class:`LZMACompressor

Labelled source text:

>    Compress *data* (a :class:`bytes` object), returning the compressed data as a
>    :class:`bytes` object.

Surrounding canonical source context:

> od can provide more
>       decompressed data before requiring new uncompressed input.
>
>       .. versionadded:: 3.5
>
> .. function:: compress(data, format=FORMAT_XZ, check=-1, preset=None, filters=None)
>
>    Compress *data* (a :class:`bytes` object), returning the compressed data as a
>    :class:`bytes` object.
>
>    See :class:`LZMACompressor` above for a description of the *format*, *check*,
>    *preset* and *filters* arguments.
>
>
> .. function:: decompress(data, format=FORMAT_AUTO, memlimit=None, filters=None

Review decision / disagreements / resolution: **pending**

## lzma-decompress

development / lzma+zlib / exact_api / draft

What does the one-shot lzma.decompress function return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `lzma-decompress`:

lzma.decompress returns the uncompressed data as bytes.

Alternative `lzma-decompress`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12926, 12936)
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12993, 13103)

Labelled source text:

> decompress

Surrounding canonical source context:

> t), returning the compressed data as a
>    :class:`bytes` object.
>
>    See :class:`LZMACompressor` above for a description of the *format*, *check*,
>    *preset* and *filters* arguments.
>
>
> .. function:: decompress(data, format=FORMAT_AUTO, memlimit=None, filters=None)
>
>    Decompress *data* (a :class:`bytes` object), returning the uncompressed data
>    as a :class:`bytes` object.
>
>    If *data* is the concatenati

Labelled source text:

>    Decompress *data* (a :class:`bytes` object), returning the uncompressed data
>    as a :class:`bytes` object.

Surrounding canonical source context:

>   See :class:`LZMACompressor` above for a description of the *format*, *check*,
>    *preset* and *filters* arguments.
>
>
> .. function:: decompress(data, format=FORMAT_AUTO, memlimit=None, filters=None)
>
>    Decompress *data* (a :class:`bytes` object), returning the uncompressed data
>    as a :class:`bytes` object.
>
>    If *data* is the concatenation of multiple distinct compressed streams,
>    decompress all of these streams, and return the concatenation of the results.
>
>    See :class:`LZMADecompressor` above fo

Review decision / disagreements / resolution: **pending**

## lzma-LZMACompressor

development / lzma+zlib / paraphrase / draft

Why use LZMACompressor rather than a one-shot operation?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `lzma-LZMACompressor`:

LZMACompressor can compress data incrementally rather than in one shot.

Alternative `lzma-LZMACompressor`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [5878, 5892)
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [5949, 6029)

Labelled source text:

> LZMACompressor

Surrounding canonical source context:

> gument of
>       ``None``.
>
>    .. versionchanged:: 3.6
>       Accepts a :term:`path-like object`.
>
>
> Compressing and decompressing data in memory
> --------------------------------------------
>
> .. class:: LZMACompressor(format=FORMAT_XZ, check=-1, preset=None, filters=None)
>
>    Create a compressor object, which can be used to compress data incrementally.
>
>    For a more convenient way of compressing a single chunk of

Labelled source text:

>    Create a compressor object, which can be used to compress data incrementally.

Surrounding canonical source context:

> term:`path-like object`.
>
>
> Compressing and decompressing data in memory
> --------------------------------------------
>
> .. class:: LZMACompressor(format=FORMAT_XZ, check=-1, preset=None, filters=None)
>
>    Create a compressor object, which can be used to compress data incrementally.
>
>    For a more convenient way of compressing a single chunk of data, see
>    :func:`compress`.
>
>    The *format* argument specifies what container format should be used.
>    Possible values are:
>
>    * :

Review decision / disagreements / resolution: **pending**

## zlib-adler32

development / lzma+zlib / exact_api / draft

What kind of checksum does zlib.adler32 calculate?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated running-checksum defaults and security commentary while retaining checksum identity and result type.

Fact `zlib-adler32`:

zlib.adler32 computes an Adler-32 checksum and returns an unsigned 32-bit integer.

Alternative `zlib-adler32`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1174, 1181)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1201, 1241)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1342, 1386)

Labelled source text:

> adler32

Surrounding canonical source context:

> .gz`` files see the :mod:`gzip` module.
>
> The available exception and functions in this module are:
>
>
> .. exception:: error
>
>    Exception raised on compression and decompression errors.
>
>
> .. function:: adler32(data[, value])
>
>    Computes an Adler-32 checksum of *data*.  (An Adler-32 checksum is almost as
>    reliable as a CRC32 but can be computed much more quickly.)  The result
>    is an unsigned 32-bit int

Labelled source text:

> Computes an Adler-32 checksum of *data*.

Surrounding canonical source context:

> zip` module.
>
> The available exception and functions in this module are:
>
>
> .. exception:: error
>
>    Exception raised on compression and decompression errors.
>
>
> .. function:: adler32(data[, value])
>
>    Computes an Adler-32 checksum of *data*.  (An Adler-32 checksum is almost as
>    reliable as a CRC32 but can be computed much more quickly.)  The result
>    is an unsigned 32-bit integer.  If *value* is present, it is used as
>    the starting

Labelled source text:

> The result
>    is an unsigned 32-bit integer.

Surrounding canonical source context:

> ression errors.
>
>
> .. function:: adler32(data[, value])
>
>    Computes an Adler-32 checksum of *data*.  (An Adler-32 checksum is almost as
>    reliable as a CRC32 but can be computed much more quickly.)  The result
>    is an unsigned 32-bit integer.  If *value* is present, it is used as
>    the starting value of the checksum; otherwise, a default value of 1
>    is used.  Passing in *value* allows computing a running checksum over the
>    concatenat

Review decision / disagreements / resolution: **pending**

## zlib-crc32

development / lzma+zlib / paraphrase / draft

What kind of checksum does zlib.crc32 return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated running-checksum defaults and security commentary while retaining checksum identity and result type.

Fact `zlib-crc32`:

zlib.crc32 computes a CRC checksum and returns an unsigned 32-bit integer.

Alternative `zlib-crc32`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [5608, 5613)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [5734, 5794)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [5795, 5839)

Labelled source text:

> crc32

Surrounding canonical source context:

> bsequences
>    that are expected to be most common should come at the end of the dictionary.
>
>    .. versionchanged:: 3.3
>       Added the *zdict* parameter and keyword argument support.
>
>
> .. function:: crc32(data[, value])
>
>    .. index::
>       single: Cyclic Redundancy Check
>       single: checksum; Cyclic Redundancy Check
>
>    Computes a CRC (Cyclic Redundancy Check) checksum of *data*. The
>    result is a

Labelled source text:

> Computes a CRC (Cyclic Redundancy Check) checksum of *data*.

Surrounding canonical source context:

> Added the *zdict* parameter and keyword argument support.
>
>
> .. function:: crc32(data[, value])
>
>    .. index::
>       single: Cyclic Redundancy Check
>       single: checksum; Cyclic Redundancy Check
>
>    Computes a CRC (Cyclic Redundancy Check) checksum of *data*. The
>    result is an unsigned 32-bit integer. If *value* is present, it is used
>    as the starting value of the checksum; otherwise, a default value of 0
>    is used.  Passing in *value* allows computi

Labelled source text:

> The
>    result is an unsigned 32-bit integer.

Surrounding canonical source context:

> . function:: crc32(data[, value])
>
>    .. index::
>       single: Cyclic Redundancy Check
>       single: checksum; Cyclic Redundancy Check
>
>    Computes a CRC (Cyclic Redundancy Check) checksum of *data*. The
>    result is an unsigned 32-bit integer. If *value* is present, it is used
>    as the starting value of the checksum; otherwise, a default value of 0
>    is used.  Passing in *value* allows computing a running checksum over the
>    concatenati

Review decision / disagreements / resolution: **pending**

## zlib-compress

development / lzma+zlib / exact_api / draft

What does zlib.compress return for its data argument?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated configuration/performance text from a label whose question only asks the data/result behaviour.

Fact `zlib-compress`:

zlib.compress returns bytes containing the compressed input data.

Alternative `zlib-compress`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1933, 1941)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1979, 2066)

Labelled source text:

> compress

Surrounding canonical source context:

>   the algorithm is designed for use as a checksum algorithm, it is not suitable
>    for use as a general hash algorithm.
>
>    .. versionchanged:: 3.0
>       The result is always unsigned.
>
> .. function:: compress(data, /, level=-1, wbits=MAX_WBITS)
>
>    Compresses the bytes in *data*, returning a bytes object containing compressed data.
>    *level* is an integer from ``0`` to ``9`` or ``-1`` controlling the lev

Labelled source text:

>    Compresses the bytes in *data*, returning a bytes object containing compressed data.

Surrounding canonical source context:

> sum algorithm, it is not suitable
>    for use as a general hash algorithm.
>
>    .. versionchanged:: 3.0
>       The result is always unsigned.
>
> .. function:: compress(data, /, level=-1, wbits=MAX_WBITS)
>
>    Compresses the bytes in *data*, returning a bytes object containing compressed data.
>    *level* is an integer from ``0`` to ``9`` or ``-1`` controlling the level of compression;
>    ``1`` (Z_BEST_SPEED) is fastest and produces the least compression, ``9`` (Z_BEST_COMPRESSION)
>    is sl

Review decision / disagreements / resolution: **pending**

## zlib-decompress

development / lzma+zlib / paraphrase / draft

Which input does zlib.decompress expand?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated configuration/performance text from a label whose question only asks the data/result behaviour.

Fact `zlib-decompress`:

zlib.decompress decompresses the input bytes and returns uncompressed bytes.

Alternative `zlib-decompress`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [6385, 6395)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [6445, 6543)

Labelled source text:

> decompress

Surrounding canonical source context:

>   the algorithm is designed for use as a checksum algorithm, it is not suitable
>    for use as a general hash algorithm.
>
>    .. versionchanged:: 3.0
>       The result is always unsigned.
>
> .. function:: decompress(data, /, wbits=MAX_WBITS, bufsize=DEF_BUF_SIZE)
>
>    Decompresses the bytes in *data*, returning a bytes object containing the
>    uncompressed data.  The *wbits* parameter depends on
>    the format of

Labelled source text:

>    Decompresses the bytes in *data*, returning a bytes object containing the
>    uncompressed data.

Surrounding canonical source context:

>  it is not suitable
>    for use as a general hash algorithm.
>
>    .. versionchanged:: 3.0
>       The result is always unsigned.
>
> .. function:: decompress(data, /, wbits=MAX_WBITS, bufsize=DEF_BUF_SIZE)
>
>    Decompresses the bytes in *data*, returning a bytes object containing the
>    uncompressed data.  The *wbits* parameter depends on
>    the format of *data*, and is discussed further below.
>    If *bufsize* is given, it is used as the initial size of the output
>    buffer.  Raises the :exc:`error` e

Review decision / disagreements / resolution: **pending**

## sqlite3-connect

held_out / bz2+sqlite3 / exact_api / draft

What does sqlite3.connect return for a database path?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the explicit return type; opening a connection alone does not label the requested result type.
- Added the independently sufficient tutorial call and return-type explanation.

Fact `sqlite3-connect`:

sqlite3.connect opens the database and returns a sqlite3.Connection object.

Alternative `sqlite3-connect`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [8775, 8782)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [9083, 9126)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [12377, 12404)

Labelled source text:

> connect

Surrounding canonical source context:

> ence
> ---------
>
> .. We keep the old sqlite3-module-contents ref to prevent breaking links.
> .. _sqlite3-module-contents:
>
> .. _sqlite3-module-functions:
>
> Module functions
> ^^^^^^^^^^^^^^^^
>
> .. function:: connect(database, timeout=5.0, detect_types=0, \
>                       isolation_level="DEFERRED", check_same_thread=True, \
>                       factory=sqlite3.Connection, cached_statements=128, \
>

Labelled source text:

>    Open a connection to an SQLite database.

Surrounding canonical source context:

> e_thread=True, \
>                       factory=sqlite3.Connection, cached_statements=128, \
>                       uri=False, *, \
>                       autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL)
>
>    Open a connection to an SQLite database.
>
>    :param database:
>        The path to the database file to be opened.
>        You can pass ``":memory:"`` to create an `SQLite database existing only
>        in memory <https://sqlite.org/inmemorydb.

Labelled source text:

> :rtype: ~sqlite3.Connection

Surrounding canonical source context:

> n.
>        *autocommit* currently defaults to
>        :const:`~sqlite3.LEGACY_TRANSACTION_CONTROL`.
>        The default will change to ``False`` in a future Python release.
>    :type autocommit: bool
>
>    :rtype: ~sqlite3.Connection
>
>    .. audit-event:: sqlite3.connect database sqlite3.connect
>    .. audit-event:: sqlite3.connect/handle connection_handle sqlite3.connect
>
>    .. versionchanged:: 3.4
>       Added the *uri* parameter.

Alternative `sqlite3-connect-tutorial`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [2723, 2762)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [2764, 2862)

Labelled source text:

>    con = sqlite3.connect("tutorial.db")

Surrounding canonical source context:

> all :func:`sqlite3.connect` to create a connection to
> the database :file:`tutorial.db` in the current working directory,
> implicitly creating it if it does not exist:
>
> .. testcode::
>
>    import sqlite3
>    con = sqlite3.connect("tutorial.db")
>
> The returned :class:`Connection` object ``con``
> represents the connection to the on-disk database.
>
> In order to execute SQL statements and fetch results from SQL queries,
> we will need to use a datab

Labelled source text:

> The returned :class:`Connection` object ``con``
> represents the connection to the on-disk database.

Surrounding canonical source context:

> onnection to
> the database :file:`tutorial.db` in the current working directory,
> implicitly creating it if it does not exist:
>
> .. testcode::
>
>    import sqlite3
>    con = sqlite3.connect("tutorial.db")
>
> The returned :class:`Connection` object ``con``
> represents the connection to the on-disk database.
>
> In order to execute SQL statements and fetch results from SQL queries,
> we will need to use a database cursor.
> Call :meth:`con.cursor() <Connection.cursor>` to create the :class:`Cursor`:
>
> .. testcod

Review decision / disagreements / resolution: **pending**

## sqlite3-complete_statement

held_out / bz2+sqlite3 / paraphrase / draft

What does sqlite3.complete_statement check about SQL text?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `sqlite3-complete_statement`:

complete_statement checks for a semicolon-terminated statement with no unclosed string literals; it does not validate SQL syntax.

Alternative `sqlite3-complete_statement`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [13152, 13170)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [13183, 13469)

Labelled source text:

> complete_statement

Surrounding canonical source context:

> tect_types*,
>       *isolation_level*, *check_same_thread*, *factory*, *cached_statements*,
>       and *uri* is deprecated.
>       They will become keyword-only parameters in Python 3.15.
>
> .. function:: complete_statement(statement)
>
>    Return ``True`` if the string *statement* appears to contain
>    one or more complete SQL statements.
>    No syntactic verification or parsing of any kind is performed,
>    other than che

Labelled source text:

>    Return ``True`` if the string *statement* appears to contain
>    one or more complete SQL statements.
>    No syntactic verification or parsing of any kind is performed,
>    other than checking that there are no unclosed string literals
>    and the statement is terminated by a semicolon.

Surrounding canonical source context:

> evel*, *check_same_thread*, *factory*, *cached_statements*,
>       and *uri* is deprecated.
>       They will become keyword-only parameters in Python 3.15.
>
> .. function:: complete_statement(statement)
>
>    Return ``True`` if the string *statement* appears to contain
>    one or more complete SQL statements.
>    No syntactic verification or parsing of any kind is performed,
>    other than checking that there are no unclosed string literals
>    and the statement is terminated by a semicolon.
>
>    For example:
>
>    .. doctest::
>
>       >>> sqlite3.complete_statement("SELECT foo FROM bar;")
>       True
>       >>> sqlite3.complete_statement("SELECT foo")
>       False
>
>    This function may be usef

Review decision / disagreements / resolution: **pending**

## sqlite3-register_adapter

held_out / bz2+sqlite3 / exact_api / draft

How does sqlite3.register_adapter convert a Python type?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `sqlite3-register_adapter`:

register_adapter registers a callable receiving an object of the named Python type and returning a value of a native SQLite type.

Alternative `sqlite3-register_adapter`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14596, 14612)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14632, 14909)

Labelled source text:

> register_adapter

Surrounding canonical source context:

> n user-defined function callbacks are logged as unraisable exceptions.
>       Use an :func:`unraisable hook handler <sys.unraisablehook>` for
>       introspection of the failed callback.
>
> .. function:: register_adapter(type, adapter, /)
>
>    Register an *adapter* :term:`callable` to adapt the Python type *type*
>    into an SQLite type.
>    The adapter is called with a Python object of type *type* as its sole
>    argume

Labelled source text:

>    Register an *adapter* :term:`callable` to adapt the Python type *type*
>    into an SQLite type.
>    The adapter is called with a Python object of type *type* as its sole
>    argument, and must return a value of a
>    :ref:`type that SQLite natively understands <sqlite3-types>`.

Surrounding canonical source context:

> e logged as unraisable exceptions.
>       Use an :func:`unraisable hook handler <sys.unraisablehook>` for
>       introspection of the failed callback.
>
> .. function:: register_adapter(type, adapter, /)
>
>    Register an *adapter* :term:`callable` to adapt the Python type *type*
>    into an SQLite type.
>    The adapter is called with a Python object of type *type* as its sole
>    argument, and must return a value of a
>    :ref:`type that SQLite natively understands <sqlite3-types>`.
>
> .. function:: register_converter(typename, converter, /)
>
>    Register the *converter* :term:`callable` to convert SQLite objects of type
>    *typename* into a Python object of a specific type.
>    The

Review decision / disagreements / resolution: **pending**

## sqlite3-register_converter

held_out / bz2+sqlite3 / paraphrase / draft

How does sqlite3.register_converter restore a named SQL type?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `sqlite3-register_converter`:

register_converter registers a callable receiving bytes for the named SQLite type and returning an object of the desired Python type.

Alternative `sqlite3-register_converter`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14925, 14943)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14969, 15385)

Labelled source text:

> register_converter

Surrounding canonical source context:

> ype.
>    The adapter is called with a Python object of type *type* as its sole
>    argument, and must return a value of a
>    :ref:`type that SQLite natively understands <sqlite3-types>`.
>
> .. function:: register_converter(typename, converter, /)
>
>    Register the *converter* :term:`callable` to convert SQLite objects of type
>    *typename* into a Python object of a specific type.
>    The converter is invoked for all SQLi

Labelled source text:

>    Register the *converter* :term:`callable` to convert SQLite objects of type
>    *typename* into a Python object of a specific type.
>    The converter is invoked for all SQLite values of type *typename*;
>    it is passed a :class:`bytes` object and should return an object of the
>    desired Python type.
>    Consult the parameter *detect_types* of
>    :func:`connect` for information regarding how type detection works.

Surrounding canonical source context:

> object of type *type* as its sole
>    argument, and must return a value of a
>    :ref:`type that SQLite natively understands <sqlite3-types>`.
>
> .. function:: register_converter(typename, converter, /)
>
>    Register the *converter* :term:`callable` to convert SQLite objects of type
>    *typename* into a Python object of a specific type.
>    The converter is invoked for all SQLite values of type *typename*;
>    it is passed a :class:`bytes` object and should return an object of the
>    desired Python type.
>    Consult the parameter *detect_types* of
>    :func:`connect` for information regarding how type detection works.
>
>    Note: *typename* and the name of the type in your query are matched
>    case-insensitively.
>
>
> .. _sqlite3-module-constants:
>
> Module constants
> ^^^^^^^^^^^^^^^^
>
> .. data:: LEGACY_TRANSACTION_CONTROL

Review decision / disagreements / resolution: **pending**

## pathlib-PurePath

development / pathlib+shutil / exact_api / draft

When should PurePath be used instead of a concrete path?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old span described flavour selection, not the reason to use pure paths instead of concrete paths.

Fact `pathlib-PurePath`:

Use a pure path class to manipulate paths without accessing the filesystem/OS; PurePath chooses the current system’s pure path flavour.

Alternative `pathlib-PurePath`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [3392, 3400)
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [3417, 3571)
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [1635, 1863)

Labelled source text:

> PurePath

Surrounding canonical source context:

> aths
> ----------
>
> Pure path objects provide path-handling operations which don't actually
> access a filesystem.  There are three ways to access these classes, which
> we also call *flavours*:
>
> .. class:: PurePath(*pathsegments)
>
>    A generic class that represents the system's path flavour (instantiating
>    it creates either a :class:`PurePosixPath` or a :class:`PureWindowsPath`)::
>
>       >>> PurePath('setup.p

Labelled source text:

>    A generic class that represents the system's path flavour (instantiating
>    it creates either a :class:`PurePosixPath` or a :class:`PureWindowsPath`)::

Surrounding canonical source context:

> h objects provide path-handling operations which don't actually
> access a filesystem.  There are three ways to access these classes, which
> we also call *flavours*:
>
> .. class:: PurePath(*pathsegments)
>
>    A generic class that represents the system's path flavour (instantiating
>    it creates either a :class:`PurePosixPath` or a :class:`PureWindowsPath`)::
>
>       >>> PurePath('setup.py')      # Running on a Unix machine
>       PurePosixPath('setup.py')
>
>    Each element of *pathsegments* can be either a string representing a
>    path segment, or an object

Labelled source text:

> #. You want to make sure that your code only manipulates paths without actually
>    accessing the OS. In this case, instantiating one of the pure classes may be
>    useful since those simply don't have any OS-accessing operations.

Surrounding canonical source context:

>  If you want to manipulate Windows paths on a Unix machine (or vice versa).
>    You cannot instantiate a :class:`WindowsPath` when running on Unix, but you
>    can instantiate :class:`PureWindowsPath`.
> #. You want to make sure that your code only manipulates paths without actually
>    accessing the OS. In this case, instantiating one of the pure classes may be
>    useful since those simply don't have any OS-accessing operations.
>
> .. seealso::
>    :pep:`428`: The pathlib module -- object-oriented filesystem paths.
>
> .. seealso::
>    For low-level path manipulation on strings, you can also use the
>    :mod:`os.path` module.
>
>
> Basi

Review decision / disagreements / resolution: **pending**

## pathlib-PurePosixPath

development / pathlib+shutil / paraphrase / draft

Which filesystem flavor does PurePosixPath represent?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pathlib-PurePosixPath`:

PurePosixPath represents non-Windows filesystem paths.

Alternative `pathlib-PurePosixPath`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [5584, 5597)
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [5614, 5712)

Labelled source text:

> PurePosixPath

Surrounding canonical source context:

> the :class:`os.PathLike` interface, allowing them
>    to be used anywhere the interface is accepted.
>
>    .. versionchanged:: 3.6
>       Added support for the :class:`os.PathLike` interface.
>
> .. class:: PurePosixPath(*pathsegments)
>
>    A subclass of :class:`PurePath`, this path flavour represents non-Windows
>    filesystem paths::
>
>       >>> PurePosixPath('/etc/hosts')
>       PurePosixPath('/etc/hosts')
>
>    *pathse

Labelled source text:

>    A subclass of :class:`PurePath`, this path flavour represents non-Windows
>    filesystem paths::

Surrounding canonical source context:

> face, allowing them
>    to be used anywhere the interface is accepted.
>
>    .. versionchanged:: 3.6
>       Added support for the :class:`os.PathLike` interface.
>
> .. class:: PurePosixPath(*pathsegments)
>
>    A subclass of :class:`PurePath`, this path flavour represents non-Windows
>    filesystem paths::
>
>       >>> PurePosixPath('/etc/hosts')
>       PurePosixPath('/etc/hosts')
>
>    *pathsegments* is specified similarly to :class:`PurePath`.
>
> .. class:: PureWindowsPath(*pathsegments)
>
>    A subclass of :

Review decision / disagreements / resolution: **pending**

## pathlib-PureWindowsPath

development / pathlib+shutil / exact_api / draft

Which filesystem flavor does PureWindowsPath represent?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pathlib-PureWindowsPath`:

PureWindowsPath represents Windows filesystem paths, including UNC paths.

Alternative `pathlib-PureWindowsPath`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [5862, 5877)
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [5894, 6012)

Labelled source text:

> PureWindowsPath

Surrounding canonical source context:

> avour represents non-Windows
>    filesystem paths::
>
>       >>> PurePosixPath('/etc/hosts')
>       PurePosixPath('/etc/hosts')
>
>    *pathsegments* is specified similarly to :class:`PurePath`.
>
> .. class:: PureWindowsPath(*pathsegments)
>
>    A subclass of :class:`PurePath`, this path flavour represents Windows
>    filesystem paths, including `UNC paths`_::
>
>       >>> PureWindowsPath('c:/', 'Users', 'Ximénez')
>       Pure

Labelled source text:

>    A subclass of :class:`PurePath`, this path flavour represents Windows
>    filesystem paths, including `UNC paths`_::

Surrounding canonical source context:

> filesystem paths::
>
>       >>> PurePosixPath('/etc/hosts')
>       PurePosixPath('/etc/hosts')
>
>    *pathsegments* is specified similarly to :class:`PurePath`.
>
> .. class:: PureWindowsPath(*pathsegments)
>
>    A subclass of :class:`PurePath`, this path flavour represents Windows
>    filesystem paths, including `UNC paths`_::
>
>       >>> PureWindowsPath('c:/', 'Users', 'Ximénez')
>       PureWindowsPath('c:/Users/Ximénez')
>       >>> PureWindowsPath('//server/share/file')
>       PureWindowsPath('//server/share/file')
>
>    *path

Review decision / disagreements / resolution: **pending**

## pathlib-Path

development / pathlib+shutil / paraphrase / draft

Which concrete path flavor is created by pathlib.Path?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pathlib-Path`:

Path creates a concrete PosixPath or WindowsPath according to the current system’s path flavour.

Alternative `pathlib-Path`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [23847, 23851)
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [23868, 24058)

Labelled source text:

> Path

Surrounding canonical source context:

> he pure path classes.  In addition to
> operations provided by the latter, they also provide methods to do system
> calls on path objects.  There are three ways to instantiate concrete paths:
>
> .. class:: Path(*pathsegments)
>
>    A subclass of :class:`PurePath`, this class represents concrete paths of
>    the system's path flavour (instantiating it creates either a
>    :class:`PosixPath` or a :class:`WindowsP

Labelled source text:

>    A subclass of :class:`PurePath`, this class represents concrete paths of
>    the system's path flavour (instantiating it creates either a
>    :class:`PosixPath` or a :class:`WindowsPath`)::

Surrounding canonical source context:

>   In addition to
> operations provided by the latter, they also provide methods to do system
> calls on path objects.  There are three ways to instantiate concrete paths:
>
> .. class:: Path(*pathsegments)
>
>    A subclass of :class:`PurePath`, this class represents concrete paths of
>    the system's path flavour (instantiating it creates either a
>    :class:`PosixPath` or a :class:`WindowsPath`)::
>
>       >>> Path('setup.py')
>       PosixPath('setup.py')
>
>    *pathsegments* is specified similarly to :class:`PurePath`.
>
> .. class:: PosixPath(*pathsegments)
>
>    A subclass of :class:`Path` and :class

Review decision / disagreements / resolution: **pending**

## shutil-copyfile

development / pathlib+shutil / exact_api / draft

Does shutil.copyfile copy file metadata?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `shutil-copyfile`:

shutil.copyfile copies file contents without metadata.

Alternative `shutil-copyfile`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [2252, 2260)
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [2297, 2533)

Labelled source text:

> copyfile

Surrounding canonical source context:

> HTTP stream),
>    you must ensure that you have called :func:`~io.IOBase.flush` or
>    :func:`~io.IOBase.close` on the file-like object before attempting to read
>    the destination file.
>
> .. function:: copyfile(src, dst, *, follow_symlinks=True)
>
>    Copy the contents (no metadata) of the file named *src* to a file named
>    *dst* and return *dst* in the most efficient way possible.
>    *src* and *dst* are :te

Labelled source text:

>    Copy the contents (no metadata) of the file named *src* to a file named
>    *dst* and return *dst* in the most efficient way possible.
>    *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings.

Surrounding canonical source context:

> e called :func:`~io.IOBase.flush` or
>    :func:`~io.IOBase.close` on the file-like object before attempting to read
>    the destination file.
>
> .. function:: copyfile(src, dst, *, follow_symlinks=True)
>
>    Copy the contents (no metadata) of the file named *src* to a file named
>    *dst* and return *dst* in the most efficient way possible.
>    *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings.
>
>    *dst* must be the complete target file name; look at :func:`~shutil.copy`
>    for a copy that accepts a target directory path.  If *src* and *dst*
>    specify the same file, :exc:`SameFileError` is

Review decision / disagreements / resolution: **pending**

## shutil-copy

development / pathlib+shutil / paraphrase / draft

What does shutil.copy preserve besides file contents?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Replaced destination-path behaviour with the missing permission-mode/metadata explanation.

Fact `shutil-copy`:

shutil.copy copies file contents and permission mode; other metadata such as creation/modification times is not preserved.

Alternative `shutil-copy`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [6832, 6836)
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [7472, 7658)

Labelled source text:

> copy

Surrounding canonical source context:

>  information.
>
>    .. audit-event:: shutil.copystat src,dst shutil.copystat
>
>    .. versionchanged:: 3.3
>       Added *follow_symlinks* argument and support for Linux extended attributes.
>
> .. function:: copy(src, dst, *, follow_symlinks=True)
>
>    Copies the file *src* to the file or directory *dst*.  *src* and *dst*
>    should be :term:`path-like objects <path-like object>` or strings.  If
>    *dst* specif

Labelled source text:

> :func:`~shutil.copy` copies the file data and the file's permission
>    mode (see :func:`os.chmod`).  Other metadata, like the
>    file's creation and modification times, is not preserved.

Surrounding canonical source context:

> lse, and *src* is a symbolic link,
>    *dst* will be created as a symbolic link.  If *follow_symlinks*
>    is true and *src* is a symbolic link, *dst* will be a copy of
>    the file *src* refers to.
>
>    :func:`~shutil.copy` copies the file data and the file's permission
>    mode (see :func:`os.chmod`).  Other metadata, like the
>    file's creation and modification times, is not preserved.
>    To preserve all file metadata from the original, use
>    :func:`~shutil.copy2` instead.
>
>    .. audit-event:: shutil.copyfile src,dst shutil.copy
>
>    .. audit-event:: shutil.copymode src,dst shutil.

Review decision / disagreements / resolution: **pending**

## shutil-copy2

development / pathlib+shutil / exact_api / draft

How does shutil.copy2 differ from shutil.copy?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `shutil-copy2`:

copy2 behaves like copy but also attempts to preserve file metadata.

Alternative `shutil-copy2`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [8218, 8223)
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [8260, 8366)

Labelled source text:

> copy2

Surrounding canonical source context:

> tform-specific fast-copy syscalls may be used internally in order to
>       copy the file more efficiently. See
>       :ref:`shutil-platform-dependent-efficient-copy-operations` section.
>
> .. function:: copy2(src, dst, *, follow_symlinks=True)
>
>    Identical to :func:`~shutil.copy` except that :func:`copy2`
>    also attempts to preserve file metadata.
>
>    When *follow_symlinks* is false, and *src* is a symb

Labelled source text:

>    Identical to :func:`~shutil.copy` except that :func:`copy2`
>    also attempts to preserve file metadata.

Surrounding canonical source context:

> sed internally in order to
>       copy the file more efficiently. See
>       :ref:`shutil-platform-dependent-efficient-copy-operations` section.
>
> .. function:: copy2(src, dst, *, follow_symlinks=True)
>
>    Identical to :func:`~shutil.copy` except that :func:`copy2`
>    also attempts to preserve file metadata.
>
>    When *follow_symlinks* is false, and *src* is a symbolic
>    link, :func:`copy2` attempts to copy all metadata from the
>    *src* symbolic link to the newly created *dst* symbolic link.
>    However,

Review decision / disagreements / resolution: **pending**

## shutil-rmtree

development / pathlib+shutil / paraphrase / draft

What does shutil.rmtree remove?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `shutil-rmtree`:

shutil.rmtree deletes a directory tree; its path must name a directory, not a symbolic link to one.

Alternative `shutil-rmtree`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [13143, 13149)
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [13266, 13376)

Labelled source text:

> rmtree

Surrounding canonical source context:

>     copy the file more efficiently. See
>       :ref:`shutil-platform-dependent-efficient-copy-operations` section.
>
>    .. versionchanged:: 3.8
>       Added the *dirs_exist_ok* parameter.
>
> .. function:: rmtree(path, ignore_errors=False, onerror=None, *, onexc=None, dir_fd=None)
>
>    .. index:: single: directory; deleting
>
>    Delete an entire directory tree; *path* must point to a directory (but not a
>    sym

Labelled source text:

> Delete an entire directory tree; *path* must point to a directory (but not a
>    symbolic link to a directory).

Surrounding canonical source context:

> rsionchanged:: 3.8
>       Added the *dirs_exist_ok* parameter.
>
> .. function:: rmtree(path, ignore_errors=False, onerror=None, *, onexc=None, dir_fd=None)
>
>    .. index:: single: directory; deleting
>
>    Delete an entire directory tree; *path* must point to a directory (but not a
>    symbolic link to a directory).  If *ignore_errors* is true, errors resulting
>    from failed removals will be ignored; if false or omitted, such errors are
>    handled by calling a handler specified by *onexc* or *onerror* or, if bo

Review decision / disagreements / resolution: **pending**

## tempfile-TemporaryFile

held_out / tempfile+fnmatch / exact_api / draft

How is a tempfile.TemporaryFile cleaned up?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `tempfile-TemporaryFile`:

TemporaryFile is destroyed when closed, including implicit close during garbage collection.

Alternative `tempfile-TemporaryFile`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [1323, 1336)
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [1602, 1720)

Labelled source text:

> TemporaryFile

Surrounding canonical source context:

> .
> To maintain backward compatibility, the argument order is somewhat odd; it
> is recommended to use keyword arguments for clarity.
>
> The module defines the following user-callable items:
>
> .. function:: TemporaryFile(mode='w+b', buffering=-1, encoding=None, newline=None, suffix=None, prefix=None, dir=None, *, errors=None)
>
>    Return a :term:`file-like object` that can be used as a temporary storage area.
>    The f

Labelled source text:

> It will be destroyed as soon
>    as it is closed (including an implicit close when the object is garbage
>    collected).

Surrounding canonical source context:

> e, prefix=None, dir=None, *, errors=None)
>
>    Return a :term:`file-like object` that can be used as a temporary storage area.
>    The file is created securely, using the same rules as :func:`mkstemp`. It will be destroyed as soon
>    as it is closed (including an implicit close when the object is garbage
>    collected).  Under Unix, the directory entry for the file is either not created at all or is removed
>    immediately after the file is created.  Other platforms do not support
>    this; your code should not rely o

Review decision / disagreements / resolution: **pending**

## tempfile-NamedTemporaryFile

held_out / tempfile+fnmatch / paraphrase / draft

Does NamedTemporaryFile have a visible name in the filesystem?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `tempfile-NamedTemporaryFile`:

NamedTemporaryFile is guaranteed to have a visible filesystem name.

Alternative `tempfile-NamedTemporaryFile`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [3357, 3375)
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [3627, 3722)

Labelled source text:

> NamedTemporaryFile

Surrounding canonical source context:

> lpath tempfile.TemporaryFile
>
>    .. versionchanged:: 3.5
>
>       The :py:const:`os.O_TMPFILE` flag is now used if available.
>
>    .. versionchanged:: 3.8
>       Added *errors* parameter.
>
>
> .. function:: NamedTemporaryFile(mode='w+b', buffering=-1, encoding=None, newline=None, suffix=None, prefix=None, dir=None, delete=True, *, errors=None, delete_on_close=True)
>
>    This function operates exactly as :func:`TemporaryFil

Labelled source text:

> This function returns a file that is guaranteed to have a visible name in
>      the file system.

Surrounding canonical source context:

> ne, suffix=None, prefix=None, dir=None, delete=True, *, errors=None, delete_on_close=True)
>
>    This function operates exactly as :func:`TemporaryFile` does, except the
>    following differences:
>
>    * This function returns a file that is guaranteed to have a visible name in
>      the file system.
>    * To manage the named file, it extends the parameters of
>      :func:`TemporaryFile` with *delete* and *delete_on_close* parameters that
>      determine whether and how the named file should be auto

Review decision / disagreements / resolution: **pending**

## tempfile-TemporaryDirectory

held_out / tempfile+fnmatch / exact_api / draft

How is a temporary directory removed when used as a context manager?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `tempfile-TemporaryDirectory`:

On context-manager completion, TemporaryDirectory removes the temporary directory and all its contents.

Alternative `tempfile-TemporaryDirectory`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [8225, 8243)
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [8423, 8697)

Labelled source text:

> TemporaryDirectory

Surrounding canonical source context:

> nged:: 3.11
>       Fully implements the :class:`io.BufferedIOBase` and
>       :class:`io.TextIOBase` abstract base classes (depending on whether binary
>       or text *mode* was specified).
>
>
> .. class:: TemporaryDirectory(suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False, *, delete=True)
>
>    This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.
>    The resulting object

Labelled source text:

> The resulting object can be used as a :term:`context manager` (see
>    :ref:`tempfile-examples`).  On completion of the context or destruction
>    of the temporary directory object, the newly created temporary directory
>    and all its contents are removed from the filesystem.

Surrounding canonical source context:

> : TemporaryDirectory(suffix=None, prefix=None, dir=None, ignore_cleanup_errors=False, *, delete=True)
>
>    This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.
>    The resulting object can be used as a :term:`context manager` (see
>    :ref:`tempfile-examples`).  On completion of the context or destruction
>    of the temporary directory object, the newly created temporary directory
>    and all its contents are removed from the filesystem.
>
>    .. attribute:: TemporaryDirectory.name
>
>       The directory name can be retrieved from the :attr:`!name` attribute of the
>       returned object.  When the returned object is used as a :term:`cont

Review decision / disagreements / resolution: **pending**

## tempfile-mkstemp

held_out / tempfile+fnmatch / paraphrase / draft

Who is responsible for deleting files created by mkstemp?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old label covered secure creation but omitted who must delete the file.

Fact `tempfile-mkstemp`:

The caller of tempfile.mkstemp is responsible for deleting the temporary file when finished.

Alternative `tempfile-mkstemp`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [10262, 10269)
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [10792, 10918)

Labelled source text:

> mkstemp

Surrounding canonical source context:

> mporaryDirectory
>
>    .. versionadded:: 3.2
>
>    .. versionchanged:: 3.10
>       Added *ignore_cleanup_errors* parameter.
>
>    .. versionchanged:: 3.12
>       Added the *delete* parameter.
>
>
> .. function:: mkstemp(suffix=None, prefix=None, dir=None, text=False)
>
>    Creates a temporary file in the most secure manner possible.  There are
>    no race conditions in the file's creation, assuming that the platform
>

Labelled source text:

> Unlike :func:`TemporaryFile`, the user of :func:`mkstemp` is responsible
>    for deleting the temporary file when done with it.

Surrounding canonical source context:

> ating user ID.  If the
>    platform uses permission bits to indicate whether a file is executable,
>    the file is executable by no one.  The file descriptor is not inherited
>    by child processes.
>
>    Unlike :func:`TemporaryFile`, the user of :func:`mkstemp` is responsible
>    for deleting the temporary file when done with it.
>
>    If *suffix* is not ``None``, the file name will end with that suffix,
>    otherwise there will be no suffix.  :func:`mkstemp` does not put a dot
>    between the file name and the suffix; if you nee

Review decision / disagreements / resolution: **pending**

## glob-glob

held_out / glob+argparse / exact_api / draft

What does glob.glob return for a pathname pattern?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `glob-glob`:

glob.glob returns a possibly empty list of path names matching the supplied pathname pattern.

Alternative `glob-glob`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [1494, 1498)
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [1604, 1728)

Labelled source text:

> glob

Surrounding canonical source context:

> xpandvars`.)
>
> For a literal match, wrap the meta-characters in brackets.
> For example, ``'[?]'`` matches the character ``'?'``.
>
> The :mod:`glob` module defines the following functions:
>
>
> .. function:: glob(pathname, *, root_dir=None, dir_fd=None, recursive=False, \
>                    include_hidden=False)
>
>    Return a possibly empty list of path names that match *pathname*, which must be
>    a string co

Labelled source text:

> Return a possibly empty list of path names that match *pathname*, which must be
>    a string containing a path specification.

Surrounding canonical source context:

> aracter ``'?'``.
>
> The :mod:`glob` module defines the following functions:
>
>
> .. function:: glob(pathname, *, root_dir=None, dir_fd=None, recursive=False, \
>                    include_hidden=False)
>
>    Return a possibly empty list of path names that match *pathname*, which must be
>    a string containing a path specification. *pathname* can be either absolute
>    (like :file:`/usr/src/Python-1.5/Makefile`) or relative (like
>    :file:`../../Tools/\*/\*.gif`), and can contain shell-style wildcards. Broken
>    symlinks are inc

Review decision / disagreements / resolution: **pending**

## glob-iglob

held_out / glob+argparse / paraphrase / draft

Why use glob.iglob instead of glob.glob?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `glob-iglob`:

glob.iglob yields the same values as glob.glob through an iterator, without storing them all at once.

Alternative `glob-iglob`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [3671, 3676)
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [3780, 3907)

Labelled source text:

> iglob

Surrounding canonical source context:

> cursive globs using "``**``".
>
>    .. versionchanged:: 3.10
>       Added the *root_dir* and *dir_fd* parameters.
>
>    .. versionchanged:: 3.11
>       Added the *include_hidden* parameter.
>
>
> .. function:: iglob(pathname, *, root_dir=None, dir_fd=None, recursive=False, \
>                     include_hidden=False)
>
>    Return an :term:`iterator` which yields the same values as :func:`glob`
>    without actually s

Labelled source text:

>    Return an :term:`iterator` which yields the same values as :func:`glob`
>    without actually storing them all simultaneously.

Surrounding canonical source context:

> .
>
>    .. versionchanged:: 3.11
>       Added the *include_hidden* parameter.
>
>
> .. function:: iglob(pathname, *, root_dir=None, dir_fd=None, recursive=False, \
>                     include_hidden=False)
>
>    Return an :term:`iterator` which yields the same values as :func:`glob`
>    without actually storing them all simultaneously.
>
>    .. audit-event:: glob.glob pathname,recursive glob.iglob
>    .. audit-event:: glob.glob/2 pathname,recursive,root_dir,dir_fd glob.iglob
>
>    .. note::
>       This function may return duplicate path

Review decision / disagreements / resolution: **pending**

## glob-escape

held_out / glob+argparse / exact_api / draft

How can glob.escape treat wildcard characters literally?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `glob-escape`:

glob.escape escapes ?, * and [ so they match literally; special characters in drive/UNC sharepoints are not escaped.

Alternative `glob-escape`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4442, 4448)
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4460, 4793)

Labelled source text:

> escape

Surrounding canonical source context:

> cursive globs using "``**``".
>
>    .. versionchanged:: 3.10
>       Added the *root_dir* and *dir_fd* parameters.
>
>    .. versionchanged:: 3.11
>       Added the *include_hidden* parameter.
>
>
> .. function:: escape(pathname)
>
>    Escape all special characters (``'?'``, ``'*'`` and ``'['``).
>    This is useful if you want to match an arbitrary literal string that may
>    have special characters in it.  Special char

Labelled source text:

>    Escape all special characters (``'?'``, ``'*'`` and ``'['``).
>    This is useful if you want to match an arbitrary literal string that may
>    have special characters in it.  Special characters in drive/UNC
>    sharepoints are not escaped, e.g. on Windows
>    ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.

Surrounding canonical source context:

> g "``**``".
>
>    .. versionchanged:: 3.10
>       Added the *root_dir* and *dir_fd* parameters.
>
>    .. versionchanged:: 3.11
>       Added the *include_hidden* parameter.
>
>
> .. function:: escape(pathname)
>
>    Escape all special characters (``'?'``, ``'*'`` and ``'['``).
>    This is useful if you want to match an arbitrary literal string that may
>    have special characters in it.  Special characters in drive/UNC
>    sharepoints are not escaped, e.g. on Windows
>    ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.
>
>    .. versionadded:: 3.4
>
>
> .. function:: translate(pathname, *, recursive=False, include_hidden=False, seps=None)
>
>    Convert the given path specification to a regular expression for use with
>    :fu

Review decision / disagreements / resolution: **pending**

## glob-translate

held_out / glob+argparse / paraphrase / draft

How does glob.translate turn a path pattern into a regular expression?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `glob-translate`:

glob.translate converts a pathname specification containing shell-style wildcards into a regular expression for re.match.

Alternative `glob-translate`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4836, 4845)
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4910, 5065)

Labelled source text:

> translate

Surrounding canonical source context:

> Special characters in drive/UNC
>    sharepoints are not escaped, e.g. on Windows
>    ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.
>
>    .. versionadded:: 3.4
>
>
> .. function:: translate(pathname, *, recursive=False, include_hidden=False, seps=None)
>
>    Convert the given path specification to a regular expression for use with
>    :func:`re.match`. The path specification can contain sh

Labelled source text:

>    Convert the given path specification to a regular expression for use with
>    :func:`re.match`. The path specification can contain shell-style wildcards.

Surrounding canonical source context:

> ndows
>    ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.
>
>    .. versionadded:: 3.4
>
>
> .. function:: translate(pathname, *, recursive=False, include_hidden=False, seps=None)
>
>    Convert the given path specification to a regular expression for use with
>    :func:`re.match`. The path specification can contain shell-style wildcards.
>
>    For example:
>
>       >>> import glob, re
>       >>>
>       >>> regex = glob.translate('**/*.txt', recursive=True, include_hidden=True)
>       >>> regex
>       '(?s:(?:.+/)?[^/]*\\.txt)\\z'
>       >>> r

Review decision / disagreements / resolution: **pending**

## fnmatch-fnmatch

held_out / tempfile+fnmatch / exact_api / draft

How does fnmatch.fnmatch normalize case?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `fnmatch-fnmatch`:

fnmatch.fnmatch case-normalizes both the filename and pattern using os.path.normcase before matching.

Alternative `fnmatch-fnmatch`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [2372, 2379)
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [2392, 2718)

Labelled source text:

> fnmatch

Surrounding canonical source context:

> with a *maxsize* of 32768
> is used to cache the (typed) compiled regex patterns in the following
> functions: :func:`fnmatch`, :func:`fnmatchcase`, :func:`.filter`, :func:`.filterfalse`.
>
>
> .. function:: fnmatch(name, pat)
>
>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``.  Both parameters are case-normalized
>    using :func:`os.path.normcase`. :f

Labelled source text:

>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``.  Both parameters are case-normalized
>    using :func:`os.path.normcase`. :func:`fnmatchcase` can be used to perform a
>    case-sensitive comparison, regardless of whether that's standard for the
>    operating system.

Surrounding canonical source context:

> 32768
> is used to cache the (typed) compiled regex patterns in the following
> functions: :func:`fnmatch`, :func:`fnmatchcase`, :func:`.filter`, :func:`.filterfalse`.
>
>
> .. function:: fnmatch(name, pat)
>
>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``.  Both parameters are case-normalized
>    using :func:`os.path.normcase`. :func:`fnmatchcase` can be used to perform a
>    case-sensitive comparison, regardless of whether that's standard for the
>    operating system.
>
>    This example will print all file names in the current directory with the
>    extension ``.txt``::
>
>       import fnmatch
>       import os
>
>       for file in os.listdir('.'):
>           if fnmatch.fnm

Review decision / disagreements / resolution: **pending**

## fnmatch-fnmatchcase

held_out / tempfile+fnmatch / paraphrase / draft

How can shell wildcard matching remain case-sensitive?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed the handout alternative: its extracted prose does not identify this named API. The handout-only behavioural question remains supported.

Fact `fnmatch-fnmatchcase`:

Use fnmatch.fnmatchcase for case-sensitive shell wildcard matching without os.path.normcase normalization.

Alternative `fnmatch-fnmatchcase`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [2981, 2992)
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3005, 3198)

Labelled source text:

> fnmatchcase

Surrounding canonical source context:

> ctory with the
>    extension ``.txt``::
>
>       import fnmatch
>       import os
>
>       for file in os.listdir('.'):
>           if fnmatch.fnmatch(file, '*.txt'):
>               print(file)
>
>
> .. function:: fnmatchcase(name, pat)
>
>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.norm

Labelled source text:

>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.normcase`.

Surrounding canonical source context:

> ion ``.txt``::
>
>       import fnmatch
>       import os
>
>       for file in os.listdir('.'):
>           if fnmatch.fnmatch(file, '*.txt'):
>               print(file)
>
>
> .. function:: fnmatchcase(name, pat)
>
>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.normcase`.
>
>
> .. function:: filter(names, pat)
>
>    Construct a list from those elements of the :term:`iterable` of filename
>    strings *names* that match the pattern string *pat*.
>    It is the same as ``[n for n

Review decision / disagreements / resolution: **pending**

## fnmatch-filter

held_out / tempfile+fnmatch / exact_api / draft

What does fnmatch.filter select from a list of names?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed the handout alternative: its extracted prose does not identify this named API. The handout-only behavioural question remains supported.

Fact `fnmatch-filter`:

fnmatch.filter returns the list of input filename strings matching the pattern, equivalent to [n for n in names if fnmatch(n, pat)].

Alternative `fnmatch-filter`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3215, 3221)
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3235, 3467)

Labelled source text:

> filter

Surrounding canonical source context:

> ether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.normcase`.
>
>
> .. function:: filter(names, pat)
>
>    Construct a list from those elements of the :term:`iterable` of filename
>    strings *names* that match the pattern string *pat*.
>    It is the same as ``[n for n in names if fnmatch(n,

Labelled source text:

>    Construct a list from those elements of the :term:`iterable` of filename
>    strings *names* that match the pattern string *pat*.
>    It is the same as ``[n for n in names if fnmatch(n, pat)]``,
>    but implemented more efficiently.

Surrounding canonical source context:

> tring *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.normcase`.
>
>
> .. function:: filter(names, pat)
>
>    Construct a list from those elements of the :term:`iterable` of filename
>    strings *names* that match the pattern string *pat*.
>    It is the same as ``[n for n in names if fnmatch(n, pat)]``,
>    but implemented more efficiently.
>
>
> .. function:: filterfalse(names, pat)
>
>    Construct a list from those elements of the :term:`iterable` of filename
>    strings *names* that do not match the pattern string *pat*.
>    It is the same a

Review decision / disagreements / resolution: **pending**

## fnmatch-translate

held_out / tempfile+fnmatch / paraphrase / draft

How does fnmatch.translate produce a regular expression?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `fnmatch-translate`:

fnmatch.translate converts a string shell-style pattern into a regular expression for re.match.

Alternative `fnmatch-translate`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3796, 3805)
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3812, 3967)

Labelled source text:

> translate

Surrounding canonical source context:

> *names* that do not match the pattern string *pat*.
>    It is the same as ``[n for n in names if not fnmatch(n, pat)]``,
>    but implemented more efficiently.
>
>    .. versionadded:: 3.14
>
>
> .. function:: translate(pat)
>
>    Return the shell-style pattern *pat* converted to a regular expression for
>    using with :func:`re.match`. The pattern is expected to be a :class:`str`.
>
>    Example:
>
>       >>> import fnmatc

Labelled source text:

>    Return the shell-style pattern *pat* converted to a regular expression for
>    using with :func:`re.match`. The pattern is expected to be a :class:`str`.

Surrounding canonical source context:

> not match the pattern string *pat*.
>    It is the same as ``[n for n in names if not fnmatch(n, pat)]``,
>    but implemented more efficiently.
>
>    .. versionadded:: 3.14
>
>
> .. function:: translate(pat)
>
>    Return the shell-style pattern *pat* converted to a regular expression for
>    using with :func:`re.match`. The pattern is expected to be a :class:`str`.
>
>    Example:
>
>       >>> import fnmatch, re
>       >>>
>       >>> regex = fnmatch.translate('*.txt')
>       >>> regex
>       '(?s:.*\\.txt)\\z'
>       >>> reobj = re.compile(regex)
>       >>> reobj.match('f

Review decision / disagreements / resolution: **pending**

## re-search

development / re+bisect / exact_api / draft

Where in a string does re.search look for a match?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Scoped support to the question’s matching-position condition, not unrelated failure and zero-length notes.

Fact `re-search`:

re.search scans for the first matching location anywhere in the string.

Alternative `re-search`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [38344, 38350)
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [38378, 38540)

Labelled source text:

> search

Surrounding canonical source context:

> mpile` and the module-level matching functions are cached, so
>       programs that use only a few regular expressions at a time needn't worry
>       about compiling regular expressions.
>
>
> .. function:: search(pattern, string, flags=0)
>
>    Scan through *string* looking for the first location where the regular expression
>    *pattern* produces a match, and return a corresponding :class:`~re.Match`. Return
>

Labelled source text:

>    Scan through *string* looking for the first location where the regular expression
>    *pattern* produces a match, and return a corresponding :class:`~re.Match`.

Surrounding canonical source context:

> ng functions are cached, so
>       programs that use only a few regular expressions at a time needn't worry
>       about compiling regular expressions.
>
>
> .. function:: search(pattern, string, flags=0)
>
>    Scan through *string* looking for the first location where the regular expression
>    *pattern* produces a match, and return a corresponding :class:`~re.Match`. Return
>    ``None`` if no position in the string matches the pattern; note that this is
>    different from finding a zero-length match at some point in the string.
>
>    The expression's behaviour can be

Review decision / disagreements / resolution: **pending**

## re-match

development / re+bisect / paraphrase / draft

Why can re.match miss a pattern occurring later in a string?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Scoped support to the question’s matching-position condition, not unrelated failure and zero-length notes.

Fact `re-match`:

re.match only matches at the beginning of the string, so a pattern appearing only later is missed.

Alternative `re-match`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [38896, 38901)
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [38929, 39073)

Labelled source text:

> match

Surrounding canonical source context:

> tring.
>
>    The expression's behaviour can be modified by specifying a *flags* value.
>    Values can be any of the `flags`_ variables, combined using bitwise OR
>    (the ``|`` operator).
>
>
> .. function:: match(pattern, string, flags=0)
>
>    If zero or more characters at the beginning of *string* match the regular
>    expression *pattern*, return a corresponding :class:`~re.Match`.  Return
>    ``None`` if the

Labelled source text:

>    If zero or more characters at the beginning of *string* match the regular
>    expression *pattern*, return a corresponding :class:`~re.Match`.

Surrounding canonical source context:

> iour can be modified by specifying a *flags* value.
>    Values can be any of the `flags`_ variables, combined using bitwise OR
>    (the ``|`` operator).
>
>
> .. function:: match(pattern, string, flags=0)
>
>    If zero or more characters at the beginning of *string* match the regular
>    expression *pattern*, return a corresponding :class:`~re.Match`.  Return
>    ``None`` if the string does not match the pattern; note that this is
>    different from a zero-length match.
>
>    Note that even in :const:`MULTILINE` mode, :func:`re.match` will only match

Review decision / disagreements / resolution: **pending**

## re-fullmatch

development / re+bisect / exact_api / draft

When does re.fullmatch succeed?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Scoped support to the question’s matching-position condition, not unrelated failure and zero-length notes.

Fact `re-fullmatch`:

re.fullmatch succeeds when the entire string matches the pattern.

Alternative `re-fullmatch`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [39660, 39669)
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [39697, 39809)

Labelled source text:

> fullmatch

Surrounding canonical source context:

> tch`).
>
>    The expression's behaviour can be modified by specifying a *flags* value.
>    Values can be any of the `flags`_ variables, combined using bitwise OR
>    (the ``|`` operator).
>
>
> .. function:: fullmatch(pattern, string, flags=0)
>
>    If the whole *string* matches the regular expression *pattern*, return a
>    corresponding :class:`~re.Match`.  Return ``None`` if the string does not match
>    the patter

Labelled source text:

>    If the whole *string* matches the regular expression *pattern*, return a
>    corresponding :class:`~re.Match`.

Surrounding canonical source context:

>  can be modified by specifying a *flags* value.
>    Values can be any of the `flags`_ variables, combined using bitwise OR
>    (the ``|`` operator).
>
>
> .. function:: fullmatch(pattern, string, flags=0)
>
>    If the whole *string* matches the regular expression *pattern*, return a
>    corresponding :class:`~re.Match`.  Return ``None`` if the string does not match
>    the pattern; note that this is different from a zero-length match.
>
>    The expression's behaviour can be modified by specifying a *flags* value.
>    Va

Review decision / disagreements / resolution: **pending**

## re-findall

development / re+bisect / paraphrase / draft

How are multiple matches returned by re.findall?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `re-findall`:

re.findall returns non-overlapping matches as a list of strings or tuples, in left-to-right order, including empty matches.

Alternative `re-findall`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [42349, 42356)
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [42384, 42613)

Labelled source text:

> findall

Surrounding canonical source context:

>       Passing *maxsplit* and *flags* as positional arguments is deprecated.
>       In future Python versions they will be
>       :ref:`keyword-only parameters <keyword-only_parameter>`.
>
>
> .. function:: findall(pattern, string, flags=0)
>
>    Return all non-overlapping matches of *pattern* in *string*, as a list of
>    strings or tuples.  The *string* is scanned left-to-right, and matches
>    are returned in th

Labelled source text:

>    Return all non-overlapping matches of *pattern* in *string*, as a list of
>    strings or tuples.  The *string* is scanned left-to-right, and matches
>    are returned in the order found.  Empty matches are included in the result.

Surrounding canonical source context:

> * as positional arguments is deprecated.
>       In future Python versions they will be
>       :ref:`keyword-only parameters <keyword-only_parameter>`.
>
>
> .. function:: findall(pattern, string, flags=0)
>
>    Return all non-overlapping matches of *pattern* in *string*, as a list of
>    strings or tuples.  The *string* is scanned left-to-right, and matches
>    are returned in the order found.  Empty matches are included in the result.
>
>    The result depends on the number of capturing groups in the pattern.
>    If there are no groups, return a list of strings matching the whole
>    pattern.  If there is exactly one group, return a li

Review decision / disagreements / resolution: **pending**

## collections-Counter

held_out / collections+heapq / exact_api / draft

What does collections.Counter count?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `collections-Counter`:

Counter counts hashable objects, storing objects as dictionary keys and their counts as values; counts may be zero or negative.

Alternative `collections-Counter`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [10114, 10121)
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [10146, 10524)

Labelled source text:

> Counter

Surrounding canonical source context:

> )
>     >>> Counter(words).most_common(10)
>     [('the', 1143), ('and', 966), ('to', 762), ('of', 669), ('i', 631),
>      ('you', 554),  ('a', 546), ('my', 514), ('hamlet', 471), ('in', 451)]
>
> .. class:: Counter([iterable-or-mapping])
>
>     A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
>     It is a collection where elements are stored as dictionary keys
>     and their cou

Labelled source text:

>     A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
>     It is a collection where elements are stored as dictionary keys
>     and their counts are stored as dictionary values.  Counts are allowed to be
>     any integer value including zero or negative counts.  The :class:`Counter`
>     class is similar to bags or multisets in other languages.

Surrounding canonical source context:

> mmon(10)
>     [('the', 1143), ('and', 966), ('to', 762), ('of', 669), ('i', 631),
>      ('you', 554),  ('a', 546), ('my', 514), ('hamlet', 471), ('in', 451)]
>
> .. class:: Counter([iterable-or-mapping])
>
>     A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
>     It is a collection where elements are stored as dictionary keys
>     and their counts are stored as dictionary values.  Counts are allowed to be
>     any integer value including zero or negative counts.  The :class:`Counter`
>     class is similar to bags or multisets in other languages.
>
>     Elements are counted from an *iterable* or initialized from another
>     *mapping* (or counter):
>
>         >>> c = Counter()                           # a new, empty counter
>         >>> c = Counte

Review decision / disagreements / resolution: **pending**

## collections-deque

held_out / collections+heapq / paraphrase / draft

What is a deque optimized for?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Replaced constructor initialization with the missing optimization and complexity statement.

Fact `collections-deque`:

A deque supports thread-safe, memory-efficient appends and pops at either end with approximately O(1) performance.

Alternative `collections-deque`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [18937, 18942)
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [19139, 19433)

Labelled source text:

> deque

Surrounding canonical source context:

> ee :func:`itertools.combinations_with_replacement`::
>
>         map(Counter, combinations_with_replacement('ABC', 2)) # --> AA AB AC BB BC CC
>
>
> :class:`deque` objects
> ----------------------
>
> .. class:: deque([iterable, [maxlen]])
>
>     Returns a new deque object initialized left-to-right (using :meth:`append`) with
>     data from *iterable*.  If *iterable* is not specified, the new deque is empty.
>
>     Deq

Labelled source text:

> Deques are a generalization of stacks and queues (the name is pronounced "deck"
>     and is short for "double-ended queue").  Deques support thread-safe, memory
>     efficient appends and pops from either side of the deque with approximately the
>     same *O*\ (1) performance in either direction.

Surrounding canonical source context:

> que([iterable, [maxlen]])
>
>     Returns a new deque object initialized left-to-right (using :meth:`append`) with
>     data from *iterable*.  If *iterable* is not specified, the new deque is empty.
>
>     Deques are a generalization of stacks and queues (the name is pronounced "deck"
>     and is short for "double-ended queue").  Deques support thread-safe, memory
>     efficient appends and pops from either side of the deque with approximately the
>     same *O*\ (1) performance in either direction.
>
>     Though :class:`list` objects support similar operations, they are optimized for
>     fast fixed-length operations and incur *O*\ (*n*) memory movement costs for
>     ``pop(0)`` and ``insert(0, v)`

Review decision / disagreements / resolution: **pending**

## collections-defaultdict

held_out / collections+heapq / exact_api / draft

What relationship does defaultdict have to the built-in dict class?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `collections-defaultdict`:

defaultdict subclasses dict, overriding one method and adding one writable instance variable while retaining the remaining dict behaviour.

Alternative `collections-defaultdict`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [27705, 27716)
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [27750, 28041)

Labelled source text:

> defaultdict

Surrounding canonical source context:

> sy to implement Forth style
> stack manipulations such as ``dup``, ``drop``, ``swap``, ``over``, ``pick``,
> ``rot``, and ``roll``.
>
>
> :class:`defaultdict` objects
> ----------------------------
>
> .. class:: defaultdict(default_factory=None, /, [...])
>
>     Return a new dictionary-like object.  :class:`defaultdict` is a subclass of the
>     built-in :class:`dict` class.  It overrides one method and adds one writable
>

Labelled source text:

>     Return a new dictionary-like object.  :class:`defaultdict` is a subclass of the
>     built-in :class:`dict` class.  It overrides one method and adds one writable
>     instance variable.  The remaining functionality is the same as for the
>     :class:`dict` class and is not documented here.

Surrounding canonical source context:

> ns such as ``dup``, ``drop``, ``swap``, ``over``, ``pick``,
> ``rot``, and ``roll``.
>
>
> :class:`defaultdict` objects
> ----------------------------
>
> .. class:: defaultdict(default_factory=None, /, [...])
>
>     Return a new dictionary-like object.  :class:`defaultdict` is a subclass of the
>     built-in :class:`dict` class.  It overrides one method and adds one writable
>     instance variable.  The remaining functionality is the same as for the
>     :class:`dict` class and is not documented here.
>
>     The first argument provides the initial value for the :attr:`default_factory`
>     attribute; it defaults to ``None``. All remaining arguments are treated the same
>     as if they were passed to t

Review decision / disagreements / resolution: **pending**

## collections-namedtuple

held_out / collections+heapq / paraphrase / draft

What does namedtuple create?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `collections-namedtuple`:

namedtuple creates a tuple subclass with named fields accessible as attributes as well as by indexing and iteration.

Alternative `collections-namedtuple`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [32898, 32908)
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [32978, 33390)

Labelled source text:

> namedtuple

Surrounding canonical source context:

> ple and allow for more readable,
> self-documenting code.  They can be used wherever regular tuples are used, and
> they add the ability to access fields by name instead of position index.
>
> .. function:: namedtuple(typename, field_names, *, rename=False, defaults=None, module=None)
>
>     Returns a new tuple subclass named *typename*.  The new subclass is used to
>     create tuple-like objects that have fields acc

Labelled source text:

>     Returns a new tuple subclass named *typename*.  The new subclass is used to
>     create tuple-like objects that have fields accessible by attribute lookup as
>     well as being indexable and iterable.  Instances of the subclass also have a
>     helpful docstring (with *typename* and *field_names*) and a helpful
>     :meth:`~object.__repr__` method which lists the tuple contents in a ``name=value``
>     format.

Surrounding canonical source context:

> er regular tuples are used, and
> they add the ability to access fields by name instead of position index.
>
> .. function:: namedtuple(typename, field_names, *, rename=False, defaults=None, module=None)
>
>     Returns a new tuple subclass named *typename*.  The new subclass is used to
>     create tuple-like objects that have fields accessible by attribute lookup as
>     well as being indexable and iterable.  Instances of the subclass also have a
>     helpful docstring (with *typename* and *field_names*) and a helpful
>     :meth:`~object.__repr__` method which lists the tuple contents in a ``name=value``
>     format.
>
>     The *field_names* are a sequence of strings such as ``['x', 'y']``.
>     Alternatively, *field_names* can be a single string with each fieldname
>     separated by whitespace and/or commas, for exa

Review decision / disagreements / resolution: **pending**

## heapq-heappush

held_out / collections+heapq / exact_api / draft

How does heapq.heappush maintain the heap?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `heapq-heappush`:

heappush adds an item while preserving the min-heap invariant.

Alternative `heapq-heappush`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2529, 2537)
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2551, 2628)

Labelled source text:

> heappush

Surrounding canonical source context:

> r transform an existing list
> into a min-heap or max-heap using the :func:`heapify` or :func:`heapify_max`
> functions, respectively.
>
> The following functions are provided for min-heaps:
>
>
> .. function:: heappush(heap, item)
>
>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.
>
>
> .. function:: heappop(heap)
>
>    Pop and return the smallest item from the *heap*, maintaining the min-heap

Labelled source text:

>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.

Surrounding canonical source context:

> g list
> into a min-heap or max-heap using the :func:`heapify` or :func:`heapify_max`
> functions, respectively.
>
> The following functions are provided for min-heaps:
>
>
> .. function:: heappush(heap, item)
>
>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.
>
>
> .. function:: heappop(heap)
>
>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smalle

Review decision / disagreements / resolution: **pending**

## heapq-heappop

held_out / collections+heapq / paraphrase / draft

Which element is returned by heapq.heappop?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `heapq-heappop`:

heappop removes and returns the smallest heap item while preserving the min-heap invariant.

Alternative `heapq-heappop`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2645, 2652)
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2660, 2872)

Labelled source text:

> heappop

Surrounding canonical source context:

>  respectively.
>
> The following functions are provided for min-heaps:
>
>
> .. function:: heappush(heap, item)
>
>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.
>
>
> .. function:: heappop(heap)
>
>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping

Labelled source text:

>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping it, use ``heap[0]``.

Surrounding canonical source context:

>
> The following functions are provided for min-heaps:
>
>
> .. function:: heappush(heap, item)
>
>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.
>
>
> .. function:: heappop(heap)
>
>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping it, use ``heap[0]``.
>
>
> .. function:: heappushpop(heap, item)
>
>    Push *item* on the heap, then pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    foll

Review decision / disagreements / resolution: **pending**

## heapq-heapify

held_out / collections+heapq / exact_api / draft

How does heapq.heapify transform a list?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `heapq-heapify`:

heapify transforms the list in place into a min-heap in linear time.

Alternative `heapq-heapify`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [3132, 3139)
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [3144, 3208)

Labelled source text:

> heapify

Surrounding canonical source context:

> the heap, then pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    followed by a separate call to :func:`heappop`.
>
>
> .. function:: heapify(x)
>
>    Transform list *x* into a min-heap, in-place, in linear time.
>
>
> .. function:: heapreplace(heap, item)
>
>    Pop and return the smallest item from the *heap*, and also push the new *item*.
>    The

Labelled source text:

>    Transform list *x* into a min-heap, in-place, in linear time.

Surrounding canonical source context:

> en pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    followed by a separate call to :func:`heappop`.
>
>
> .. function:: heapify(x)
>
>    Transform list *x* into a min-heap, in-place, in linear time.
>
>
> .. function:: heapreplace(heap, item)
>
>    Pop and return the smallest item from the *heap*, and also push the new *item*.
>    The heap size doesn't change. If the heap is empty, :exc:`IndexError` is

Review decision / disagreements / resolution: **pending**

## heapq-heappushpop

held_out / collections+heapq / paraphrase / draft

What does heapq.heappushpop do in one operation?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `heapq-heappushpop`:

heappushpop pushes an item and then removes and returns the smallest heap item in one combined operation.

Alternative `heapq-heappushpop`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2889, 2900)
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2914, 3115)

Labelled source text:

> heappushpop

Surrounding canonical source context:

> t item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping it, use ``heap[0]``.
>
>
> .. function:: heappushpop(heap, item)
>
>    Push *item* on the heap, then pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    followed by a separate call to :

Labelled source text:

>    Push *item* on the heap, then pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    followed by a separate call to :func:`heappop`.

Surrounding canonical source context:

> aintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping it, use ``heap[0]``.
>
>
> .. function:: heappushpop(heap, item)
>
>    Push *item* on the heap, then pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    followed by a separate call to :func:`heappop`.
>
>
> .. function:: heapify(x)
>
>    Transform list *x* into a min-heap, in-place, in linear time.
>
>
> .. function:: heapreplace(heap, item)
>
>    Pop and return the smallest item from the *heap*, and also pus

Review decision / disagreements / resolution: **pending**

## bisect-bisect_left

development / re+bisect / exact_api / draft

Where does bisect_left insert relative to existing equal values?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bisect-bisect_left`:

bisect_left returns the sorted insertion position before any existing equal values.

Alternative `bisect-bisect_left`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [1720, 1731)
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [1769, 2219)

Labelled source text:

> bisect_left

Surrounding canonical source context:

> ing
>    :py:func:`~bisect.insort_left` on the same list from multiple threads
>    may result in the list becoming unsorted.
>
> .. _bisect functions:
>
> The following functions are provided:
>
>
> .. function:: bisect_left(a, x, lo=0, hi=len(a), *, key=None)
>
>    Locate the insertion point for *x* in *a* to maintain sorted order.
>    The parameters *lo* and *hi* may be used to specify a subset of the list
>    which should

Labelled source text:

>    Locate the insertion point for *x* in *a* to maintain sorted order.
>    The parameters *lo* and *hi* may be used to specify a subset of the list
>    which should be considered; by default the entire list is used.  If *x* is
>    already present in *a*, the insertion point will be before (to the left of)
>    any existing entries.  The return value is suitable for use as the first
>    parameter to ``list.insert()`` assuming that *a* is already sorted.

Surrounding canonical source context:

>  list from multiple threads
>    may result in the list becoming unsorted.
>
> .. _bisect functions:
>
> The following functions are provided:
>
>
> .. function:: bisect_left(a, x, lo=0, hi=len(a), *, key=None)
>
>    Locate the insertion point for *x* in *a* to maintain sorted order.
>    The parameters *lo* and *hi* may be used to specify a subset of the list
>    which should be considered; by default the entire list is used.  If *x* is
>    already present in *a*, the insertion point will be before (to the left of)
>    any existing entries.  The return value is suitable for use as the first
>    parameter to ``list.insert()`` assuming that *a* is already sorted.
>
>    The returned insertion point *ip* partitions the array *a* into two
>    slices such that ``all(elem < x for elem in a[lo : ip])`` is true for the
>    left slice and ``all(elem >= x for elem in a[ip

Review decision / disagreements / resolution: **pending**

## bisect-bisect_right

development / re+bisect / paraphrase / draft

Where does bisect_right insert relative to existing equal values?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bisect-bisect_right`:

bisect_right returns the sorted insertion position after any existing equal values.

Alternative `bisect-bisect_right`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [2861, 2873)
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [2968, 3119)

Labelled source text:

> bisect_right

Surrounding canonical source context:

>  applied to the *x* value.
>
>    If *key* is ``None``, the elements are compared directly and
>    no key function is called.
>
>    .. versionchanged:: 3.10
>       Added the *key* parameter.
>
>
> .. function:: bisect_right(a, x, lo=0, hi=len(a), *, key=None)
>               bisect(a, x, lo=0, hi=len(a), *, key=None)
>
>    Similar to :py:func:`~bisect.bisect_left`, but returns an insertion point which comes
>    after (to the

Labelled source text:

>    Similar to :py:func:`~bisect.bisect_left`, but returns an insertion point which comes
>    after (to the right of) any existing entries of *x* in *a*.

Surrounding canonical source context:

> ion is called.
>
>    .. versionchanged:: 3.10
>       Added the *key* parameter.
>
>
> .. function:: bisect_right(a, x, lo=0, hi=len(a), *, key=None)
>               bisect(a, x, lo=0, hi=len(a), *, key=None)
>
>    Similar to :py:func:`~bisect.bisect_left`, but returns an insertion point which comes
>    after (to the right of) any existing entries of *x* in *a*.
>
>    The returned insertion point *ip* partitions the array *a* into two slices
>    such that ``all(elem <= x for elem in a[lo : ip])`` is true for the left slice and
>    ``all(elem > x for elem in a[ip

Review decision / disagreements / resolution: **pending**

## bisect-insort_left

development / re+bisect / exact_api / draft

What sequence of operations does insort_left perform?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bisect-insort_left`:

insort_left first finds the position using bisect_left and then inserts x there using the list insert method.

Alternative `bisect-insort_left`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [3436, 3447)
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [3527, 3741)

Labelled source text:

> insort_left

Surrounding canonical source context:

>  in a[lo : ip])`` is true for the left slice and
>    ``all(elem > x for elem in a[ip : hi])`` is true for the right slice.
>
>    .. versionchanged:: 3.10
>       Added the *key* parameter.
>
>
> .. function:: insort_left(a, x, lo=0, hi=len(a), *, key=None)
>
>    Insert *x* in *a* in sorted order.
>
>    This function first runs :py:func:`~bisect.bisect_left` to locate an insertion point.
>    Next, it runs the :meth:`~seque

Labelled source text:

> This function first runs :py:func:`~bisect.bisect_left` to locate an insertion point.
>    Next, it runs the :meth:`~sequence.insert` method on *a* to insert *x* at the
>    appropriate position to maintain sort order.

Surrounding canonical source context:

> ` is true for the right slice.
>
>    .. versionchanged:: 3.10
>       Added the *key* parameter.
>
>
> .. function:: insort_left(a, x, lo=0, hi=len(a), *, key=None)
>
>    Insert *x* in *a* in sorted order.
>
>    This function first runs :py:func:`~bisect.bisect_left` to locate an insertion point.
>    Next, it runs the :meth:`~sequence.insert` method on *a* to insert *x* at the
>    appropriate position to maintain sort order.
>
>    To support inserting records in a table, the *key* function (if any) is
>    applied to *x* for the search step but not for the insertion step.
>
>    Keep in mind that the *O*\ (log *n*) search is do

Review decision / disagreements / resolution: **pending**

## bisect-insort_right

development / re+bisect / paraphrase / draft

How does insort_right choose a position for equal elements?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bisect-insort_right`:

insort_right inserts x after existing equal values.

Alternative `bisect-insort_right`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [4069, 4081)
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [4176, 4284)

Labelled source text:

> insort_right

Surrounding canonical source context:

> he insertion step.
>
>    Keep in mind that the *O*\ (log *n*) search is dominated by the slow *O*\ (*n*)
>    insertion step.
>
>    .. versionchanged:: 3.10
>       Added the *key* parameter.
>
>
> .. function:: insort_right(a, x, lo=0, hi=len(a), *, key=None)
>               insort(a, x, lo=0, hi=len(a), *, key=None)
>
>    Similar to :py:func:`~bisect.insort_left`, but inserting *x* in *a* after any existing
>    entries of *

Labelled source text:

>    Similar to :py:func:`~bisect.insort_left`, but inserting *x* in *a* after any existing
>    entries of *x*.

Surrounding canonical source context:

> nsertion step.
>
>    .. versionchanged:: 3.10
>       Added the *key* parameter.
>
>
> .. function:: insort_right(a, x, lo=0, hi=len(a), *, key=None)
>               insort(a, x, lo=0, hi=len(a), *, key=None)
>
>    Similar to :py:func:`~bisect.insort_left`, but inserting *x* in *a* after any existing
>    entries of *x*.
>
>    This function first runs :py:func:`~bisect.bisect_right` to locate an insertion point.
>    Next, it runs the :meth:`~sequence.insert` method on *a* to insert *x* at the
>    appropriate position to

Review decision / disagreements / resolution: **pending**

## statistics-mean

development / statistics+itertools / exact_api / draft

What average does statistics.mean calculate?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the independently sufficient arithmetic-mean definition under the same named API.

Fact `statistics-mean`:

statistics.mean returns the arithmetic mean of the data.

Alternative `statistics-mean`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5027, 5031)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5039, 5122)

Labelled source text:

> mean

Surrounding canonical source context:

> Function details
> ----------------
>
> Note: The functions do not require the data given to them to be sorted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly call

Labelled source text:

>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.

Surrounding canonical source context:

> ails
> ----------------
>
> Note: The functions do not require the data given to them to be sorted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly called "the average", although it is only one of many
>    different mathematical averages.  It i

Alternative `statistics-mean-definition`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5027, 5031)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5127, 5210)

Labelled source text:

> mean

Surrounding canonical source context:

> Function details
> ----------------
>
> Note: The functions do not require the data given to them to be sorted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly call

Labelled source text:

> The arithmetic mean is the sum of the data divided by the number of data
>    points.

Surrounding canonical source context:

> orted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly called "the average", although it is only one of many
>    different mathematical averages.  It is a measure of the central location of
>    the data.
>
>    If *data* is empty, :exc:`Statis

Review decision / disagreements / resolution: **pending**

## statistics-median

development / statistics+itertools / paraphrase / draft

How is statistics.median determined for an even number of values?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the explicit even-number condition instead of relying on the generic median description.

Fact `statistics-median`:

For an even number of numeric values, statistics.median returns the average of the two middle values.

Alternative `statistics-median`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [12584, 12590)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [13040, 13157)

Labelled source text:

> median

Surrounding canonical source context:

>  >>> new_selections = [rand() for i in range(10)]
>       >>> [round(x, 1) for x in new_selections]
>       [0.7, 6.2, 1.2, 6.9, 7.0, 1.8, 2.5, -0.5, -1.8, 5.6]
>
>    .. versionadded:: 3.13
>
>
> .. function:: median(data)
>
>    Return the median (middle value) of numeric data, using the common "mean of
>    middle two" method.  If *data* is empty, :exc:`StatisticsError` is raised.
>    *data* can be a sequence or iter

Labelled source text:

> When the number of data points is even, the median is interpolated by taking
>    the average of the two middle values:

Surrounding canonical source context:

> l location and is less affected by
>    the presence of outliers.  When the number of data points is odd, the
>    middle data point is returned:
>
>    .. doctest::
>
>       >>> median([1, 3, 5])
>       3
>
>    When the number of data points is even, the median is interpolated by taking
>    the average of the two middle values:
>
>    .. doctest::
>
>       >>> median([1, 3, 5, 7])
>       4.0
>
>    This is suited for when your data is discrete, and you don't mind that the
>    median may not be an actual data point.
>
>    If the data is

Review decision / disagreements / resolution: **pending**

## statistics-mode

development / statistics+itertools / exact_api / draft

What does statistics.mode return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the tie-breaking qualifier to avoid treating all tied modes as an unspecified result.

Fact `statistics-mode`:

statistics.mode returns the most common data point; ties return the first encountered value.

Alternative `statistics-mode`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [16596, 16600)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [16608, 16787)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [16792, 16896)

Labelled source text:

> mode

Surrounding canonical source context:

> al for getting a
>    correct result.  The function does not check this precondition.
>
>    Inputs may be any numeric type that can be coerced to a float during
>    the interpolation step.
>
>
> .. function:: mode(data)
>
>    Return the single most common data point from discrete or nominal *data*.
>    The mode (when it exists) is the most typical value and serves as a
>    measure of central location.
>
>    If there

Labelled source text:

>    Return the single most common data point from discrete or nominal *data*.
>    The mode (when it exists) is the most typical value and serves as a
>    measure of central location.

Surrounding canonical source context:

> ng a
>    correct result.  The function does not check this precondition.
>
>    Inputs may be any numeric type that can be coerced to a float during
>    the interpolation step.
>
>
> .. function:: mode(data)
>
>    Return the single most common data point from discrete or nominal *data*.
>    The mode (when it exists) is the most typical value and serves as a
>    measure of central location.
>
>    If there are multiple modes with the same frequency, returns the first one
>    encountered in the *data*.  If the smallest or largest of those is
>    desired instead, use ``min(multimode(data))`` o

Labelled source text:

> If there are multiple modes with the same frequency, returns the first one
>    encountered in the *data*.

Surrounding canonical source context:

> n:: mode(data)
>
>    Return the single most common data point from discrete or nominal *data*.
>    The mode (when it exists) is the most typical value and serves as a
>    measure of central location.
>
>    If there are multiple modes with the same frequency, returns the first one
>    encountered in the *data*.  If the smallest or largest of those is
>    desired instead, use ``min(multimode(data))`` or ``max(multimode(data))``.
>    If the input *data* is empty, :exc:`StatisticsError` is raised.
>
>    ``mode`` a

Review decision / disagreements / resolution: **pending**

## statistics-stdev

development / statistics+itertools / paraphrase / draft

Which standard deviation is computed by statistics.stdev?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `statistics-stdev`:

statistics.stdev returns the sample standard deviation, the square root of the sample variance.

Alternative `statistics-stdev`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [20913, 20918)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [20937, 21076)

Labelled source text:

> stdev

Surrounding canonical source context:

> opulation mean as the second argument.  Provided the data points are a
>       random sample of the population, the result will be an unbiased estimate
>       of the population variance.
>
>
> .. function:: stdev(data, xbar=None)
>
>    Return the sample standard deviation (the square root of the sample
>    variance).  See :func:`variance` for arguments and other details.
>
>    .. doctest::
>
>       >>> stdev([1.5, 2

Labelled source text:

>    Return the sample standard deviation (the square root of the sample
>    variance).  See :func:`variance` for arguments and other details.

Surrounding canonical source context:

> cond argument.  Provided the data points are a
>       random sample of the population, the result will be an unbiased estimate
>       of the population variance.
>
>
> .. function:: stdev(data, xbar=None)
>
>    Return the sample standard deviation (the square root of the sample
>    variance).  See :func:`variance` for arguments and other details.
>
>    .. doctest::
>
>       >>> stdev([1.5, 2.5, 2.5, 2.75, 3.25, 4.75])
>       1.0810874155219827
>
>
> .. function:: variance(data, xbar=None)
>
>    Return the sample variance of *data*, an iterable of at lea

Review decision / disagreements / resolution: **pending**

## decimal-Decimal

held_out / decimal+fractions / exact_api / draft

Which kinds of values can construct a Decimal?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The original span said only that construction is based on value; it did not list supported input types.

Fact `decimal-Decimal`:

Decimal accepts an integer, string, tuple, float or another Decimal value.

Alternative `decimal-Decimal`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [12768, 12775)
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [12869, 13015)

Labelled source text:

> Decimal

Surrounding canonical source context:

>  the data no differently than with other Python numeric
> types.
>
> .. %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
>
>
> .. _decimal-decimal:
>
> Decimal objects
> ---------------
>
>
> .. class:: Decimal(value="0", context=None)
>
>    Construct a new :class:`Decimal` object based from *value*.
>
>    *value* can be an integer, string, tuple, :class:`float`, or another :class:`Decimal`
>    object. If no *va

Labelled source text:

> *value* can be an integer, string, tuple, :class:`float`, or another :class:`Decimal`
>    object. If no *value* is given, returns ``Decimal('0')``.

Surrounding canonical source context:

> %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
>
>
> .. _decimal-decimal:
>
> Decimal objects
> ---------------
>
>
> .. class:: Decimal(value="0", context=None)
>
>    Construct a new :class:`Decimal` object based from *value*.
>
>    *value* can be an integer, string, tuple, :class:`float`, or another :class:`Decimal`
>    object. If no *value* is given, returns ``Decimal('0')``.  If *value* is a
>    string, it should conform to the decimal numeric string syntax after leading
>    and trailing whitespace characters, as well as underscores throughout, are removed::
>
>       sign

Review decision / disagreements / resolution: **pending**

## decimal-getcontext

held_out / decimal+fractions / paraphrase / draft

What does decimal.getcontext return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `decimal-getcontext`:

getcontext returns the current context for the active thread.

Alternative `decimal-getcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39151, 39161)
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39165, 39217)

Labelled source text:

> getcontext

Surrounding canonical source context:

>  as exceptions, and limit
> the range for exponents.
>
> Each thread has its own current context which is accessed or changed using the
> :func:`getcontext` and :func:`setcontext` functions:
>
>
> .. function:: getcontext()
>
>    Return the current context for the active thread.
>
>
> .. function:: setcontext(c, /)
>
>    Set the current context for the active thread to *c*.
>
> You can also use the :keyword:`with` statement and

Labelled source text:

>    Return the current context for the active thread.

Surrounding canonical source context:

> , and limit
> the range for exponents.
>
> Each thread has its own current context which is accessed or changed using the
> :func:`getcontext` and :func:`setcontext` functions:
>
>
> .. function:: getcontext()
>
>    Return the current context for the active thread.
>
>
> .. function:: setcontext(c, /)
>
>    Set the current context for the active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change

Review decision / disagreements / resolution: **pending**

## decimal-localcontext

held_out / decimal+fractions / exact_api / draft

How does decimal.localcontext isolate context changes?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `decimal-localcontext`:

localcontext sets a copy of the supplied context (or current context) on entering the with block and restores the previous context on exit.

Alternative `decimal-localcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39452, 39464)
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39486, 39837)

Labelled source text:

> localcontext

Surrounding canonical source context:

>    Set the current context for the active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change the active context.
>
> .. function:: localcontext(ctx=None, **kwargs)
>
>    Return a context manager that will set the current context for the active thread
>    to a copy of *ctx* on entry to the with-statement and restore the previous context
>    when

Labelled source text:

>    Return a context manager that will set the current context for the active thread
>    to a copy of *ctx* on entry to the with-statement and restore the previous context
>    when exiting the with-statement. If no context is specified, a copy of the
>    current context is used.  The *kwargs* argument is used to set the attributes
>    of the new context.

Surrounding canonical source context:

>  active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change the active context.
>
> .. function:: localcontext(ctx=None, **kwargs)
>
>    Return a context manager that will set the current context for the active thread
>    to a copy of *ctx* on entry to the with-statement and restore the previous context
>    when exiting the with-statement. If no context is specified, a copy of the
>    current context is used.  The *kwargs* argument is used to set the attributes
>    of the new context.
>
>    For example, the following code sets the current decimal precision to 42 places,
>    performs a calculation, and then automatically restores the previous context::
>
>       from decimal import local

Review decision / disagreements / resolution: **pending**

## decimal-setcontext

held_out / decimal+fractions / paraphrase / draft

How is the active decimal context replaced?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `decimal-setcontext`:

setcontext replaces the active thread’s current decimal context with c.

Alternative `decimal-setcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39234, 39244)
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39252, 39308)

Labelled source text:

> setcontext

Surrounding canonical source context:

>  context which is accessed or changed using the
> :func:`getcontext` and :func:`setcontext` functions:
>
>
> .. function:: getcontext()
>
>    Return the current context for the active thread.
>
>
> .. function:: setcontext(c, /)
>
>    Set the current context for the active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change the active context.
>
> .. fun

Labelled source text:

>    Set the current context for the active thread to *c*.

Surrounding canonical source context:

> accessed or changed using the
> :func:`getcontext` and :func:`setcontext` functions:
>
>
> .. function:: getcontext()
>
>    Return the current context for the active thread.
>
>
> .. function:: setcontext(c, /)
>
>    Set the current context for the active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change the active context.
>
> .. function:: localcontext(ctx=None, **kwargs)
>
>    Return a context ma

Review decision / disagreements / resolution: **pending**

## fractions-Fraction

held_out / decimal+fractions / exact_api / draft

Which numerator and denominator inputs can construct a Fraction?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `fractions-Fraction`:

The numerator/denominator constructor accepts numbers.Rational values and returns their ratio; a zero denominator raises ZeroDivisionError.

Alternative `fractions-Fraction`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [555, 563)
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [649, 913)

Labelled source text:

> Fraction

Surrounding canonical source context:

> rt for rational number arithmetic.
>
>
> A Fraction instance can be constructed from a pair of integers, from
> another rational number, or from a string.
>
> .. index:: single: as_integer_ratio()
>
> .. class:: Fraction(numerator=0, denominator=1)
>            Fraction(number)
>            Fraction(string)
>
>    The first version requires that *numerator* and *denominator* are instances
>    of :class:`numbers.Rational` and

Labelled source text:

>    The first version requires that *numerator* and *denominator* are instances
>    of :class:`numbers.Rational` and returns a new :class:`Fraction` instance
>    with value ``numerator/denominator``. If *denominator* is ``0``, it
>    raises a :exc:`ZeroDivisionError`.

Surrounding canonical source context:

> egers, from
> another rational number, or from a string.
>
> .. index:: single: as_integer_ratio()
>
> .. class:: Fraction(numerator=0, denominator=1)
>            Fraction(number)
>            Fraction(string)
>
>    The first version requires that *numerator* and *denominator* are instances
>    of :class:`numbers.Rational` and returns a new :class:`Fraction` instance
>    with value ``numerator/denominator``. If *denominator* is ``0``, it
>    raises a :exc:`ZeroDivisionError`.
>
>    The second version requires that *number* is an instance of
>    :class:`numbers.Rational` or has the :meth:`!as_integer_ratio` method
>    (this includes :class:`float` and :class:`decimal.Decimal`)

Review decision / disagreements / resolution: **pending**

## fractions-as_integer_ratio

held_out / decimal+fractions / paraphrase / draft

How does Fraction.as_integer_ratio represent a rational number?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `fractions-as_integer_ratio`:

Fraction.as_integer_ratio returns two integers whose ratio equals the Fraction, in lowest terms with a positive denominator.

Alternative `fractions-as_integer_ratio`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [4789, 4805)
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [4809, 4967)

Labelled source text:

> as_integer_ratio

Surrounding canonical source context:

> integer_ratio` method.
>
>    .. attribute:: numerator
>
>       Numerator of the Fraction in lowest term.
>
>    .. attribute:: denominator
>
>       Denominator of the Fraction in lowest term.
>
>
>    .. method:: as_integer_ratio()
>
>       Return a tuple of two integers, whose ratio is equal
>       to the original Fraction.  The ratio is in lowest terms
>       and has a positive denominator.
>
>       .. versionadded:: 3.8
>
>    .. m

Labelled source text:

>       Return a tuple of two integers, whose ratio is equal
>       to the original Fraction.  The ratio is in lowest terms
>       and has a positive denominator.

Surrounding canonical source context:

> d.
>
>    .. attribute:: numerator
>
>       Numerator of the Fraction in lowest term.
>
>    .. attribute:: denominator
>
>       Denominator of the Fraction in lowest term.
>
>
>    .. method:: as_integer_ratio()
>
>       Return a tuple of two integers, whose ratio is equal
>       to the original Fraction.  The ratio is in lowest terms
>       and has a positive denominator.
>
>       .. versionadded:: 3.8
>
>    .. method:: is_integer()
>
>       Return ``True`` if the Fraction is an integer.
>
>       .. versionadded:: 3.12
>
>    .. classmethod:: from_float(f)
>
>       Alternative con

Review decision / disagreements / resolution: **pending**

## fractions-limit_denominator

held_out / decimal+fractions / exact_api / draft

What does Fraction.limit_denominator approximate?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `fractions-limit_denominator`:

limit_denominator returns the closest Fraction whose denominator does not exceed max_denominator.

Alternative `fractions-limit_denominator`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [6174, 6191)
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [6218, 6434)

Labelled source text:

> limit_denominator

Surrounding canonical source context:

> lass:`numbers.Rational`,
>       :class:`float` or :class:`decimal.Decimal`, and objects with
>       the :meth:`!as_integer_ratio` method, but not strings.
>
>       .. versionadded:: 3.14
>
>
>    .. method:: limit_denominator(max_denominator=1000000)
>
>       Finds and returns the closest :class:`Fraction` to ``self`` that has
>       denominator at most max_denominator.  This method is useful for finding
>       rational appro

Labelled source text:

>       Finds and returns the closest :class:`Fraction` to ``self`` that has
>       denominator at most max_denominator.  This method is useful for finding
>       rational approximations to a given floating-point number:

Surrounding canonical source context:

> ` or :class:`decimal.Decimal`, and objects with
>       the :meth:`!as_integer_ratio` method, but not strings.
>
>       .. versionadded:: 3.14
>
>
>    .. method:: limit_denominator(max_denominator=1000000)
>
>       Finds and returns the closest :class:`Fraction` to ``self`` that has
>       denominator at most max_denominator.  This method is useful for finding
>       rational approximations to a given floating-point number:
>
>          >>> from fractions import Fraction
>          >>> Fraction('3.1415926535897932').limit_denominator(1000)
>          Fraction(355, 113)
>
>       or for recovering a rational number that's represen

Review decision / disagreements / resolution: **pending**

## fractions-from_float

held_out / decimal+fractions / paraphrase / draft

How does Fraction.from_float interpret a float value?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `fractions-from_float`:

from_float accepts float or numbers.Integral values; the float’s represented value is used, so from_float(0.3) differs from Fraction(3, 10).

Alternative `fractions-from_float`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [5131, 5141)
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [5146, 5351)

Labelled source text:

> from_float

Surrounding canonical source context:

>      and has a positive denominator.
>
>       .. versionadded:: 3.8
>
>    .. method:: is_integer()
>
>       Return ``True`` if the Fraction is an integer.
>
>       .. versionadded:: 3.12
>
>    .. classmethod:: from_float(f)
>
>       Alternative constructor which only accepts instances of
>       :class:`float` or :class:`numbers.Integral`. Beware that
>       ``Fraction.from_float(0.3)`` is not the same value as ``Fraction

Labelled source text:

>       Alternative constructor which only accepts instances of
>       :class:`float` or :class:`numbers.Integral`. Beware that
>       ``Fraction.from_float(0.3)`` is not the same value as ``Fraction(3, 10)``.

Surrounding canonical source context:

> positive denominator.
>
>       .. versionadded:: 3.8
>
>    .. method:: is_integer()
>
>       Return ``True`` if the Fraction is an integer.
>
>       .. versionadded:: 3.12
>
>    .. classmethod:: from_float(f)
>
>       Alternative constructor which only accepts instances of
>       :class:`float` or :class:`numbers.Integral`. Beware that
>       ``Fraction.from_float(0.3)`` is not the same value as ``Fraction(3, 10)``.
>
>       .. note::
>
>          From Python 3.2 onwards, you can also construct a
>          :class:`Fraction` instance directly from a :class:`float`.
>
>
>    .. classmethod:: from_decimal(dec)
>
>       Alterna

Review decision / disagreements / resolution: **pending**

## itertools-count

development / statistics+itertools / exact_api / draft

What values does itertools.count generate?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Included the signature so step and its defaults are supported rather than inferred from evenly spaced values.
- Removed map/zip usage examples from the evenly-spaced-sequence requirement.

Fact `itertools-count`:

itertools.count yields start, start+step, start+2*step, and so on; start defaults to 0 and step to 1.

Alternative `itertools-count`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15133, 15155)
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15160, 15237)

Labelled source text:

> count(start=0, step=1)

Surrounding canonical source context:

> (data, selectors):
>            # compress('ABCDEF', [1,0,1,0,1,1]) → A C E F
>            return (datum for datum, selector in zip(data, selectors) if selector)
>
>    .. versionadded:: 3.1
>
>
> .. function:: count(start=0, step=1)
>
>    Make an iterator that returns evenly spaced values beginning with
>    *start*. Can be used with :func:`map` to generate consecutive data
>    points or with :func:`zip` to add sequence numbers.  Rou

Labelled source text:

> Make an iterator that returns evenly spaced values beginning with
>    *start*.

Surrounding canonical source context:

>    # compress('ABCDEF', [1,0,1,0,1,1]) → A C E F
>            return (datum for datum, selector in zip(data, selectors) if selector)
>
>    .. versionadded:: 3.1
>
>
> .. function:: count(start=0, step=1)
>
>    Make an iterator that returns evenly spaced values beginning with
>    *start*. Can be used with :func:`map` to generate consecutive data
>    points or with :func:`zip` to add sequence numbers.  Roughly
>    equivalent to::
>
>       def count(start=0, step=1):
>           # count(10) →

Review decision / disagreements / resolution: **pending**

## itertools-cycle

development / statistics+itertools / paraphrase / draft

How does itertools.cycle reuse its input?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `itertools-cycle`:

itertools.cycle saves the iterable’s elements and repeats that saved sequence indefinitely.

Alternative `itertools-cycle`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15879, 15884)
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15899, 16080)

Labelled source text:

> cycle

Surrounding canonical source context:

> ved by substituting multiplicative code such as: ``(start + step * i
>    for i in count())``.
>
>    .. versionchanged:: 3.1
>       Added *step* argument and allowed non-integer arguments.
>
>
> .. function:: cycle(iterable)
>
>    Make an iterator returning elements from the *iterable* and saving a
>    copy of each.  When the iterable is exhausted, return elements from
>    the saved copy.  Repeats indefinitely.  Ro

Labelled source text:

> Make an iterator returning elements from the *iterable* and saving a
>    copy of each.  When the iterable is exhausted, return elements from
>    the saved copy.  Repeats indefinitely.

Surrounding canonical source context:

> multiplicative code such as: ``(start + step * i
>    for i in count())``.
>
>    .. versionchanged:: 3.1
>       Added *step* argument and allowed non-integer arguments.
>
>
> .. function:: cycle(iterable)
>
>    Make an iterator returning elements from the *iterable* and saving a
>    copy of each.  When the iterable is exhausted, return elements from
>    the saved copy.  Repeats indefinitely.  Roughly equivalent to::
>
>       def cycle(iterable):
>           # cycle('ABCD') → A B C D A B C D A B C D ...
>
>           saved = []
>           for element in iterable:
>               yield element
>

Review decision / disagreements / resolution: **pending**

## itertools-repeat

development / statistics+itertools / exact_api / draft

How does itertools.repeat control the number of repetitions?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `itertools-repeat`:

itertools.repeat yields the same object repeatedly, indefinitely when times is omitted or the specified number of times otherwise.

Alternative `itertools-repeat`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [25976, 25982)
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [26001, 26126)

Labelled source text:

> repeat

Surrounding canonical source context:

> :func:`product` runs, it completely consumes the input iterables,
>    keeping pools of values in memory to generate the products.  Accordingly,
>    it is only useful with finite inputs.
>
>
> .. function:: repeat(object[, times])
>
>    Make an iterator that returns *object* over and over again. Runs indefinitely
>    unless the *times* argument is specified.
>
>    Roughly equivalent to::
>
>       def repeat(object, t

Labelled source text:

>    Make an iterator that returns *object* over and over again. Runs indefinitely
>    unless the *times* argument is specified.

Surrounding canonical source context:

> completely consumes the input iterables,
>    keeping pools of values in memory to generate the products.  Accordingly,
>    it is only useful with finite inputs.
>
>
> .. function:: repeat(object[, times])
>
>    Make an iterator that returns *object* over and over again. Runs indefinitely
>    unless the *times* argument is specified.
>
>    Roughly equivalent to::
>
>       def repeat(object, times=None):
>           # repeat(10, 3) → 10 10 10
>           if times is None:
>               while True:
>                   yield object
>

Review decision / disagreements / resolution: **pending**

## itertools-chain

development / statistics+itertools / paraphrase / draft

How does itertools.chain combine iterables?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `itertools-chain`:

itertools.chain yields each iterable’s elements in sequence, moving to the next when the previous one is exhausted.

Alternative `itertools-chain`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [10847, 10852)
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [10869, 11038)

Labelled source text:

> chain

Surrounding canonical source context:

> n:
>                   raise ValueError('batched(): incomplete batch')
>               yield batch
>
>    .. versionadded:: 3.12
>
>    .. versionchanged:: 3.13
>       Added the *strict* option.
>
>
> .. function:: chain(*iterables)
>
>    Make an iterator that returns elements from the first iterable until
>    it is exhausted, then proceeds to the next iterable, until all of the
>    iterables are exhausted.  This combine

Labelled source text:

> Make an iterator that returns elements from the first iterable until
>    it is exhausted, then proceeds to the next iterable, until all of the
>    iterables are exhausted.

Surrounding canonical source context:

> aise ValueError('batched(): incomplete batch')
>               yield batch
>
>    .. versionadded:: 3.12
>
>    .. versionchanged:: 3.13
>       Added the *strict* option.
>
>
> .. function:: chain(*iterables)
>
>    Make an iterator that returns elements from the first iterable until
>    it is exhausted, then proceeds to the next iterable, until all of the
>    iterables are exhausted.  This combines multiple data sources into a
>    single iterator.  Roughly equivalent to::
>
>       def chain(*iterables):
>           # chain('ABC', 'DEF') → A B C D E F
>           for iterable in iterable

Review decision / disagreements / resolution: **pending**

## argparse-ArgumentParser

held_out / glob+argparse / exact_api / draft

What is the role of argparse.ArgumentParser?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old constructor sentence was circular; replaced it with the explicit role of the parser.

Fact `argparse-ArgumentParser`:

ArgumentParser is the container for argument specifications and parser-wide options used to build the command-line interface.

Alternative `argparse-ArgumentParser`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [1713, 1942)

Labelled source text:

> The :mod:`!argparse` module's support for command-line interfaces is built
> around an instance of :class:`argparse.ArgumentParser`.  It is a container for
> argument specifications and has options that apply to the parser as whole::

Surrounding canonical source context:

> se those out of :data:`sys.argv`.  The :mod:`!argparse`
> module also automatically generates help and usage messages.  The module
> will also issue errors when users give the program invalid arguments.
>
> The :mod:`!argparse` module's support for command-line interfaces is built
> around an instance of :class:`argparse.ArgumentParser`.  It is a container for
> argument specifications and has options that apply to the parser as whole::
>
>    parser = argparse.ArgumentParser(
>                        prog='ProgramName',
>                        description='What the program does',
>                        epilog='Text at the bottom of help'

Review decision / disagreements / resolution: **pending**

## argparse-parse_args

held_out / glob+argparse / paraphrase / draft

What is returned after ArgumentParser.parse_args interprets the command line?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `argparse-parse_args`:

parse_args interprets argument strings, assigns the converted values to namespace attributes, and returns the populated namespace.

Alternative `argparse-parse_args`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [55641, 55666)
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [55695, 55817)

Labelled source text:

> ArgumentParser.parse_args

Surrounding canonical source context:

>  action=argparse.BooleanOptionalAction)
>        >>> parser.parse_args(['--no-foo'])
>        Namespace(foo=False)
>
>    .. versionadded:: 3.9
>
>
> The parse_args() method
> -----------------------
>
> .. method:: ArgumentParser.parse_args(args=None, namespace=None)
>
>    Convert argument strings to objects and assign them as attributes of the
>    namespace.  Return the populated namespace.
>
>    Previous calls to :meth:`add_argument` deter

Labelled source text:

>    Convert argument strings to objects and assign them as attributes of the
>    namespace.  Return the populated namespace.

Surrounding canonical source context:

> ser.parse_args(['--no-foo'])
>        Namespace(foo=False)
>
>    .. versionadded:: 3.9
>
>
> The parse_args() method
> -----------------------
>
> .. method:: ArgumentParser.parse_args(args=None, namespace=None)
>
>    Convert argument strings to objects and assign them as attributes of the
>    namespace.  Return the populated namespace.
>
>    Previous calls to :meth:`add_argument` determine exactly what objects are
>    created and how they are assigned. See the documentation for
>    :meth:`!add_argument` for details.
>
>    * args_ - List

Review decision / disagreements / resolution: **pending**

## argparse-add_subparsers

held_out / glob+argparse / exact_api / draft

How does ArgumentParser.add_subparsers support subcommands?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Dropped the motivating svn examples, retaining the returned action and subparser construction behaviour.

Fact `argparse-add_subparsers`:

add_subparsers returns an action object whose add_parser method creates an ArgumentParser for a named subcommand.

Alternative `argparse-add_subparsers`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [63590, 63619)
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [64237, 64702)

Labelled source text:

> ArgumentParser.add_subparsers

Surrounding canonical source context:

>  >>> parser.add_argument('--foo')
>       >>> parser.parse_args(args=['--foo', 'BAR'], namespace=c)
>       >>> c.foo
>       'BAR'
>
>
> Other utilities
> ---------------
>
> Sub-commands
> ^^^^^^^^^^^^
>
> .. method:: ArgumentParser.add_subparsers(*, [title], [description], [prog], \
>                                           [parser_class], [action], \
>                                           [dest], [required], \
>

Labelled source text:

> :class:`ArgumentParser` supports the creation of such subcommands with the
>    :meth:`!add_subparsers` method.  The :meth:`!add_subparsers` method is normally
>    called with no arguments and returns a special action object.  This object
>    has a single method, :meth:`~_SubParsersAction.add_parser`, which takes a
>    command name and any :class:`!ArgumentParser` constructor arguments, and
>    returns an :class:`!ArgumentParser` object that can be modified as usual.

Surrounding canonical source context:

> vn commit``.  Splitting up functionality
>    this way can be a particularly good idea when a program performs several
>    different functions which require different kinds of command-line arguments.
>    :class:`ArgumentParser` supports the creation of such subcommands with the
>    :meth:`!add_subparsers` method.  The :meth:`!add_subparsers` method is normally
>    called with no arguments and returns a special action object.  This object
>    has a single method, :meth:`~_SubParsersAction.add_parser`, which takes a
>    command name and any :class:`!ArgumentParser` constructor arguments, and
>    returns an :class:`!ArgumentParser` object that can be modified as usual.
>
>    Description of parameters:
>
>    * *title* - title for the sub-parser group in help output; by default
>      "subcommands" if description is provided, otherwise uses title for
>      positional argume

Review decision / disagreements / resolution: **pending**

## argparse-parse_known_args

held_out / glob+argparse / paraphrase / draft

How does parse_known_args handle unrecognized command-line arguments?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old motivation paragraph omitted the actual no-error and two-item-return contract.

Fact `argparse-parse_known_args`:

parse_known_args parses known arguments without rejecting extra ones and returns (populated namespace, list of unrecognized arguments).

Alternative `argparse-parse_known_args`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [82068, 82099)
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [82375, 82666)

Labelled source text:

> ArgumentParser.parse_known_args

Surrounding canonical source context:

> turn a string containing a help message, including the program usage and
>    information about the arguments registered with the :class:`ArgumentParser`.
>
>
> Partial parsing
> ^^^^^^^^^^^^^^^
>
> .. method:: ArgumentParser.parse_known_args(args=None, namespace=None)
>
>    Sometimes a script only needs to handle a specific set of command-line
>    arguments, leaving any unrecognized arguments for another script or program.
>    In these cases

Labelled source text:

> This method works similarly to :meth:`~ArgumentParser.parse_args`, but it does
>    not raise an error for extra, unrecognized arguments. Instead, it parses the
>    known arguments and returns a two item tuple that contains the populated
>    namespace and the list of any unrecognized arguments.

Surrounding canonical source context:

> ecific set of command-line
>    arguments, leaving any unrecognized arguments for another script or program.
>    In these cases, the :meth:`~ArgumentParser.parse_known_args` method can be
>    useful.
>
>    This method works similarly to :meth:`~ArgumentParser.parse_args`, but it does
>    not raise an error for extra, unrecognized arguments. Instead, it parses the
>    known arguments and returns a two item tuple that contains the populated
>    namespace and the list of any unrecognized arguments.
>
>    ::
>
>       >>> parser = argparse.ArgumentParser()
>       >>> parser.add_argument('--foo', action='store_true')
>       >>> parser.add_argument('bar')
>       >>> parser.parse_known_args(['--foo', '--ba

Review decision / disagreements / resolution: **pending**

## compound-json-dumps-pickle-dumps

development / json+pickle / multi_source / draft

Which json function returns a JSON string rather than writing to a stream; and what type of result does pickle.dumps return?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the worked example that names json.dumps and shows its returned JSON string.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `json-dumps`:

json.dumps returns the serialized JSON representation as a string, rather than writing it to a stream.

Alternative `json-dumps`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [8462, 8467)
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [8692, 8861)

Labelled source text:

> dumps

Surrounding canonical source context:

> : 3.4
>       Use ``(',', ': ')`` as default if *indent* is not ``None``.
>
>    .. versionchanged:: 3.6
>       All optional parameters are now :ref:`keyword-only <keyword-only_parameter>`.
>
>
> .. function:: dumps(obj, *, skipkeys=False, ensure_ascii=True, \
>                     check_circular=True, allow_nan=True, cls=None, \
>                     indent=None, separators=None, default=None, \
>

Labelled source text:

>    Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
>    table <py-to-json-table>`.  The arguments have the same meaning as in
>    :func:`dump`.

Surrounding canonical source context:

> ensure_ascii=True, \
>                     check_circular=True, allow_nan=True, cls=None, \
>                     indent=None, separators=None, default=None, \
>                     sort_keys=False, **kw)
>
>    Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
>    table <py-to-json-table>`.  The arguments have the same meaning as in
>    :func:`dump`.
>
>    .. note::
>
>       Keys in key/value pairs of JSON are always of the type :class:`str`. When
>       a dictionary is converted into JSON, all the keys of the dictionary are
>       coerced to strings.

Alternative `json-dumps-worked-example`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [1366, 1471)

Labelled source text:

>     >>> json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
>     '["foo", {"bar": ["baz", null, 1.0, 2]}]'

Surrounding canonical source context:

> parsed is recommended.
>
> This module exposes an API familiar to users of the standard library
> :mod:`marshal` and :mod:`pickle` modules.
>
> Encoding basic Python object hierarchies::
>
>     >>> import json
>     >>> json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
>     '["foo", {"bar": ["baz", null, 1.0, 2]}]'
>     >>> print(json.dumps("\"foo\bar"))
>     "\"foo\bar"
>     >>> print(json.dumps('\u1234'))
>     "\u1234"
>     >>> print(json.dumps('\\'))
>     "\\"
>     >>> print(json.dumps({"c": 0, "b": 0, "a": 0}, sor

Fact `pickle-dumps`:

pickle.dumps returns the pickled representation as bytes rather than writing it to a file.

Alternative `pickle-dumps`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9717, 9722)
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9787, 9907)

Labelled source text:

> dumps

Surrounding canonical source context:

> tocol*, *fix_imports* and *buffer_callback* have
>    the same meaning as in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was added.
>
> .. function:: dumps(obj, protocol=None, *, fix_imports=True, buffer_callback=None)
>
>    Return the pickled representation of the object *obj* as a :class:`bytes` object,
>    instead of writing it to a file.
>
>    Arguments

Labelled source text:

>    Return the pickled representation of the object *obj* as a :class:`bytes` object,
>    instead of writing it to a file.

Surrounding canonical source context:

> s in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was added.
>
> .. function:: dumps(obj, protocol=None, *, fix_imports=True, buffer_callback=None)
>
>    Return the pickled representation of the object *obj* as a :class:`bytes` object,
>    instead of writing it to a file.
>
>    Arguments *protocol*, *fix_imports* and *buffer_callback* have the same
>    meaning as in the :class:`Pickler` constructor.
>
>    .. versionchanged:: 3.8
>       The *buffer_callback* argument was add

Review decision / disagreements / resolution: **pending**

## compound-csv-reader-gzip-decompress

development / csv+gzip / multi_source / draft

What does csv.reader produce from an iterable of lines; and can gzip.decompress handle concatenated gzip members?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old span described the input and reader object but omitted the returned row representation and conversion exception.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated configuration/performance text from a label whose question only asks the data/result behaviour.

Fact `csv-reader`:

csv.reader returns a reader object yielding rows as lists of strings; QUOTE_NONNUMERIC converts unquoted fields to floats instead.

Alternative `csv-reader`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2024, 2030)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2077, 2263)
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2925, 3168)

Labelled source text:

> reader

Surrounding canonical source context:

>  to Python.
>
>
> .. _csv-contents:
>
> Module Contents
> ---------------
>
> The :mod:`csv` module defines the following functions:
>
>
> .. index::
>    single: universal newlines; csv.reader function
>
> .. function:: reader(csvfile, /, dialect='excel', **fmtparams)
>
>    Return a :ref:`reader object <reader-objects>` that will process
>    lines from the given *csvfile*.  A csvfile must be an iterable of
>    strings, each in

Labelled source text:

> Return a :ref:`reader object <reader-objects>` that will process
>    lines from the given *csvfile*.  A csvfile must be an iterable of
>    strings, each in the reader's defined csv format.

Surrounding canonical source context:

> -----------
>
> The :mod:`csv` module defines the following functions:
>
>
> .. index::
>    single: universal newlines; csv.reader function
>
> .. function:: reader(csvfile, /, dialect='excel', **fmtparams)
>
>    Return a :ref:`reader object <reader-objects>` that will process
>    lines from the given *csvfile*.  A csvfile must be an iterable of
>    strings, each in the reader's defined csv format.
>    A csvfile is most commonly a file-like object or list.
>    If *csvfile* is a file object,
>    it should be opened with ``newline=''``. [1]_  An optional
>    *dialect* parameter can be given which is

Labelled source text:

> Each row read from the csv file is returned as a list of strings.  No
>    automatic data type conversion is performed unless the :data:`QUOTE_NONNUMERIC` format
>    option is specified (in which case unquoted fields are transformed into floats).

Surrounding canonical source context:

> uments
>    can be given to override individual formatting parameters in the current
>    dialect.  For full details about the dialect and formatting parameters, see
>    section :ref:`csv-fmt-params`.
>
>    Each row read from the csv file is returned as a list of strings.  No
>    automatic data type conversion is performed unless the :data:`QUOTE_NONNUMERIC` format
>    option is specified (in which case unquoted fields are transformed into floats).
>
>    A short usage example::
>
>       >>> import csv
>       >>> with open('eggs.csv', newline='') as csvfile:
>       ...     spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
>       ...     fo

Fact `gzip-decompress`:

gzip.decompress returns uncompressed bytes and supports concatenated gzip members.

Alternative `gzip-decompress`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [8899, 8909)
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [8917, 9127)

Labelled source text:

> decompress

Surrounding canonical source context:

> versionchanged:: 3.14
>       The *mtime* parameter now defaults to 0 for reproducible output.
>       For the previous behaviour of using the current time,
>       pass ``None`` to *mtime*.
>
> .. function:: decompress(data)
>
>    Decompress the *data*, returning a :class:`bytes` object containing the
>    uncompressed data. This function is capable of decompressing multi-member
>    gzip data (multiple gzip blocks conca

Labelled source text:

>    Decompress the *data*, returning a :class:`bytes` object containing the
>    uncompressed data. This function is capable of decompressing multi-member
>    gzip data (multiple gzip blocks concatenated together).

Surrounding canonical source context:

> .14
>       The *mtime* parameter now defaults to 0 for reproducible output.
>       For the previous behaviour of using the current time,
>       pass ``None`` to *mtime*.
>
> .. function:: decompress(data)
>
>    Decompress the *data*, returning a :class:`bytes` object containing the
>    uncompressed data. This function is capable of decompressing multi-member
>    gzip data (multiple gzip blocks concatenated together). When the data is
>    certain to contain only one member the :func:`zlib.decompress` function with
>    *wbits* set to 31 is faster.
>
>    .. versionadded:: 3.2
>    .. versionchanged:: 3.11
>       Speed is i

Review decision / disagreements / resolution: **pending**

## compound-lzma-compress-zlib-compress

development / lzma+zlib / multi_source / draft

How does lzma.compress return compressed data; and what does zlib.compress return for its data argument?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed unrelated configuration/performance text from a label whose question only asks the data/result behaviour.

Fact `lzma-compress`:

lzma.compress compresses bytes and returns the compressed data as bytes.

Alternative `lzma-compress`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12613, 12621)
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12684, 12790)

Labelled source text:

> compress

Surrounding canonical source context:

> ttribute:: needs_input
>
>       ``False`` if the :meth:`.decompress` method can provide more
>       decompressed data before requiring new uncompressed input.
>
>       .. versionadded:: 3.5
>
> .. function:: compress(data, format=FORMAT_XZ, check=-1, preset=None, filters=None)
>
>    Compress *data* (a :class:`bytes` object), returning the compressed data as a
>    :class:`bytes` object.
>
>    See :class:`LZMACompressor

Labelled source text:

>    Compress *data* (a :class:`bytes` object), returning the compressed data as a
>    :class:`bytes` object.

Surrounding canonical source context:

> od can provide more
>       decompressed data before requiring new uncompressed input.
>
>       .. versionadded:: 3.5
>
> .. function:: compress(data, format=FORMAT_XZ, check=-1, preset=None, filters=None)
>
>    Compress *data* (a :class:`bytes` object), returning the compressed data as a
>    :class:`bytes` object.
>
>    See :class:`LZMACompressor` above for a description of the *format*, *check*,
>    *preset* and *filters* arguments.
>
>
> .. function:: decompress(data, format=FORMAT_AUTO, memlimit=None, filters=None

Fact `zlib-compress`:

zlib.compress returns bytes containing the compressed input data.

Alternative `zlib-compress`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1933, 1941)
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1979, 2066)

Labelled source text:

> compress

Surrounding canonical source context:

>   the algorithm is designed for use as a checksum algorithm, it is not suitable
>    for use as a general hash algorithm.
>
>    .. versionchanged:: 3.0
>       The result is always unsigned.
>
> .. function:: compress(data, /, level=-1, wbits=MAX_WBITS)
>
>    Compresses the bytes in *data*, returning a bytes object containing compressed data.
>    *level* is an integer from ``0`` to ``9`` or ``-1`` controlling the lev

Labelled source text:

>    Compresses the bytes in *data*, returning a bytes object containing compressed data.

Surrounding canonical source context:

> sum algorithm, it is not suitable
>    for use as a general hash algorithm.
>
>    .. versionchanged:: 3.0
>       The result is always unsigned.
>
> .. function:: compress(data, /, level=-1, wbits=MAX_WBITS)
>
>    Compresses the bytes in *data*, returning a bytes object containing compressed data.
>    *level* is an integer from ``0`` to ``9`` or ``-1`` controlling the level of compression;
>    ``1`` (Z_BEST_SPEED) is fastest and produces the least compression, ``9`` (Z_BEST_COMPRESSION)
>    is sl

Review decision / disagreements / resolution: **pending**

## compound-pathlib-Path-shutil-copy2

development / pathlib+shutil / multi_source / draft

Which concrete path flavor is created by pathlib.Path; and how does shutil.copy2 differ from shutil.copy?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `pathlib-Path`:

Path creates a concrete PosixPath or WindowsPath according to the current system’s path flavour.

Alternative `pathlib-Path`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [23847, 23851)
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [23868, 24058)

Labelled source text:

> Path

Surrounding canonical source context:

> he pure path classes.  In addition to
> operations provided by the latter, they also provide methods to do system
> calls on path objects.  There are three ways to instantiate concrete paths:
>
> .. class:: Path(*pathsegments)
>
>    A subclass of :class:`PurePath`, this class represents concrete paths of
>    the system's path flavour (instantiating it creates either a
>    :class:`PosixPath` or a :class:`WindowsP

Labelled source text:

>    A subclass of :class:`PurePath`, this class represents concrete paths of
>    the system's path flavour (instantiating it creates either a
>    :class:`PosixPath` or a :class:`WindowsPath`)::

Surrounding canonical source context:

>   In addition to
> operations provided by the latter, they also provide methods to do system
> calls on path objects.  There are three ways to instantiate concrete paths:
>
> .. class:: Path(*pathsegments)
>
>    A subclass of :class:`PurePath`, this class represents concrete paths of
>    the system's path flavour (instantiating it creates either a
>    :class:`PosixPath` or a :class:`WindowsPath`)::
>
>       >>> Path('setup.py')
>       PosixPath('setup.py')
>
>    *pathsegments* is specified similarly to :class:`PurePath`.
>
> .. class:: PosixPath(*pathsegments)
>
>    A subclass of :class:`Path` and :class

Fact `shutil-copy2`:

copy2 behaves like copy but also attempts to preserve file metadata.

Alternative `shutil-copy2`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [8218, 8223)
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [8260, 8366)

Labelled source text:

> copy2

Surrounding canonical source context:

> tform-specific fast-copy syscalls may be used internally in order to
>       copy the file more efficiently. See
>       :ref:`shutil-platform-dependent-efficient-copy-operations` section.
>
> .. function:: copy2(src, dst, *, follow_symlinks=True)
>
>    Identical to :func:`~shutil.copy` except that :func:`copy2`
>    also attempts to preserve file metadata.
>
>    When *follow_symlinks* is false, and *src* is a symb

Labelled source text:

>    Identical to :func:`~shutil.copy` except that :func:`copy2`
>    also attempts to preserve file metadata.

Surrounding canonical source context:

> sed internally in order to
>       copy the file more efficiently. See
>       :ref:`shutil-platform-dependent-efficient-copy-operations` section.
>
> .. function:: copy2(src, dst, *, follow_symlinks=True)
>
>    Identical to :func:`~shutil.copy` except that :func:`copy2`
>    also attempts to preserve file metadata.
>
>    When *follow_symlinks* is false, and *src* is a symbolic
>    link, :func:`copy2` attempts to copy all metadata from the
>    *src* symbolic link to the newly created *dst* symbolic link.
>    However,

Review decision / disagreements / resolution: **pending**

## compound-re-fullmatch-bisect-bisect_left

development / re+bisect / multi_source / draft

When does re.fullmatch succeed; and where does bisect_left insert relative to existing equal values?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Scoped support to the question’s matching-position condition, not unrelated failure and zero-length notes.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `re-fullmatch`:

re.fullmatch succeeds when the entire string matches the pattern.

Alternative `re-fullmatch`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [39660, 39669)
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [39697, 39809)

Labelled source text:

> fullmatch

Surrounding canonical source context:

> tch`).
>
>    The expression's behaviour can be modified by specifying a *flags* value.
>    Values can be any of the `flags`_ variables, combined using bitwise OR
>    (the ``|`` operator).
>
>
> .. function:: fullmatch(pattern, string, flags=0)
>
>    If the whole *string* matches the regular expression *pattern*, return a
>    corresponding :class:`~re.Match`.  Return ``None`` if the string does not match
>    the patter

Labelled source text:

>    If the whole *string* matches the regular expression *pattern*, return a
>    corresponding :class:`~re.Match`.

Surrounding canonical source context:

>  can be modified by specifying a *flags* value.
>    Values can be any of the `flags`_ variables, combined using bitwise OR
>    (the ``|`` operator).
>
>
> .. function:: fullmatch(pattern, string, flags=0)
>
>    If the whole *string* matches the regular expression *pattern*, return a
>    corresponding :class:`~re.Match`.  Return ``None`` if the string does not match
>    the pattern; note that this is different from a zero-length match.
>
>    The expression's behaviour can be modified by specifying a *flags* value.
>    Va

Fact `bisect-bisect_left`:

bisect_left returns the sorted insertion position before any existing equal values.

Alternative `bisect-bisect_left`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [1720, 1731)
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [1769, 2219)

Labelled source text:

> bisect_left

Surrounding canonical source context:

> ing
>    :py:func:`~bisect.insort_left` on the same list from multiple threads
>    may result in the list becoming unsorted.
>
> .. _bisect functions:
>
> The following functions are provided:
>
>
> .. function:: bisect_left(a, x, lo=0, hi=len(a), *, key=None)
>
>    Locate the insertion point for *x* in *a* to maintain sorted order.
>    The parameters *lo* and *hi* may be used to specify a subset of the list
>    which should

Labelled source text:

>    Locate the insertion point for *x* in *a* to maintain sorted order.
>    The parameters *lo* and *hi* may be used to specify a subset of the list
>    which should be considered; by default the entire list is used.  If *x* is
>    already present in *a*, the insertion point will be before (to the left of)
>    any existing entries.  The return value is suitable for use as the first
>    parameter to ``list.insert()`` assuming that *a* is already sorted.

Surrounding canonical source context:

>  list from multiple threads
>    may result in the list becoming unsorted.
>
> .. _bisect functions:
>
> The following functions are provided:
>
>
> .. function:: bisect_left(a, x, lo=0, hi=len(a), *, key=None)
>
>    Locate the insertion point for *x* in *a* to maintain sorted order.
>    The parameters *lo* and *hi* may be used to specify a subset of the list
>    which should be considered; by default the entire list is used.  If *x* is
>    already present in *a*, the insertion point will be before (to the left of)
>    any existing entries.  The return value is suitable for use as the first
>    parameter to ``list.insert()`` assuming that *a* is already sorted.
>
>    The returned insertion point *ip* partitions the array *a* into two
>    slices such that ``all(elem < x for elem in a[lo : ip])`` is true for the
>    left slice and ``all(elem >= x for elem in a[ip

Review decision / disagreements / resolution: **pending**

## compound-statistics-mean-itertools-count

development / statistics+itertools / multi_source / draft

What average does statistics.mean calculate; and what values does itertools.count generate?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Added the independently sufficient arithmetic-mean definition under the same named API.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Included the signature so step and its defaults are supported rather than inferred from evenly spaced values.
- Removed map/zip usage examples from the evenly-spaced-sequence requirement.

Fact `statistics-mean`:

statistics.mean returns the arithmetic mean of the data.

Alternative `statistics-mean`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5027, 5031)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5039, 5122)

Labelled source text:

> mean

Surrounding canonical source context:

> Function details
> ----------------
>
> Note: The functions do not require the data given to them to be sorted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly call

Labelled source text:

>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.

Surrounding canonical source context:

> ails
> ----------------
>
> Note: The functions do not require the data given to them to be sorted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly called "the average", although it is only one of many
>    different mathematical averages.  It i

Alternative `statistics-mean-definition`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5027, 5031)
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5127, 5210)

Labelled source text:

> mean

Surrounding canonical source context:

> Function details
> ----------------
>
> Note: The functions do not require the data given to them to be sorted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly call

Labelled source text:

> The arithmetic mean is the sum of the data divided by the number of data
>    points.

Surrounding canonical source context:

> orted.
> However, for reading convenience, most of the examples show sorted sequences.
>
> .. function:: mean(data)
>
>    Return the sample arithmetic mean of *data* which can be a sequence or iterable.
>
>    The arithmetic mean is the sum of the data divided by the number of data
>    points.  It is commonly called "the average", although it is only one of many
>    different mathematical averages.  It is a measure of the central location of
>    the data.
>
>    If *data* is empty, :exc:`Statis

Fact `itertools-count`:

itertools.count yields start, start+step, start+2*step, and so on; start defaults to 0 and step to 1.

Alternative `itertools-count`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15133, 15155)
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15160, 15237)

Labelled source text:

> count(start=0, step=1)

Surrounding canonical source context:

> (data, selectors):
>            # compress('ABCDEF', [1,0,1,0,1,1]) → A C E F
>            return (datum for datum, selector in zip(data, selectors) if selector)
>
>    .. versionadded:: 3.1
>
>
> .. function:: count(start=0, step=1)
>
>    Make an iterator that returns evenly spaced values beginning with
>    *start*. Can be used with :func:`map` to generate consecutive data
>    points or with :func:`zip` to add sequence numbers.  Rou

Labelled source text:

> Make an iterator that returns evenly spaced values beginning with
>    *start*.

Surrounding canonical source context:

>    # compress('ABCDEF', [1,0,1,0,1,1]) → A C E F
>            return (datum for datum, selector in zip(data, selectors) if selector)
>
>    .. versionadded:: 3.1
>
>
> .. function:: count(start=0, step=1)
>
>    Make an iterator that returns evenly spaced values beginning with
>    *start*. Can be used with :func:`map` to generate consecutive data
>    points or with :func:`zip` to add sequence numbers.  Roughly
>    equivalent to::
>
>       def count(start=0, step=1):
>           # count(10) →

Review decision / disagreements / resolution: **pending**

## compound-base64-urlsafe_b64encode-hashlib-hexdigest

held_out / base64+hashlib / multi_source / draft

Which characters does URL-safe Base64 substitute; and how does hash.hexdigest differ from a byte digest?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Scoped the substitution fact to the requested character replacements, not unrelated return type/padding commentary.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Restricted the behaviour label to the complete answer-bearing sentences, rather than requiring unrelated surrounding options or examples.

Fact `base64-urlsafe_b64encode`:

URL-safe Base64 substitutes - for + and _ for / in the standard alphabet.

Alternative `base64-urlsafe_b64encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [3887, 3904)
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [4006, 4102)

Labelled source text:

> urlsafe_b64encode

Surrounding canonical source context:

> ss:`bytes`.
>
>
> .. function:: standard_b64decode(s)
>
>    Decode :term:`bytes-like object` or ASCII string *s* using the standard
>    Base64 alphabet and return the decoded :class:`bytes`.
>
>
> .. function:: urlsafe_b64encode(s)
>
>    Encode :term:`bytes-like object` *s* using the
>    URL- and filesystem-safe alphabet, which
>    substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
>    standard Base64 alphabet,

Labelled source text:

> substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
>    standard Base64 alphabet

Surrounding canonical source context:

> andard
>    Base64 alphabet and return the decoded :class:`bytes`.
>
>
> .. function:: urlsafe_b64encode(s)
>
>    Encode :term:`bytes-like object` *s* using the
>    URL- and filesystem-safe alphabet, which
>    substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
>    standard Base64 alphabet, and return the encoded :class:`bytes`.  The result
>    can still contain ``=``.
>
>
> .. function:: urlsafe_b64decode(s)
>
>    Decode :term:`bytes-like object` or ASCII string *s*
>    using the URL- and fil

Fact `hashlib-hexdigest`:

hash.hexdigest returns a hexadecimal string twice the byte digest length.

Alternative `hashlib-hexdigest`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7659, 7673)
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7680, 7805)

Labelled source text:

> hash.hexdigest

Surrounding canonical source context:

> urn the digest of the data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.
>
>
> .. method:: hash.hexdigest()
>
>    Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.  This may be used to
>    exchange the value safely in email or other

Labelled source text:

> Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.

Surrounding canonical source context:

>  data passed to the :meth:`update` method so far.
>    This is a bytes object of size :attr:`digest_size` which may contain bytes in
>    the whole range from 0 to 255.
>
>
> .. method:: hash.hexdigest()
>
>    Like :meth:`digest` except the digest is returned as a string object of
>    double length, containing only hexadecimal digits.  This may be used to
>    exchange the value safely in email or other non-binary environments.
>
>
> .. method:: hash.copy()
>
>    Return a copy ("clone") of the hash object.  This can be used to efficiently

Review decision / disagreements / resolution: **pending**

## compound-bz2-BZ2Compressor-sqlite3-register_adapter

held_out / bz2+sqlite3 / multi_source / draft

What is the purpose of BZ2Compressor; and how does sqlite3.register_adapter convert a Python type?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `bz2-BZ2Compressor`:

BZ2Compressor supports incremental compression; bz2.compress is the one-shot alternative.

Alternative `bz2-BZ2Compressor`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [6498, 6511)
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [6530, 6695)

Labelled source text:

> BZ2Compressor

Surrounding canonical source context:

> le simultaneous
>       readers or writers, just like its equivalent classes in :mod:`gzip` and
>       :mod:`lzma` have always been.
>
>
> Incremental (de)compression
> ---------------------------
>
> .. class:: BZ2Compressor(compresslevel=9)
>
>    Create a new compressor object. This object may be used to compress data
>    incrementally. For one-shot compression, use the :func:`compress` function
>    instead.
>
>    *compressle

Labelled source text:

>    Create a new compressor object. This object may be used to compress data
>    incrementally. For one-shot compression, use the :func:`compress` function
>    instead.

Surrounding canonical source context:

>  writers, just like its equivalent classes in :mod:`gzip` and
>       :mod:`lzma` have always been.
>
>
> Incremental (de)compression
> ---------------------------
>
> .. class:: BZ2Compressor(compresslevel=9)
>
>    Create a new compressor object. This object may be used to compress data
>    incrementally. For one-shot compression, use the :func:`compress` function
>    instead.
>
>    *compresslevel*, if given, must be an integer between ``1`` and ``9``. The
>    default is ``9``.
>
>    .. method:: compress(data)
>
>       Provide data to the compressor object. Returns a chunk of com

Fact `sqlite3-register_adapter`:

register_adapter registers a callable receiving an object of the named Python type and returning a value of a native SQLite type.

Alternative `sqlite3-register_adapter`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14596, 14612)
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14632, 14909)

Labelled source text:

> register_adapter

Surrounding canonical source context:

> n user-defined function callbacks are logged as unraisable exceptions.
>       Use an :func:`unraisable hook handler <sys.unraisablehook>` for
>       introspection of the failed callback.
>
> .. function:: register_adapter(type, adapter, /)
>
>    Register an *adapter* :term:`callable` to adapt the Python type *type*
>    into an SQLite type.
>    The adapter is called with a Python object of type *type* as its sole
>    argume

Labelled source text:

>    Register an *adapter* :term:`callable` to adapt the Python type *type*
>    into an SQLite type.
>    The adapter is called with a Python object of type *type* as its sole
>    argument, and must return a value of a
>    :ref:`type that SQLite natively understands <sqlite3-types>`.

Surrounding canonical source context:

> e logged as unraisable exceptions.
>       Use an :func:`unraisable hook handler <sys.unraisablehook>` for
>       introspection of the failed callback.
>
> .. function:: register_adapter(type, adapter, /)
>
>    Register an *adapter* :term:`callable` to adapt the Python type *type*
>    into an SQLite type.
>    The adapter is called with a Python object of type *type* as its sole
>    argument, and must return a value of a
>    :ref:`type that SQLite natively understands <sqlite3-types>`.
>
> .. function:: register_converter(typename, converter, /)
>
>    Register the *converter* :term:`callable` to convert SQLite objects of type
>    *typename* into a Python object of a specific type.
>    The

Review decision / disagreements / resolution: **pending**

## compound-tempfile-mkstemp-fnmatch-fnmatchcase

held_out / tempfile+fnmatch / multi_source / draft

Who is responsible for deleting files created by mkstemp; and how can shell wildcard matching remain case-sensitive?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old label covered secure creation but omitted who must delete the file.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Removed the handout alternative: its extracted prose does not identify this named API. The handout-only behavioural question remains supported.

Fact `tempfile-mkstemp`:

The caller of tempfile.mkstemp is responsible for deleting the temporary file when finished.

Alternative `tempfile-mkstemp`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [10262, 10269)
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [10792, 10918)

Labelled source text:

> mkstemp

Surrounding canonical source context:

> mporaryDirectory
>
>    .. versionadded:: 3.2
>
>    .. versionchanged:: 3.10
>       Added *ignore_cleanup_errors* parameter.
>
>    .. versionchanged:: 3.12
>       Added the *delete* parameter.
>
>
> .. function:: mkstemp(suffix=None, prefix=None, dir=None, text=False)
>
>    Creates a temporary file in the most secure manner possible.  There are
>    no race conditions in the file's creation, assuming that the platform
>

Labelled source text:

> Unlike :func:`TemporaryFile`, the user of :func:`mkstemp` is responsible
>    for deleting the temporary file when done with it.

Surrounding canonical source context:

> ating user ID.  If the
>    platform uses permission bits to indicate whether a file is executable,
>    the file is executable by no one.  The file descriptor is not inherited
>    by child processes.
>
>    Unlike :func:`TemporaryFile`, the user of :func:`mkstemp` is responsible
>    for deleting the temporary file when done with it.
>
>    If *suffix* is not ``None``, the file name will end with that suffix,
>    otherwise there will be no suffix.  :func:`mkstemp` does not put a dot
>    between the file name and the suffix; if you nee

Fact `fnmatch-fnmatchcase`:

Use fnmatch.fnmatchcase for case-sensitive shell wildcard matching without os.path.normcase normalization.

Alternative `fnmatch-fnmatchcase`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [2981, 2992)
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3005, 3198)

Labelled source text:

> fnmatchcase

Surrounding canonical source context:

> ctory with the
>    extension ``.txt``::
>
>       import fnmatch
>       import os
>
>       for file in os.listdir('.'):
>           if fnmatch.fnmatch(file, '*.txt'):
>               print(file)
>
>
> .. function:: fnmatchcase(name, pat)
>
>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.norm

Labelled source text:

>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.normcase`.

Surrounding canonical source context:

> ion ``.txt``::
>
>       import fnmatch
>       import os
>
>       for file in os.listdir('.'):
>           if fnmatch.fnmatch(file, '*.txt'):
>               print(file)
>
>
> .. function:: fnmatchcase(name, pat)
>
>    Test whether the filename string *name* matches the pattern string *pat*,
>    returning ``True`` or ``False``;
>    the comparison is case-sensitive and does not apply :func:`os.path.normcase`.
>
>
> .. function:: filter(names, pat)
>
>    Construct a list from those elements of the :term:`iterable` of filename
>    strings *names* that match the pattern string *pat*.
>    It is the same as ``[n for n

Review decision / disagreements / resolution: **pending**

## compound-collections-Counter-heapq-heappop

held_out / collections+heapq / multi_source / draft

What does collections.Counter count; and which element is returned by heapq.heappop?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `collections-Counter`:

Counter counts hashable objects, storing objects as dictionary keys and their counts as values; counts may be zero or negative.

Alternative `collections-Counter`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [10114, 10121)
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [10146, 10524)

Labelled source text:

> Counter

Surrounding canonical source context:

> )
>     >>> Counter(words).most_common(10)
>     [('the', 1143), ('and', 966), ('to', 762), ('of', 669), ('i', 631),
>      ('you', 554),  ('a', 546), ('my', 514), ('hamlet', 471), ('in', 451)]
>
> .. class:: Counter([iterable-or-mapping])
>
>     A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
>     It is a collection where elements are stored as dictionary keys
>     and their cou

Labelled source text:

>     A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
>     It is a collection where elements are stored as dictionary keys
>     and their counts are stored as dictionary values.  Counts are allowed to be
>     any integer value including zero or negative counts.  The :class:`Counter`
>     class is similar to bags or multisets in other languages.

Surrounding canonical source context:

> mmon(10)
>     [('the', 1143), ('and', 966), ('to', 762), ('of', 669), ('i', 631),
>      ('you', 554),  ('a', 546), ('my', 514), ('hamlet', 471), ('in', 451)]
>
> .. class:: Counter([iterable-or-mapping])
>
>     A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
>     It is a collection where elements are stored as dictionary keys
>     and their counts are stored as dictionary values.  Counts are allowed to be
>     any integer value including zero or negative counts.  The :class:`Counter`
>     class is similar to bags or multisets in other languages.
>
>     Elements are counted from an *iterable* or initialized from another
>     *mapping* (or counter):
>
>         >>> c = Counter()                           # a new, empty counter
>         >>> c = Counte

Fact `heapq-heappop`:

heappop removes and returns the smallest heap item while preserving the min-heap invariant.

Alternative `heapq-heappop`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2645, 2652)
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2660, 2872)

Labelled source text:

> heappop

Surrounding canonical source context:

>  respectively.
>
> The following functions are provided for min-heaps:
>
>
> .. function:: heappush(heap, item)
>
>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.
>
>
> .. function:: heappop(heap)
>
>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping

Labelled source text:

>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping it, use ``heap[0]``.

Surrounding canonical source context:

>
> The following functions are provided for min-heaps:
>
>
> .. function:: heappush(heap, item)
>
>    Push the value *item* onto the *heap*, maintaining the min-heap invariant.
>
>
> .. function:: heappop(heap)
>
>    Pop and return the smallest item from the *heap*, maintaining the min-heap
>    invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
>    smallest item without popping it, use ``heap[0]``.
>
>
> .. function:: heappushpop(heap, item)
>
>    Push *item* on the heap, then pop and return the smallest item from the
>    *heap*.  The combined action runs more efficiently than :func:`heappush`
>    foll

Review decision / disagreements / resolution: **pending**

## compound-decimal-localcontext-fractions-limit_denominator

held_out / decimal+fractions / multi_source / draft

How does decimal.localcontext isolate context changes; and what does Fraction.limit_denominator approximate?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.

Fact `decimal-localcontext`:

localcontext sets a copy of the supplied context (or current context) on entering the with block and restores the previous context on exit.

Alternative `decimal-localcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39452, 39464)
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39486, 39837)

Labelled source text:

> localcontext

Surrounding canonical source context:

>    Set the current context for the active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change the active context.
>
> .. function:: localcontext(ctx=None, **kwargs)
>
>    Return a context manager that will set the current context for the active thread
>    to a copy of *ctx* on entry to the with-statement and restore the previous context
>    when

Labelled source text:

>    Return a context manager that will set the current context for the active thread
>    to a copy of *ctx* on entry to the with-statement and restore the previous context
>    when exiting the with-statement. If no context is specified, a copy of the
>    current context is used.  The *kwargs* argument is used to set the attributes
>    of the new context.

Surrounding canonical source context:

>  active thread to *c*.
>
> You can also use the :keyword:`with` statement and the :func:`localcontext`
> function to temporarily change the active context.
>
> .. function:: localcontext(ctx=None, **kwargs)
>
>    Return a context manager that will set the current context for the active thread
>    to a copy of *ctx* on entry to the with-statement and restore the previous context
>    when exiting the with-statement. If no context is specified, a copy of the
>    current context is used.  The *kwargs* argument is used to set the attributes
>    of the new context.
>
>    For example, the following code sets the current decimal precision to 42 places,
>    performs a calculation, and then automatically restores the previous context::
>
>       from decimal import local

Fact `fractions-limit_denominator`:

limit_denominator returns the closest Fraction whose denominator does not exceed max_denominator.

Alternative `fractions-limit_denominator`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [6174, 6191)
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [6218, 6434)

Labelled source text:

> limit_denominator

Surrounding canonical source context:

> lass:`numbers.Rational`,
>       :class:`float` or :class:`decimal.Decimal`, and objects with
>       the :meth:`!as_integer_ratio` method, but not strings.
>
>       .. versionadded:: 3.14
>
>
>    .. method:: limit_denominator(max_denominator=1000000)
>
>       Finds and returns the closest :class:`Fraction` to ``self`` that has
>       denominator at most max_denominator.  This method is useful for finding
>       rational appro

Labelled source text:

>       Finds and returns the closest :class:`Fraction` to ``self`` that has
>       denominator at most max_denominator.  This method is useful for finding
>       rational approximations to a given floating-point number:

Surrounding canonical source context:

> ` or :class:`decimal.Decimal`, and objects with
>       the :meth:`!as_integer_ratio` method, but not strings.
>
>       .. versionadded:: 3.14
>
>
>    .. method:: limit_denominator(max_denominator=1000000)
>
>       Finds and returns the closest :class:`Fraction` to ``self`` that has
>       denominator at most max_denominator.  This method is useful for finding
>       rational approximations to a given floating-point number:
>
>          >>> from fractions import Fraction
>          >>> Fraction('3.1415926535897932').limit_denominator(1000)
>          Fraction(355, 113)
>
>       or for recovering a rational number that's represen

Review decision / disagreements / resolution: **pending**

## compound-glob-escape-argparse-parse_known_args

held_out / glob+argparse / multi_source / draft

How can glob.escape treat wildcard characters literally; and how does parse_known_args handle unrecognized command-line arguments?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- Verified the named API and surrounding pinned documentation; added its identifying declaration to the required evidence.
- The old motivation paragraph omitted the actual no-error and two-item-return contract.

Fact `glob-escape`:

glob.escape escapes ?, * and [ so they match literally; special characters in drive/UNC sharepoints are not escaped.

Alternative `glob-escape`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4442, 4448)
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4460, 4793)

Labelled source text:

> escape

Surrounding canonical source context:

> cursive globs using "``**``".
>
>    .. versionchanged:: 3.10
>       Added the *root_dir* and *dir_fd* parameters.
>
>    .. versionchanged:: 3.11
>       Added the *include_hidden* parameter.
>
>
> .. function:: escape(pathname)
>
>    Escape all special characters (``'?'``, ``'*'`` and ``'['``).
>    This is useful if you want to match an arbitrary literal string that may
>    have special characters in it.  Special char

Labelled source text:

>    Escape all special characters (``'?'``, ``'*'`` and ``'['``).
>    This is useful if you want to match an arbitrary literal string that may
>    have special characters in it.  Special characters in drive/UNC
>    sharepoints are not escaped, e.g. on Windows
>    ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.

Surrounding canonical source context:

> g "``**``".
>
>    .. versionchanged:: 3.10
>       Added the *root_dir* and *dir_fd* parameters.
>
>    .. versionchanged:: 3.11
>       Added the *include_hidden* parameter.
>
>
> .. function:: escape(pathname)
>
>    Escape all special characters (``'?'``, ``'*'`` and ``'['``).
>    This is useful if you want to match an arbitrary literal string that may
>    have special characters in it.  Special characters in drive/UNC
>    sharepoints are not escaped, e.g. on Windows
>    ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.
>
>    .. versionadded:: 3.4
>
>
> .. function:: translate(pathname, *, recursive=False, include_hidden=False, seps=None)
>
>    Convert the given path specification to a regular expression for use with
>    :fu

Fact `argparse-parse_known_args`:

parse_known_args parses known arguments without rejecting extra ones and returns (populated namespace, list of unrecognized arguments).

Alternative `argparse-parse_known_args`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [82068, 82099)
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [82375, 82666)

Labelled source text:

> ArgumentParser.parse_known_args

Surrounding canonical source context:

> turn a string containing a help message, including the program usage and
>    information about the arguments registered with the :class:`ArgumentParser`.
>
>
> Partial parsing
> ^^^^^^^^^^^^^^^
>
> .. method:: ArgumentParser.parse_known_args(args=None, namespace=None)
>
>    Sometimes a script only needs to handle a specific set of command-line
>    arguments, leaving any unrecognized arguments for another script or program.
>    In these cases

Labelled source text:

> This method works similarly to :meth:`~ArgumentParser.parse_args`, but it does
>    not raise an error for extra, unrecognized arguments. Instead, it parses the
>    known arguments and returns a two item tuple that contains the populated
>    namespace and the list of any unrecognized arguments.

Surrounding canonical source context:

> ecific set of command-line
>    arguments, leaving any unrecognized arguments for another script or program.
>    In these cases, the :meth:`~ArgumentParser.parse_known_args` method can be
>    useful.
>
>    This method works similarly to :meth:`~ArgumentParser.parse_args`, but it does
>    not raise an error for extra, unrecognized arguments. Instead, it parses the
>    known arguments and returns a two item tuple that contains the populated
>    namespace and the list of any unrecognized arguments.
>
>    ::
>
>       >>> parser = argparse.ArgumentParser()
>       >>> parser.add_argument('--foo', action='store_true')
>       >>> parser.add_argument('bar')
>       >>> parser.parse_known_args(['--foo', '--ba

Review decision / disagreements / resolution: **pending**

## unsupported-1

development / json+pickle / unsupported / draft

What is the internal Project Juniper API key rotation schedule?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-2

development / csv+gzip / unsupported / draft

Who owns the Acme payroll CSV export in our team?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-3

development / csv+gzip / unsupported / draft

What gzip compression level does our private backup service mandate?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-4

development / pathlib+shutil / unsupported / draft

Which directory contains our private workbench production credentials?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-5

development / statistics+itertools / unsupported / draft

What was the p95 latency of our service yesterday?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-6

development / re+bisect / unsupported / draft

Which regex did our team approve in ticket INTERNAL-928?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-7

held_out / base64+hashlib / unsupported / draft

What is our organization's private signing key encoded in Base64?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-8

held_out / bz2+sqlite3 / unsupported / draft

What is the password for our private reporting database?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-9

held_out / tempfile+fnmatch / unsupported / draft

Which filenames did our latest private deployment remove?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-10

held_out / collections+heapq / unsupported / draft

What heap size limit did our internal capacity review approve?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-11

held_out / decimal+fractions / unsupported / draft

Who approved our company's accounting rounding policy?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## unsupported-12

held_out / glob+argparse / unsupported / draft

Which command deployed our private application last Friday?

Expected answerable: False

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked question against the corpus scope: no private organization, secret, ownership, deployment or service telemetry data is supplied. Unsupported only relative to this corpus, not a claim about the outside world.

Review decision / disagreements / resolution: **pending**

## stress-revision

development / juniper-stress / revision / draft

Under revision 2, how many retries are permitted for JN-481?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Checked the named revision/subsystem and every support alternative against the complete short stress source or extracted handout pages.
- Added revision-2 identity to both alternatives; the retry number alone cannot establish the requested revision.

Fact `revision`:

JN-481 now allows five retries before operator escalation.

Alternative `revision`:
- `stress:retry-new.md` revision `f0cfe05b61ca05abbfddbbfed34ead46b7033daa152020d39ea86ccecd63f2d1` extracted-text characters [36, 126)

Labelled source text:

> Revision 2 replaces revision 1. JN-481 now allows five retries before operator escalation.

Surrounding canonical source context:

> # Juniper retry policy, revision 2
>
> Revision 2 replaces revision 1. JN-481 now allows five retries before operator escalation.

Alternative `revision-alternative`:
- `stress:retry-copy.md` revision `d4021474303e3649238d0f23ea296cc916568be7351cbae87b600d84a9527311` extracted-text characters [29, 39)
- `stress:retry-copy.md` revision `d4021474303e3649238d0f23ea296cc916568be7351cbae87b600d84a9527311` extracted-text characters [41, 99)

Labelled source text:

> revision 2

Surrounding canonical source context:

> # Juniper operator handbook, revision 2
>
> JN-481 now allows five retries before operator escalation.

Labelled source text:

> JN-481 now allows five retries before operator escalation.

Surrounding canonical source context:

> # Juniper operator handbook, revision 2
>
> JN-481 now allows five retries before operator escalation.

Review decision / disagreements / resolution: **pending**

## stress-old-revision

development / juniper-stress / revision / draft

Under revision 1, how many retries were permitted for JN-481?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the named revision/subsystem and every support alternative against the complete short stress source or extracted handout pages.

Fact `old-revision`:

Revision 1 allows two retries for JN-481 before operator escalation.

Alternative `old-revision`:
- `stress:retry-old.md` revision `5bd58e8c336e10d2c19aa03ef5efe7fd6ad88aad6eb4d4052d7e0b823cbe652e` extracted-text characters [36, 104)

Labelled source text:

> Revision 1 allows two retries for JN-481 before operator escalation.

Surrounding canonical source context:

> # Juniper retry policy, revision 1
>
> Revision 1 allows two retries for JN-481 before operator escalation.

Review decision / disagreements / resolution: **pending**

## stress-distractor

development / juniper-stress / hard_distractor / draft

How many retries are permitted for JN-482, the other subsystem?

Expected answerable: True

AI self-review: **retained**, 2026-10-12. Independent human approval remains pending.

- Checked the named revision/subsystem and every support alternative against the complete short stress source or extracted handout pages.

Fact `distractor`:

JN-482 allows nine retries.

Alternative `distractor`:
- `stress:retry-distractor.md` revision `fe8a1ce83a0731a8746a224b224028ecb420994f29fcce7920c4cebdccb72435` extracted-text characters [41, 68)

Labelled source text:

> JN-482 allows nine retries.

Surrounding canonical source context:

> # Juniper retry policy, other subsystem
>
> JN-482 allows nine retries. This setting does not apply to JN-481.

Review decision / disagreements / resolution: **pending**

## pdf-two-page

held_out / tempfile+fnmatch / multi_page / draft

In the fnmatch handout, how do case-sensitive matching and filtering a list of filenames work?

Expected answerable: True

AI self-review: **corrected**, 2026-10-12. Independent human approval remains pending.

- Checked the named revision/subsystem and every support alternative against the complete short stress source or extracted handout pages.

Fact `pdf-case`:

Test whether the filename string name matches the pattern string pat, returning True or False; the comparison is case-sensitive and does not apply os.path.normcase.

Alternative `fnmatch-fnmatchcase-pdf-alternative`:
- `python314:fnmatch-pdf` revision `ac393dc047e2b294804c60022762465fcc45cad8a65ba3214dc76bab9143abdd` extracted-text characters [0, 185)

Labelled source text:

> Test whether the filename string *name* matches the pattern string *pat*,
> returning ‘‘True‘‘ or ‘‘False‘‘; the comparison is case-sensitive and does not
> apply :func:‘os.path.normcase‘.

Surrounding canonical source context:

> Test whether the filename string *name* matches the pattern string *pat*,
> returning ‘‘True‘‘ or ‘‘False‘‘; the comparison is case-sensitive and does not
> apply :func:‘os.path.normcase‘.
>
>
> Construct a list from those elements of the :term:‘iterable‘ of filename strings
> *names* that match the pattern string *pat*. It is the same as ‘‘[n for n in
> names if fnmatch(n, pat)]‘‘, but impleme

Fact `pdf-filter`:

Construct a list from those elements of the iterable of filename strings names that match the pattern string pat. It is the same as [n for n in names if fnmatch(n, pat)], but implemented more efficiently.

Alternative `fnmatch-filter-pdf-alternative`:
- `python314:fnmatch-pdf` revision `ac393dc047e2b294804c60022762465fcc45cad8a65ba3214dc76bab9143abdd` extracted-text characters [185, 187)

Labelled source text:

>
>

Surrounding canonical source context:

> Test whether the filename string *name* matches the pattern string *pat*,
> returning ‘‘True‘‘ or ‘‘False‘‘; the comparison is case-sensitive and does not
> apply :func:‘os.path.normcase‘.
>
>
> Construct a list from those elements of the :term:‘iterable‘ of filename strings
> *names* that match the pattern string *pat*. It is the same as ‘‘[n for n in
> names if fnmatch(n, pat)]‘‘, but implement

Review decision / disagreements / resolution: **pending**
