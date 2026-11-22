# English technical-workbench annotation review

Dataset SHA-256: `3828ea7f9332975c2b0447958126ebe8bc06589b78a740fe336542d33b087365`

All annotations are authored drafts. An independent reviewer must check the question, answerability, required facts, each complete alternative, source revision and offsets, category and grouping. Check surrounding source context, not just the excerpt. Record disagreements and resolve them before approval. Do not infer correctness from a successful loader check or approve unseen questions.

To approve reviewed labels, set each dataset query review.status to approved and review.reviewer to your identity. Keep the author identity. Add review notes for disputed or revised labels. Update the dataset version when facts/splits change; rerun recorded comparisons against the new manifest hash. No runner auto-approves annotations.

## json-dumps

development / json+pickle / exact_api / draft

Which json function returns a JSON string rather than writing to a stream?

Expected answerable: True

Fact `json-dumps`:

Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
   table <py-to-json-table>`.  The arguments have the same meaning as in
   :func:`dump`.

Alternative `json-dumps`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [8692, 8861)

Review decision / disagreements / resolution: **pending**

## json-load

development / json+pickle / paraphrase / draft

How does json.load read a serialized value?

Expected answerable: True

Fact `json-load`:

Deserialize *fp* to a Python object
   using the :ref:`JSON-to-Python conversion table <json-to-py-table>`.

Alternative `json-load`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [9462, 9572)

Review decision / disagreements / resolution: **pending**

## json-JSONDecoder

development / json+pickle / exact_api / draft

What job does JSONDecoder perform?

Expected answerable: True

Fact `json-JSONDecoder`:

Simple JSON decoder.

Alternative `json-JSONDecoder`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [13630, 13653)

Review decision / disagreements / resolution: **pending**

## json-JSONEncoder

development / json+pickle / paraphrase / draft

What is JSONEncoder used for?

Expected answerable: True

Fact `json-JSONEncoder`:

Extensible JSON encoder for Python data structures.

Alternative `json-JSONEncoder`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [17393, 17447)

Review decision / disagreements / resolution: **pending**

## csv-reader

development / csv+gzip / exact_api / draft

What does csv.reader produce from an iterable of lines?

Expected answerable: True

Fact `csv-reader`:

Return a :ref:`reader object <reader-objects>` that will process
   lines from the given *csvfile*.  A csvfile must be an iterable of
   strings, each in the reader's defined csv format.
   A csvfile is most commonly a file-like object or list.
   If *csvfile* is a file object,
   it should be opened with ``newline=''``. [1]_  An optional
   *dialect* parameter can be given which is used to define a set of parameters
   specific to a particular CSV dialect.  It may be an instance of a subclass of
   the :class:`Dialect` class or one of the strings returned by the
   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments
   can be given to override individual formatting parameters in the current
   dialect.  For full details about the dialect and formatting parameters, see
   section :ref:`csv-fmt-params`.

Alternative `csv-reader`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2074, 2920)

Review decision / disagreements / resolution: **pending**

## csv-writer

development / csv+gzip / paraphrase / draft

How does csv.writer use its output object?

Expected answerable: True

Fact `csv-writer`:

Return a writer object responsible for converting the user's data into delimited
   strings on the given file-like object.  *csvfile* can be any object with a
   :meth:`~io.TextIOBase.write` method.

Alternative `csv-writer`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [3583, 3784)

Review decision / disagreements / resolution: **pending**

## csv-DictReader

development / csv+gzip / exact_api / draft

How are field names determined by csv.DictReader?

Expected answerable: True

Fact `csv-DictReader`:

The *fieldnames* parameter is a :term:`sequence`.  If *fieldnames* is
   omitted, the values in the first row of file *f* will be used as the
   fieldnames and will be omitted from the results. If
   *fieldnames* is provided, they will be used and the first row will be
   included in the results.  Regardless of how the fieldnames are determined,
   the dictionary preserves their original ordering.

Alternative `csv-DictReader`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [6603, 7006)

Review decision / disagreements / resolution: **pending**

## csv-DictWriter

development / csv+gzip / paraphrase / draft

How does csv.DictWriter map dictionaries onto output columns?

Expected answerable: True

Fact `csv-DictWriter`:

Create an object which operates like a regular writer but maps dictionaries
   onto output rows.  The *fieldnames* parameter is a :mod:`sequence
   <collections.abc>` of keys that identify the order in which values in the
   dictionary passed to the :meth:`~csvwriter.writerow` method are written to file
   *f*.

Alternative `csv-DictWriter`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [8200, 8515)

Review decision / disagreements / resolution: **pending**

## pickle-dump

development / json+pickle / exact_api / draft

Where does pickle.dump write its serialized representation?

Expected answerable: True

Fact `pickle-dump`:

Write the pickled representation of the object *obj* to the open
   :term:`file object` *file*.  This is equivalent to
   ``Pickler(file, protocol).dump(obj)``.

Alternative `pickle-dump`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9327, 9490)

Review decision / disagreements / resolution: **pending**

## pickle-dumps

development / json+pickle / paraphrase / draft

What type of result does pickle.dumps return?

Expected answerable: True

Fact `pickle-dumps`:

Return the pickled representation of the object *obj* as a :class:`bytes` object,
   instead of writing it to a file.

Alternative `pickle-dumps`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9787, 9907)

Review decision / disagreements / resolution: **pending**

## pickle-load

development / json+pickle / exact_api / draft

What does pickle.load reconstruct from a file?

Expected answerable: True

Fact `pickle-load`:

Read the pickled representation of an object from the open :term:`file object`
   *file* and return the reconstituted object hierarchy specified therein.
   This is equivalent to ``Unpickler(file).load()``.

Alternative `pickle-load`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [10208, 10417)

Review decision / disagreements / resolution: **pending**

## pickle-loads

development / json+pickle / paraphrase / draft

How does pickle.loads reconstruct an object from bytes?

Expected answerable: True

Fact `pickle-loads`:

Return the reconstituted object hierarchy of the pickled representation
   *data* of an object. *data* must be a :term:`bytes-like object`.

Alternative `pickle-loads`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [10909, 11051)

Review decision / disagreements / resolution: **pending**

## hashlib-new

held_out / base64+hashlib / exact_api / draft

How can hashlib create a hash object by algorithm name?

Expected answerable: True

Fact `hashlib-new`:

Is a generic constructor that takes the string *name* of the desired
   algorithm as its first parameter.  It also exists to allow access to the
   above listed hashes as well as any other algorithms that your OpenSSL
   library may offer.

Alternative `hashlib-new`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [4497, 4739)

Review decision / disagreements / resolution: **pending**

## hashlib-update

held_out / base64+hashlib / paraphrase / draft

What happens when hash.update is called repeatedly?

Expected answerable: True

Fact `hashlib-update`:

Update the hash object with the :term:`bytes-like object`.
   Repeated calls are equivalent to a single call with the
   concatenation of all the arguments: ``m.update(a); m.update(b)`` is
   equivalent to ``m.update(a+b)``.

Alternative `hashlib-update`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7196, 7423)

Review decision / disagreements / resolution: **pending**

## hashlib-digest

held_out / base64+hashlib / exact_api / draft

What representation does hash.digest return?

Expected answerable: True

Fact `hashlib-digest`:

Return the digest of the data passed to the :meth:`update` method so far.
   This is a bytes object of size :attr:`digest_size` which may contain bytes in
   the whole range from 0 to 255.

Alternative `hashlib-digest`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7453, 7644)

Review decision / disagreements / resolution: **pending**

## hashlib-hexdigest

held_out / base64+hashlib / paraphrase / draft

How does hash.hexdigest differ from a byte digest?

Expected answerable: True

Fact `hashlib-hexdigest`:

Like :meth:`digest` except the digest is returned as a string object of
   double length, containing only hexadecimal digits.  This may be used to
   exchange the value safely in email or other non-binary environments.

Alternative `hashlib-hexdigest`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7677, 7898)

Review decision / disagreements / resolution: **pending**

## base64-b64encode

held_out / base64+hashlib / exact_api / draft

What input and output types are used by base64.b64encode?

Expected answerable: True

Fact `base64-b64encode`:

Encode the :term:`bytes-like object` *s* using Base64 and return the encoded
   :class:`bytes`.

Alternative `base64-b64encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [2063, 2161)

Review decision / disagreements / resolution: **pending**

## base64-b64decode

held_out / base64+hashlib / paraphrase / draft

How can base64.b64decode validate non-alphabet input?

Expected answerable: True

Fact `base64-b64decode`:

If *validate* is ``False`` (the default), characters that are neither
   in the normal base-64 alphabet nor the alternative alphabet are
   discarded prior to the padding check.  If *validate* is ``True``,
   these non-alphabet characters in the input result in a
   :exc:`binascii.Error`.

Alternative `base64-b64decode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [3081, 3373)

Review decision / disagreements / resolution: **pending**

## base64-urlsafe_b64encode

held_out / base64+hashlib / exact_api / draft

Which characters does URL-safe Base64 substitute?

Expected answerable: True

Fact `base64-urlsafe_b64encode`:

Encode :term:`bytes-like object` *s* using the
   URL- and filesystem-safe alphabet, which
   substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
   standard Base64 alphabet, and return the encoded :class:`bytes`.  The result
   can still contain ``=``.

Alternative `base64-urlsafe_b64encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [3909, 4182)

Review decision / disagreements / resolution: **pending**

## base64-b32encode

held_out / base64+hashlib / paraphrase / draft

How do I encode bytes using Base32 in Python?

Expected answerable: True

Fact `base64-b32encode`:

Encode the :term:`bytes-like object` *s* using Base32 and return the
   encoded :class:`bytes`.

Alternative `base64-b32encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [4504, 4602)

Review decision / disagreements / resolution: **pending**

## gzip-open

development / csv+gzip / exact_api / draft

What file object does gzip.open return?

Expected answerable: True

Fact `gzip-open`:

Open a gzip-compressed file in binary or text mode, returning a :term:`file
   object`.

Alternative `gzip-open`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [1167, 1257)

Review decision / disagreements / resolution: **pending**

## gzip-compress

development / csv+gzip / paraphrase / draft

How do I compress bytes into gzip format without creating a file?

Expected answerable: True

Fact `gzip-compress`:

Compress the *data*, returning a :class:`bytes` object containing
   the compressed data.  *compresslevel* and *mtime* have the same meaning as in
   the :class:`GzipFile` constructor above,
   but *mtime* defaults to 0 for reproducible output.

Alternative `gzip-compress`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [7795, 8042)

Review decision / disagreements / resolution: **pending**

## gzip-decompress

development / csv+gzip / exact_api / draft

Can gzip.decompress handle concatenated gzip members?

Expected answerable: True

Fact `gzip-decompress`:

Decompress the *data*, returning a :class:`bytes` object containing the
   uncompressed data. This function is capable of decompressing multi-member
   gzip data (multiple gzip blocks concatenated together). When the data is
   certain to contain only one member the :func:`zlib.decompress` function with
   *wbits* set to 31 is faster.

Alternative `gzip-decompress`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [8917, 9256)

Review decision / disagreements / resolution: **pending**

## gzip-GzipFile

development / csv+gzip / paraphrase / draft

What does the GzipFile constructor represent?

Expected answerable: True

Fact `gzip-GzipFile`:

Constructor for the :class:`GzipFile` class, which simulates most of the
   methods of a :term:`file object`, with the exception of the :meth:`~io.IOBase.truncate`
   method.  At least one of *fileobj* and *filename* must be given a non-trivial
   value.

Alternative `gzip-GzipFile`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [2798, 3055)

Review decision / disagreements / resolution: **pending**

## bz2-open

held_out / bz2+sqlite3 / exact_api / draft

What modes does bz2.open support?

Expected answerable: True

Fact `bz2-open`:

Open a bzip2-compressed file in binary or text mode, returning a :term:`file
   object`.

Alternative `bz2-open`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [1089, 1180)

Review decision / disagreements / resolution: **pending**

## bz2-compress

held_out / bz2+sqlite3 / paraphrase / draft

What input does bz2.compress compress?

Expected answerable: True

Fact `bz2-compress`:

Compress *data*, a :term:`bytes-like object <bytes-like object>`.

Alternative `bz2-compress`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [9663, 9731)

Review decision / disagreements / resolution: **pending**

## bz2-decompress

held_out / bz2+sqlite3 / exact_api / draft

What input does bz2.decompress accept?

Expected answerable: True

Fact `bz2-decompress`:

Decompress *data*, a :term:`bytes-like object <bytes-like object>`.

Alternative `bz2-decompress`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [9937, 10007)

Review decision / disagreements / resolution: **pending**

## bz2-BZ2Compressor

held_out / bz2+sqlite3 / paraphrase / draft

What is the purpose of BZ2Compressor?

Expected answerable: True

Fact `bz2-BZ2Compressor`:

Create a new compressor object. This object may be used to compress data
   incrementally. For one-shot compression, use the :func:`compress` function
   instead.

Alternative `bz2-BZ2Compressor`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [6530, 6695)

Review decision / disagreements / resolution: **pending**

## lzma-open

development / lzma+zlib / exact_api / draft

What modes does lzma.open support?

Expected answerable: True

Fact `lzma-open`:

Open an LZMA-compressed file in binary or text mode, returning a :term:`file
   object`.

Alternative `lzma-open`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [1357, 1448)

Review decision / disagreements / resolution: **pending**

## lzma-compress

development / lzma+zlib / paraphrase / draft

How does lzma.compress return compressed data?

Expected answerable: True

Fact `lzma-compress`:

Compress *data* (a :class:`bytes` object), returning the compressed data as a
   :class:`bytes` object.

Alternative `lzma-compress`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12684, 12790)

Review decision / disagreements / resolution: **pending**

## lzma-decompress

development / lzma+zlib / exact_api / draft

What does the one-shot lzma.decompress function return?

Expected answerable: True

Fact `lzma-decompress`:

Decompress *data* (a :class:`bytes` object), returning the uncompressed data
   as a :class:`bytes` object.

Alternative `lzma-decompress`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12993, 13103)

Review decision / disagreements / resolution: **pending**

## lzma-LZMACompressor

development / lzma+zlib / paraphrase / draft

Why use LZMACompressor rather than a one-shot operation?

Expected answerable: True

Fact `lzma-LZMACompressor`:

Create a compressor object, which can be used to compress data incrementally.

Alternative `lzma-LZMACompressor`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [5949, 6029)

Review decision / disagreements / resolution: **pending**

## zlib-adler32

development / lzma+zlib / exact_api / draft

What kind of checksum does zlib.adler32 calculate?

Expected answerable: True

Fact `zlib-adler32`:

Computes an Adler-32 checksum of *data*.  (An Adler-32 checksum is almost as
   reliable as a CRC32 but can be computed much more quickly.)  The result
   is an unsigned 32-bit integer.  If *value* is present, it is used as
   the starting value of the checksum; otherwise, a default value of 1
   is used.  Passing in *value* allows computing a running checksum over the
   concatenation of several inputs.  The algorithm is not cryptographically
   strong, and should not be used for authentication or digital signatures.  Since
   the algorithm is designed for use as a checksum algorithm, it is not suitable
   for use as a general hash algorithm.

Alternative `zlib-adler32`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1198, 1852)

Review decision / disagreements / resolution: **pending**

## zlib-crc32

development / lzma+zlib / paraphrase / draft

What kind of checksum does zlib.crc32 return?

Expected answerable: True

Fact `zlib-crc32`:

Computes a CRC (Cyclic Redundancy Check) checksum of *data*. The
   result is an unsigned 32-bit integer. If *value* is present, it is used
   as the starting value of the checksum; otherwise, a default value of 0
   is used.  Passing in *value* allows computing a running checksum over the
   concatenation of several inputs.  The algorithm is not cryptographically
   strong, and should not be used for authentication or digital signatures.  Since
   the algorithm is designed for use as a checksum algorithm, it is not suitable
   for use as a general hash algorithm.

Alternative `zlib-crc32`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [5731, 6304)

Review decision / disagreements / resolution: **pending**

## zlib-compress

development / lzma+zlib / exact_api / draft

What does zlib.compress return for its data argument?

Expected answerable: True

Fact `zlib-compress`:

Compresses the bytes in *data*, returning a bytes object containing compressed data.
   *level* is an integer from ``0`` to ``9`` or ``-1`` controlling the level of compression;
   ``1`` (Z_BEST_SPEED) is fastest and produces the least compression, ``9`` (Z_BEST_COMPRESSION)
   is slowest and produces the most.  ``0`` (Z_NO_COMPRESSION) is no compression.
   The default value is ``-1`` (Z_DEFAULT_COMPRESSION).  Z_DEFAULT_COMPRESSION represents a default
   compromise between speed and compression (currently equivalent to level 6).

Alternative `zlib-compress`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1979, 2518)

Review decision / disagreements / resolution: **pending**

## zlib-decompress

development / lzma+zlib / paraphrase / draft

Which input does zlib.decompress expand?

Expected answerable: True

Fact `zlib-decompress`:

Decompresses the bytes in *data*, returning a bytes object containing the
   uncompressed data.  The *wbits* parameter depends on
   the format of *data*, and is discussed further below.
   If *bufsize* is given, it is used as the initial size of the output
   buffer.  Raises the :exc:`error` exception if any error occurs.

Alternative `zlib-decompress`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [6445, 6772)

Review decision / disagreements / resolution: **pending**

## sqlite3-connect

held_out / bz2+sqlite3 / exact_api / draft

What does sqlite3.connect return for a database path?

Expected answerable: True

Fact `sqlite3-connect`:

Open a connection to an SQLite database.

Alternative `sqlite3-connect`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [9083, 9126)

Review decision / disagreements / resolution: **pending**

## sqlite3-complete_statement

held_out / bz2+sqlite3 / paraphrase / draft

What does sqlite3.complete_statement check about SQL text?

Expected answerable: True

Fact `sqlite3-complete_statement`:

Return ``True`` if the string *statement* appears to contain
   one or more complete SQL statements.
   No syntactic verification or parsing of any kind is performed,
   other than checking that there are no unclosed string literals
   and the statement is terminated by a semicolon.

Alternative `sqlite3-complete_statement`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [13183, 13469)

Review decision / disagreements / resolution: **pending**

## sqlite3-register_adapter

held_out / bz2+sqlite3 / exact_api / draft

How does sqlite3.register_adapter convert a Python type?

Expected answerable: True

Fact `sqlite3-register_adapter`:

Register an *adapter* :term:`callable` to adapt the Python type *type*
   into an SQLite type.
   The adapter is called with a Python object of type *type* as its sole
   argument, and must return a value of a
   :ref:`type that SQLite natively understands <sqlite3-types>`.

Alternative `sqlite3-register_adapter`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14632, 14909)

Review decision / disagreements / resolution: **pending**

## sqlite3-register_converter

held_out / bz2+sqlite3 / paraphrase / draft

How does sqlite3.register_converter restore a named SQL type?

Expected answerable: True

Fact `sqlite3-register_converter`:

Register the *converter* :term:`callable` to convert SQLite objects of type
   *typename* into a Python object of a specific type.
   The converter is invoked for all SQLite values of type *typename*;
   it is passed a :class:`bytes` object and should return an object of the
   desired Python type.
   Consult the parameter *detect_types* of
   :func:`connect` for information regarding how type detection works.

Alternative `sqlite3-register_converter`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14969, 15385)

Review decision / disagreements / resolution: **pending**

## pathlib-PurePath

development / pathlib+shutil / exact_api / draft

When should PurePath be used instead of a concrete path?

Expected answerable: True

Fact `pathlib-PurePath`:

A generic class that represents the system's path flavour (instantiating
   it creates either a :class:`PurePosixPath` or a :class:`PureWindowsPath`)::

Alternative `pathlib-PurePath`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [3417, 3571)

Review decision / disagreements / resolution: **pending**

## pathlib-PurePosixPath

development / pathlib+shutil / paraphrase / draft

Which filesystem flavor does PurePosixPath represent?

Expected answerable: True

Fact `pathlib-PurePosixPath`:

A subclass of :class:`PurePath`, this path flavour represents non-Windows
   filesystem paths::

Alternative `pathlib-PurePosixPath`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [5614, 5712)

Review decision / disagreements / resolution: **pending**

## pathlib-PureWindowsPath

development / pathlib+shutil / exact_api / draft

Which filesystem flavor does PureWindowsPath represent?

Expected answerable: True

Fact `pathlib-PureWindowsPath`:

A subclass of :class:`PurePath`, this path flavour represents Windows
   filesystem paths, including `UNC paths`_::

Alternative `pathlib-PureWindowsPath`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [5894, 6012)

Review decision / disagreements / resolution: **pending**

## pathlib-Path

development / pathlib+shutil / paraphrase / draft

Which concrete path flavor is created by pathlib.Path?

Expected answerable: True

Fact `pathlib-Path`:

A subclass of :class:`PurePath`, this class represents concrete paths of
   the system's path flavour (instantiating it creates either a
   :class:`PosixPath` or a :class:`WindowsPath`)::

Alternative `pathlib-Path`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [23868, 24058)

Review decision / disagreements / resolution: **pending**

## shutil-copyfile

development / pathlib+shutil / exact_api / draft

Does shutil.copyfile copy file metadata?

Expected answerable: True

Fact `shutil-copyfile`:

Copy the contents (no metadata) of the file named *src* to a file named
   *dst* and return *dst* in the most efficient way possible.
   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings.

Alternative `shutil-copyfile`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [2297, 2533)

Review decision / disagreements / resolution: **pending**

## shutil-copy

development / pathlib+shutil / paraphrase / draft

What does shutil.copy preserve besides file contents?

Expected answerable: True

Fact `shutil-copy`:

Copies the file *src* to the file or directory *dst*.  *src* and *dst*
   should be :term:`path-like objects <path-like object>` or strings.  If
   *dst* specifies a directory, the file will be copied into *dst* using the
   base filename from *src*. If *dst* specifies a file that already exists,
   it will be replaced. Returns the path to the newly created file.

Alternative `shutil-copy`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [6873, 7241)

Review decision / disagreements / resolution: **pending**

## shutil-copy2

development / pathlib+shutil / exact_api / draft

How does shutil.copy2 differ from shutil.copy?

Expected answerable: True

Fact `shutil-copy2`:

Identical to :func:`~shutil.copy` except that :func:`copy2`
   also attempts to preserve file metadata.

Alternative `shutil-copy2`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [8260, 8366)

Review decision / disagreements / resolution: **pending**

## shutil-rmtree

development / pathlib+shutil / paraphrase / draft

What does shutil.rmtree remove?

Expected answerable: True

Fact `shutil-rmtree`:

Delete an entire directory tree; *path* must point to a directory (but not a
   symbolic link to a directory).  If *ignore_errors* is true, errors resulting
   from failed removals will be ignored; if false or omitted, such errors are
   handled by calling a handler specified by *onexc* or *onerror* or, if both
   are omitted, exceptions are propagated to the caller.

Alternative `shutil-rmtree`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [13263, 13635)

Review decision / disagreements / resolution: **pending**

## tempfile-TemporaryFile

held_out / tempfile+fnmatch / exact_api / draft

How is a tempfile.TemporaryFile cleaned up?

Expected answerable: True

Fact `tempfile-TemporaryFile`:

Return a :term:`file-like object` that can be used as a temporary storage area.
   The file is created securely, using the same rules as :func:`mkstemp`. It will be destroyed as soon
   as it is closed (including an implicit close when the object is garbage
   collected).  Under Unix, the directory entry for the file is either not created at all or is removed
   immediately after the file is created.  Other platforms do not support
   this; your code should not rely on a temporary file created using this
   function having or not having a visible name in the file system.

Alternative `tempfile-TemporaryFile`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [1445, 2025)

Review decision / disagreements / resolution: **pending**

## tempfile-NamedTemporaryFile

held_out / tempfile+fnmatch / paraphrase / draft

Does NamedTemporaryFile have a visible name in the filesystem?

Expected answerable: True

Fact `tempfile-NamedTemporaryFile`:

This function returns a file that is guaranteed to have a visible name in
     the file system.
   * To manage the named file, it extends the parameters of
     :func:`TemporaryFile` with *delete* and *delete_on_close* parameters that
     determine whether and how the named file should be automatically deleted.

Alternative `tempfile-NamedTemporaryFile`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [3627, 3940)

Review decision / disagreements / resolution: **pending**

## tempfile-TemporaryDirectory

held_out / tempfile+fnmatch / exact_api / draft

How is a temporary directory removed when used as a context manager?

Expected answerable: True

Fact `tempfile-TemporaryDirectory`:

This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.
   The resulting object can be used as a :term:`context manager` (see
   :ref:`tempfile-examples`).  On completion of the context or destruction
   of the temporary directory object, the newly created temporary directory
   and all its contents are removed from the filesystem.

Alternative `tempfile-TemporaryDirectory`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [8326, 8697)

Review decision / disagreements / resolution: **pending**

## tempfile-mkstemp

held_out / tempfile+fnmatch / paraphrase / draft

Who is responsible for deleting files created by mkstemp?

Expected answerable: True

Fact `tempfile-mkstemp`:

Creates a temporary file in the most secure manner possible.  There are
   no race conditions in the file's creation, assuming that the platform
   properly implements the :const:`os.O_EXCL` flag for :func:`os.open`.  The
   file is readable and writable only by the creating user ID.  If the
   platform uses permission bits to indicate whether a file is executable,
   the file is executable by no one.  The file descriptor is not inherited
   by child processes.

Alternative `tempfile-mkstemp`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [10319, 10787)

Review decision / disagreements / resolution: **pending**

## glob-glob

held_out / glob+argparse / exact_api / draft

What does glob.glob return for a pathname pattern?

Expected answerable: True

Fact `glob-glob`:

Return a possibly empty list of path names that match *pathname*, which must be
   a string containing a path specification. *pathname* can be either absolute
   (like :file:`/usr/src/Python-1.5/Makefile`) or relative (like
   :file:`../../Tools/\*/\*.gif`), and can contain shell-style wildcards. Broken
   symlinks are included in the results (as in the shell). Whether or not the
   results are sorted depends on the file system.  If a file that satisfies
   conditions is removed or added during the call of this function, whether
   a path name for that file will be included is unspecified.

Alternative `glob-glob`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [1601, 2200)

Review decision / disagreements / resolution: **pending**

## glob-iglob

held_out / glob+argparse / paraphrase / draft

Why use glob.iglob instead of glob.glob?

Expected answerable: True

Fact `glob-iglob`:

Return an :term:`iterator` which yields the same values as :func:`glob`
   without actually storing them all simultaneously.

Alternative `glob-iglob`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [3780, 3907)

Review decision / disagreements / resolution: **pending**

## glob-escape

held_out / glob+argparse / exact_api / draft

How can glob.escape treat wildcard characters literally?

Expected answerable: True

Fact `glob-escape`:

Escape all special characters (``'?'``, ``'*'`` and ``'['``).
   This is useful if you want to match an arbitrary literal string that may
   have special characters in it.  Special characters in drive/UNC
   sharepoints are not escaped, e.g. on Windows
   ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.

Alternative `glob-escape`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4460, 4793)

Review decision / disagreements / resolution: **pending**

## glob-translate

held_out / glob+argparse / paraphrase / draft

How does glob.translate turn a path pattern into a regular expression?

Expected answerable: True

Fact `glob-translate`:

Convert the given path specification to a regular expression for use with
   :func:`re.match`. The path specification can contain shell-style wildcards.

Alternative `glob-translate`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4910, 5065)

Review decision / disagreements / resolution: **pending**

## fnmatch-fnmatch

held_out / tempfile+fnmatch / exact_api / draft

How does fnmatch.fnmatch normalize case?

Expected answerable: True

Fact `fnmatch-fnmatch`:

Test whether the filename string *name* matches the pattern string *pat*,
   returning ``True`` or ``False``.  Both parameters are case-normalized
   using :func:`os.path.normcase`. :func:`fnmatchcase` can be used to perform a
   case-sensitive comparison, regardless of whether that's standard for the
   operating system.

Alternative `fnmatch-fnmatch`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [2392, 2718)

Review decision / disagreements / resolution: **pending**

## fnmatch-fnmatchcase

held_out / tempfile+fnmatch / paraphrase / draft

How can shell wildcard matching remain case-sensitive?

Expected answerable: True

Fact `fnmatch-fnmatchcase`:

Test whether the filename string *name* matches the pattern string *pat*,
   returning ``True`` or ``False``;
   the comparison is case-sensitive and does not apply :func:`os.path.normcase`.

Alternative `fnmatch-fnmatchcase`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3005, 3198)

Alternative `fnmatch-fnmatchcase-pdf-alternative`:
- `python314:fnmatch-pdf` revision `ac393dc047e2b294804c60022762465fcc45cad8a65ba3214dc76bab9143abdd` extracted-text characters [0, 185)

Review decision / disagreements / resolution: **pending**

## fnmatch-filter

held_out / tempfile+fnmatch / exact_api / draft

What does fnmatch.filter select from a list of names?

Expected answerable: True

Fact `fnmatch-filter`:

Construct a list from those elements of the :term:`iterable` of filename
   strings *names* that match the pattern string *pat*.
   It is the same as ``[n for n in names if fnmatch(n, pat)]``,
   but implemented more efficiently.

Alternative `fnmatch-filter`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3235, 3467)

Alternative `fnmatch-filter-pdf-alternative`:
- `python314:fnmatch-pdf` revision `ac393dc047e2b294804c60022762465fcc45cad8a65ba3214dc76bab9143abdd` extracted-text characters [185, 187)

Review decision / disagreements / resolution: **pending**

## fnmatch-translate

held_out / tempfile+fnmatch / paraphrase / draft

How does fnmatch.translate produce a regular expression?

Expected answerable: True

Fact `fnmatch-translate`:

Return the shell-style pattern *pat* converted to a regular expression for
   using with :func:`re.match`. The pattern is expected to be a :class:`str`.

Alternative `fnmatch-translate`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3812, 3967)

Review decision / disagreements / resolution: **pending**

## re-search

development / re+bisect / exact_api / draft

Where in a string does re.search look for a match?

Expected answerable: True

Fact `re-search`:

Scan through *string* looking for the first location where the regular expression
   *pattern* produces a match, and return a corresponding :class:`~re.Match`. Return
   ``None`` if no position in the string matches the pattern; note that this is
   different from finding a zero-length match at some point in the string.

Alternative `re-search`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [38378, 38702)

Review decision / disagreements / resolution: **pending**

## re-match

development / re+bisect / paraphrase / draft

Why can re.match miss a pattern occurring later in a string?

Expected answerable: True

Fact `re-match`:

If zero or more characters at the beginning of *string* match the regular
   expression *pattern*, return a corresponding :class:`~re.Match`.  Return
   ``None`` if the string does not match the pattern; note that this is
   different from a zero-length match.

Alternative `re-match`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [38929, 39192)

Review decision / disagreements / resolution: **pending**

## re-fullmatch

development / re+bisect / exact_api / draft

When does re.fullmatch succeed?

Expected answerable: True

Fact `re-fullmatch`:

If the whole *string* matches the regular expression *pattern*, return a
   corresponding :class:`~re.Match`.  Return ``None`` if the string does not match
   the pattern; note that this is different from a zero-length match.

Alternative `re-fullmatch`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [39697, 39925)

Review decision / disagreements / resolution: **pending**

## re-findall

development / re+bisect / paraphrase / draft

How are multiple matches returned by re.findall?

Expected answerable: True

Fact `re-findall`:

Return all non-overlapping matches of *pattern* in *string*, as a list of
   strings or tuples.  The *string* is scanned left-to-right, and matches
   are returned in the order found.  Empty matches are included in the result.

Alternative `re-findall`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [42384, 42613)

Review decision / disagreements / resolution: **pending**

## collections-Counter

held_out / collections+heapq / exact_api / draft

What does collections.Counter count?

Expected answerable: True

Fact `collections-Counter`:

A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
    It is a collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values.  Counts are allowed to be
    any integer value including zero or negative counts.  The :class:`Counter`
    class is similar to bags or multisets in other languages.

Alternative `collections-Counter`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [10146, 10524)

Review decision / disagreements / resolution: **pending**

## collections-deque

held_out / collections+heapq / paraphrase / draft

What is a deque optimized for?

Expected answerable: True

Fact `collections-deque`:

Returns a new deque object initialized left-to-right (using :meth:`append`) with
    data from *iterable*.  If *iterable* is not specified, the new deque is empty.

Alternative `collections-deque`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [18966, 19133)

Review decision / disagreements / resolution: **pending**

## collections-defaultdict

held_out / collections+heapq / exact_api / draft

What relationship does defaultdict have to the built-in dict class?

Expected answerable: True

Fact `collections-defaultdict`:

Return a new dictionary-like object.  :class:`defaultdict` is a subclass of the
    built-in :class:`dict` class.  It overrides one method and adds one writable
    instance variable.  The remaining functionality is the same as for the
    :class:`dict` class and is not documented here.

Alternative `collections-defaultdict`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [27750, 28041)

Review decision / disagreements / resolution: **pending**

## collections-namedtuple

held_out / collections+heapq / paraphrase / draft

What does namedtuple create?

Expected answerable: True

Fact `collections-namedtuple`:

Returns a new tuple subclass named *typename*.  The new subclass is used to
    create tuple-like objects that have fields accessible by attribute lookup as
    well as being indexable and iterable.  Instances of the subclass also have a
    helpful docstring (with *typename* and *field_names*) and a helpful
    :meth:`~object.__repr__` method which lists the tuple contents in a ``name=value``
    format.

Alternative `collections-namedtuple`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [32978, 33390)

Review decision / disagreements / resolution: **pending**

## heapq-heappush

held_out / collections+heapq / exact_api / draft

How does heapq.heappush maintain the heap?

Expected answerable: True

Fact `heapq-heappush`:

Push the value *item* onto the *heap*, maintaining the min-heap invariant.

Alternative `heapq-heappush`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2551, 2628)

Review decision / disagreements / resolution: **pending**

## heapq-heappop

held_out / collections+heapq / paraphrase / draft

Which element is returned by heapq.heappop?

Expected answerable: True

Fact `heapq-heappop`:

Pop and return the smallest item from the *heap*, maintaining the min-heap
   invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
   smallest item without popping it, use ``heap[0]``.

Alternative `heapq-heappop`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2660, 2872)

Review decision / disagreements / resolution: **pending**

## heapq-heapify

held_out / collections+heapq / exact_api / draft

How does heapq.heapify transform a list?

Expected answerable: True

Fact `heapq-heapify`:

Transform list *x* into a min-heap, in-place, in linear time.

Alternative `heapq-heapify`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [3144, 3208)

Review decision / disagreements / resolution: **pending**

## heapq-heappushpop

held_out / collections+heapq / paraphrase / draft

What does heapq.heappushpop do in one operation?

Expected answerable: True

Fact `heapq-heappushpop`:

Push *item* on the heap, then pop and return the smallest item from the
   *heap*.  The combined action runs more efficiently than :func:`heappush`
   followed by a separate call to :func:`heappop`.

Alternative `heapq-heappushpop`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2914, 3115)

Review decision / disagreements / resolution: **pending**

## bisect-bisect_left

development / re+bisect / exact_api / draft

Where does bisect_left insert relative to existing equal values?

Expected answerable: True

Fact `bisect-bisect_left`:

Locate the insertion point for *x* in *a* to maintain sorted order.
   The parameters *lo* and *hi* may be used to specify a subset of the list
   which should be considered; by default the entire list is used.  If *x* is
   already present in *a*, the insertion point will be before (to the left of)
   any existing entries.  The return value is suitable for use as the first
   parameter to ``list.insert()`` assuming that *a* is already sorted.

Alternative `bisect-bisect_left`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [1769, 2219)

Review decision / disagreements / resolution: **pending**

## bisect-bisect_right

development / re+bisect / paraphrase / draft

Where does bisect_right insert relative to existing equal values?

Expected answerable: True

Fact `bisect-bisect_right`:

Similar to :py:func:`~bisect.bisect_left`, but returns an insertion point which comes
   after (to the right of) any existing entries of *x* in *a*.

Alternative `bisect-bisect_right`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [2968, 3119)

Review decision / disagreements / resolution: **pending**

## bisect-insort_left

development / re+bisect / exact_api / draft

What sequence of operations does insort_left perform?

Expected answerable: True

Fact `bisect-insort_left`:

This function first runs :py:func:`~bisect.bisect_left` to locate an insertion point.
   Next, it runs the :meth:`~sequence.insert` method on *a* to insert *x* at the
   appropriate position to maintain sort order.

Alternative `bisect-insort_left`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [3527, 3741)

Review decision / disagreements / resolution: **pending**

## bisect-insort_right

development / re+bisect / paraphrase / draft

How does insort_right choose a position for equal elements?

Expected answerable: True

Fact `bisect-insort_right`:

Similar to :py:func:`~bisect.insort_left`, but inserting *x* in *a* after any existing
   entries of *x*.

Alternative `bisect-insort_right`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [4176, 4284)

Review decision / disagreements / resolution: **pending**

## statistics-mean

development / statistics+itertools / exact_api / draft

What average does statistics.mean calculate?

Expected answerable: True

Fact `statistics-mean`:

Return the sample arithmetic mean of *data* which can be a sequence or iterable.

Alternative `statistics-mean`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5039, 5122)

Review decision / disagreements / resolution: **pending**

## statistics-median

development / statistics+itertools / paraphrase / draft

How is statistics.median determined for an even number of values?

Expected answerable: True

Fact `statistics-median`:

Return the median (middle value) of numeric data, using the common "mean of
   middle two" method.  If *data* is empty, :exc:`StatisticsError` is raised.
   *data* can be a sequence or iterable.

Alternative `statistics-median`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [12598, 12795)

Review decision / disagreements / resolution: **pending**

## statistics-mode

development / statistics+itertools / exact_api / draft

What does statistics.mode return?

Expected answerable: True

Fact `statistics-mode`:

Return the single most common data point from discrete or nominal *data*.
   The mode (when it exists) is the most typical value and serves as a
   measure of central location.

Alternative `statistics-mode`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [16608, 16787)

Review decision / disagreements / resolution: **pending**

## statistics-stdev

development / statistics+itertools / paraphrase / draft

Which standard deviation is computed by statistics.stdev?

Expected answerable: True

Fact `statistics-stdev`:

Return the sample standard deviation (the square root of the sample
   variance).  See :func:`variance` for arguments and other details.

Alternative `statistics-stdev`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [20937, 21076)

Review decision / disagreements / resolution: **pending**

## decimal-Decimal

held_out / decimal+fractions / exact_api / draft

Which kinds of values can construct a Decimal?

Expected answerable: True

Fact `decimal-Decimal`:

Construct a new :class:`Decimal` object based from *value*.

Alternative `decimal-Decimal`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [12802, 12864)

Review decision / disagreements / resolution: **pending**

## decimal-getcontext

held_out / decimal+fractions / paraphrase / draft

What does decimal.getcontext return?

Expected answerable: True

Fact `decimal-getcontext`:

Return the current context for the active thread.

Alternative `decimal-getcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39165, 39217)

Review decision / disagreements / resolution: **pending**

## decimal-localcontext

held_out / decimal+fractions / exact_api / draft

How does decimal.localcontext isolate context changes?

Expected answerable: True

Fact `decimal-localcontext`:

Return a context manager that will set the current context for the active thread
   to a copy of *ctx* on entry to the with-statement and restore the previous context
   when exiting the with-statement. If no context is specified, a copy of the
   current context is used.  The *kwargs* argument is used to set the attributes
   of the new context.

Alternative `decimal-localcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39486, 39837)

Review decision / disagreements / resolution: **pending**

## decimal-setcontext

held_out / decimal+fractions / paraphrase / draft

How is the active decimal context replaced?

Expected answerable: True

Fact `decimal-setcontext`:

Set the current context for the active thread to *c*.

Alternative `decimal-setcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39252, 39308)

Review decision / disagreements / resolution: **pending**

## fractions-Fraction

held_out / decimal+fractions / exact_api / draft

Which numerator and denominator inputs can construct a Fraction?

Expected answerable: True

Fact `fractions-Fraction`:

The first version requires that *numerator* and *denominator* are instances
   of :class:`numbers.Rational` and returns a new :class:`Fraction` instance
   with value ``numerator/denominator``. If *denominator* is ``0``, it
   raises a :exc:`ZeroDivisionError`.

Alternative `fractions-Fraction`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [649, 913)

Review decision / disagreements / resolution: **pending**

## fractions-as_integer_ratio

held_out / decimal+fractions / paraphrase / draft

How does Fraction.as_integer_ratio represent a rational number?

Expected answerable: True

Fact `fractions-as_integer_ratio`:

Return a tuple of two integers, whose ratio is equal
      to the original Fraction.  The ratio is in lowest terms
      and has a positive denominator.

Alternative `fractions-as_integer_ratio`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [4809, 4967)

Review decision / disagreements / resolution: **pending**

## fractions-limit_denominator

held_out / decimal+fractions / exact_api / draft

What does Fraction.limit_denominator approximate?

Expected answerable: True

Fact `fractions-limit_denominator`:

Finds and returns the closest :class:`Fraction` to ``self`` that has
      denominator at most max_denominator.  This method is useful for finding
      rational approximations to a given floating-point number:

Alternative `fractions-limit_denominator`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [6218, 6434)

Review decision / disagreements / resolution: **pending**

## fractions-from_float

held_out / decimal+fractions / paraphrase / draft

How does Fraction.from_float interpret a float value?

Expected answerable: True

Fact `fractions-from_float`:

Alternative constructor which only accepts instances of
      :class:`float` or :class:`numbers.Integral`. Beware that
      ``Fraction.from_float(0.3)`` is not the same value as ``Fraction(3, 10)``.

Alternative `fractions-from_float`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [5146, 5351)

Review decision / disagreements / resolution: **pending**

## itertools-count

development / statistics+itertools / exact_api / draft

What values does itertools.count generate?

Expected answerable: True

Fact `itertools-count`:

Make an iterator that returns evenly spaced values beginning with
   *start*. Can be used with :func:`map` to generate consecutive data
   points or with :func:`zip` to add sequence numbers.  Roughly
   equivalent to::

Alternative `itertools-count`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15157, 15378)

Review decision / disagreements / resolution: **pending**

## itertools-cycle

development / statistics+itertools / paraphrase / draft

How does itertools.cycle reuse its input?

Expected answerable: True

Fact `itertools-cycle`:

Make an iterator returning elements from the *iterable* and saving a
   copy of each.  When the iterable is exhausted, return elements from
   the saved copy.  Repeats indefinitely.  Roughly equivalent to::

Alternative `itertools-cycle`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15896, 16105)

Review decision / disagreements / resolution: **pending**

## itertools-repeat

development / statistics+itertools / exact_api / draft

How does itertools.repeat control the number of repetitions?

Expected answerable: True

Fact `itertools-repeat`:

Make an iterator that returns *object* over and over again. Runs indefinitely
   unless the *times* argument is specified.

Alternative `itertools-repeat`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [26001, 26126)

Review decision / disagreements / resolution: **pending**

## itertools-chain

development / statistics+itertools / paraphrase / draft

How does itertools.chain combine iterables?

Expected answerable: True

Fact `itertools-chain`:

Make an iterator that returns elements from the first iterable until
   it is exhausted, then proceeds to the next iterable, until all of the
   iterables are exhausted.  This combines multiple data sources into a
   single iterator.  Roughly equivalent to::

Alternative `itertools-chain`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [10866, 11127)

Review decision / disagreements / resolution: **pending**

## argparse-ArgumentParser

held_out / glob+argparse / exact_api / draft

What is the role of argparse.ArgumentParser?

Expected answerable: True

Fact `argparse-ArgumentParser`:

Create a new :class:`ArgumentParser` object. All parameters should be passed
   as keyword arguments. Each parameter has its own more detailed description
   below, but in short they are:

Alternative `argparse-ArgumentParser`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [3499, 3689)

Review decision / disagreements / resolution: **pending**

## argparse-parse_args

held_out / glob+argparse / paraphrase / draft

What is returned after ArgumentParser.parse_args interprets the command line?

Expected answerable: True

Fact `argparse-parse_args`:

Convert argument strings to objects and assign them as attributes of the
   namespace.  Return the populated namespace.

Alternative `argparse-parse_args`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [55695, 55817)

Review decision / disagreements / resolution: **pending**

## argparse-add_subparsers

held_out / glob+argparse / exact_api / draft

How does ArgumentParser.add_subparsers support subcommands?

Expected answerable: True

Fact `argparse-add_subparsers`:

Many programs split up their functionality into a number of subcommands,
   for example, the ``svn`` program can invoke subcommands like ``svn
   checkout``, ``svn update``, and ``svn commit``.  Splitting up functionality
   this way can be a particularly good idea when a program performs several
   different functions which require different kinds of command-line arguments.
   :class:`ArgumentParser` supports the creation of such subcommands with the
   :meth:`!add_subparsers` method.  The :meth:`!add_subparsers` method is normally
   called with no arguments and returns a special action object.  This object
   has a single method, :meth:`~_SubParsersAction.add_parser`, which takes a
   command name and any :class:`!ArgumentParser` constructor arguments, and
   returns an :class:`!ArgumentParser` object that can be modified as usual.

Alternative `argparse-add_subparsers`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [63853, 64702)

Review decision / disagreements / resolution: **pending**

## argparse-parse_known_args

held_out / glob+argparse / paraphrase / draft

How does parse_known_args handle unrecognized command-line arguments?

Expected answerable: True

Fact `argparse-parse_known_args`:

Sometimes a script only needs to handle a specific set of command-line
   arguments, leaving any unrecognized arguments for another script or program.
   In these cases, the :meth:`~ArgumentParser.parse_known_args` method can be
   useful.

Alternative `argparse-parse_known_args`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [82128, 82370)

Review decision / disagreements / resolution: **pending**

## compound-json-dumps-pickle-dumps

development / json+pickle / multi_source / draft

Which json function returns a JSON string rather than writing to a stream; and what type of result does pickle.dumps return?

Expected answerable: True

Fact `json-dumps`:

Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
   table <py-to-json-table>`.  The arguments have the same meaning as in
   :func:`dump`.

Alternative `json-dumps`:
- `python314:json` revision `8d9226d893ae02caa7c326bbe4d56283f86f1062993665f473f04fb10065c45b` extracted-text characters [8692, 8861)

Fact `pickle-dumps`:

Return the pickled representation of the object *obj* as a :class:`bytes` object,
   instead of writing it to a file.

Alternative `pickle-dumps`:
- `python314:pickle` revision `b4b5830a34b7d6286b6b7814a632d6a50175fef4f3ac7bbf443e7ea2b11c0aea` extracted-text characters [9787, 9907)

Review decision / disagreements / resolution: **pending**

## compound-csv-reader-gzip-decompress

development / csv+gzip / multi_source / draft

What does csv.reader produce from an iterable of lines; and can gzip.decompress handle concatenated gzip members?

Expected answerable: True

Fact `csv-reader`:

Return a :ref:`reader object <reader-objects>` that will process
   lines from the given *csvfile*.  A csvfile must be an iterable of
   strings, each in the reader's defined csv format.
   A csvfile is most commonly a file-like object or list.
   If *csvfile* is a file object,
   it should be opened with ``newline=''``. [1]_  An optional
   *dialect* parameter can be given which is used to define a set of parameters
   specific to a particular CSV dialect.  It may be an instance of a subclass of
   the :class:`Dialect` class or one of the strings returned by the
   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments
   can be given to override individual formatting parameters in the current
   dialect.  For full details about the dialect and formatting parameters, see
   section :ref:`csv-fmt-params`.

Alternative `csv-reader`:
- `python314:csv` revision `9e0b648823bbffc3d6112de905d5fcbb7ebe2d29a4a9e8fd0e16737b6e0d3359` extracted-text characters [2074, 2920)

Fact `gzip-decompress`:

Decompress the *data*, returning a :class:`bytes` object containing the
   uncompressed data. This function is capable of decompressing multi-member
   gzip data (multiple gzip blocks concatenated together). When the data is
   certain to contain only one member the :func:`zlib.decompress` function with
   *wbits* set to 31 is faster.

Alternative `gzip-decompress`:
- `python314:gzip` revision `925ded6f8215e1dbea90bfda9a7093724a657ef01d6b3407abc645bfa8e90a55` extracted-text characters [8917, 9256)

Review decision / disagreements / resolution: **pending**

## compound-lzma-compress-zlib-compress

development / lzma+zlib / multi_source / draft

How does lzma.compress return compressed data; and what does zlib.compress return for its data argument?

Expected answerable: True

Fact `lzma-compress`:

Compress *data* (a :class:`bytes` object), returning the compressed data as a
   :class:`bytes` object.

Alternative `lzma-compress`:
- `python314:lzma` revision `fd0001a09c76ef3f12ed3f3f98c093b7e42027ebd4e471e8cc1f47ae7d5a255d` extracted-text characters [12684, 12790)

Fact `zlib-compress`:

Compresses the bytes in *data*, returning a bytes object containing compressed data.
   *level* is an integer from ``0`` to ``9`` or ``-1`` controlling the level of compression;
   ``1`` (Z_BEST_SPEED) is fastest and produces the least compression, ``9`` (Z_BEST_COMPRESSION)
   is slowest and produces the most.  ``0`` (Z_NO_COMPRESSION) is no compression.
   The default value is ``-1`` (Z_DEFAULT_COMPRESSION).  Z_DEFAULT_COMPRESSION represents a default
   compromise between speed and compression (currently equivalent to level 6).

Alternative `zlib-compress`:
- `python314:zlib` revision `1a6f1a2154eb1702e0ca89951ded99e9e208cb5ff0bb3a75453a157535c4e2a7` extracted-text characters [1979, 2518)

Review decision / disagreements / resolution: **pending**

## compound-pathlib-Path-shutil-copy2

development / pathlib+shutil / multi_source / draft

Which concrete path flavor is created by pathlib.Path; and how does shutil.copy2 differ from shutil.copy?

Expected answerable: True

Fact `pathlib-Path`:

A subclass of :class:`PurePath`, this class represents concrete paths of
   the system's path flavour (instantiating it creates either a
   :class:`PosixPath` or a :class:`WindowsPath`)::

Alternative `pathlib-Path`:
- `python314:pathlib` revision `9b243c8ba9bf1d6af953550d228c4df4daec0af5584659d026111a4167a2534b` extracted-text characters [23868, 24058)

Fact `shutil-copy2`:

Identical to :func:`~shutil.copy` except that :func:`copy2`
   also attempts to preserve file metadata.

Alternative `shutil-copy2`:
- `python314:shutil` revision `1e6afb6fc657c5ec58c36f7dffd38bba8111a0a619689739c99ad946b5ae07db` extracted-text characters [8260, 8366)

Review decision / disagreements / resolution: **pending**

## compound-re-fullmatch-bisect-bisect_left

development / re+bisect / multi_source / draft

When does re.fullmatch succeed; and where does bisect_left insert relative to existing equal values?

Expected answerable: True

Fact `re-fullmatch`:

If the whole *string* matches the regular expression *pattern*, return a
   corresponding :class:`~re.Match`.  Return ``None`` if the string does not match
   the pattern; note that this is different from a zero-length match.

Alternative `re-fullmatch`:
- `python314:re` revision `c7e0b2edf1b660d4690445f3ba41ddb4601df4dbaddcb999bc8df1e12bd507e0` extracted-text characters [39697, 39925)

Fact `bisect-bisect_left`:

Locate the insertion point for *x* in *a* to maintain sorted order.
   The parameters *lo* and *hi* may be used to specify a subset of the list
   which should be considered; by default the entire list is used.  If *x* is
   already present in *a*, the insertion point will be before (to the left of)
   any existing entries.  The return value is suitable for use as the first
   parameter to ``list.insert()`` assuming that *a* is already sorted.

Alternative `bisect-bisect_left`:
- `python314:bisect` revision `5fec029c9499806cabf8becb602e6b37ed9f28017b46f0330a11695b51f7ec37` extracted-text characters [1769, 2219)

Review decision / disagreements / resolution: **pending**

## compound-statistics-mean-itertools-count

development / statistics+itertools / multi_source / draft

What average does statistics.mean calculate; and what values does itertools.count generate?

Expected answerable: True

Fact `statistics-mean`:

Return the sample arithmetic mean of *data* which can be a sequence or iterable.

Alternative `statistics-mean`:
- `python314:statistics` revision `97a7ce318597d6cb9a7f8bfc1f123cd70077249bef13e21e58e1334a72902bbb` extracted-text characters [5039, 5122)

Fact `itertools-count`:

Make an iterator that returns evenly spaced values beginning with
   *start*. Can be used with :func:`map` to generate consecutive data
   points or with :func:`zip` to add sequence numbers.  Roughly
   equivalent to::

Alternative `itertools-count`:
- `python314:itertools` revision `69582481938d49183664bd49769b336aa138f7ee8790a6a6089c99b229d62902` extracted-text characters [15157, 15378)

Review decision / disagreements / resolution: **pending**

## compound-base64-urlsafe_b64encode-hashlib-hexdigest

held_out / base64+hashlib / multi_source / draft

Which characters does URL-safe Base64 substitute; and how does hash.hexdigest differ from a byte digest?

Expected answerable: True

Fact `base64-urlsafe_b64encode`:

Encode :term:`bytes-like object` *s* using the
   URL- and filesystem-safe alphabet, which
   substitutes ``-`` instead of ``+`` and ``_`` instead of ``/`` in the
   standard Base64 alphabet, and return the encoded :class:`bytes`.  The result
   can still contain ``=``.

Alternative `base64-urlsafe_b64encode`:
- `python314:base64` revision `dc42b6316121ae500f71b4c25326ce9929dd4e7a34e05151c762deb44524bfa7` extracted-text characters [3909, 4182)

Fact `hashlib-hexdigest`:

Like :meth:`digest` except the digest is returned as a string object of
   double length, containing only hexadecimal digits.  This may be used to
   exchange the value safely in email or other non-binary environments.

Alternative `hashlib-hexdigest`:
- `python314:hashlib` revision `5a530687bc828b8b60dd6f21b2bae215c4bd6917d386c610b55dd7b95de3f9af` extracted-text characters [7677, 7898)

Review decision / disagreements / resolution: **pending**

## compound-bz2-BZ2Compressor-sqlite3-register_adapter

held_out / bz2+sqlite3 / multi_source / draft

What is the purpose of BZ2Compressor; and how does sqlite3.register_adapter convert a Python type?

Expected answerable: True

Fact `bz2-BZ2Compressor`:

Create a new compressor object. This object may be used to compress data
   incrementally. For one-shot compression, use the :func:`compress` function
   instead.

Alternative `bz2-BZ2Compressor`:
- `python314:bz2` revision `bf31bfad910f4dc338a286174db692d2e9ff1403022287f945cacf6e73634348` extracted-text characters [6530, 6695)

Fact `sqlite3-register_adapter`:

Register an *adapter* :term:`callable` to adapt the Python type *type*
   into an SQLite type.
   The adapter is called with a Python object of type *type* as its sole
   argument, and must return a value of a
   :ref:`type that SQLite natively understands <sqlite3-types>`.

Alternative `sqlite3-register_adapter`:
- `python314:sqlite3` revision `d16dc0094b557effa0ae52618da0f61f0cb50bf05ce21942f3a9b2e70af40163` extracted-text characters [14632, 14909)

Review decision / disagreements / resolution: **pending**

## compound-tempfile-mkstemp-fnmatch-fnmatchcase

held_out / tempfile+fnmatch / multi_source / draft

Who is responsible for deleting files created by mkstemp; and how can shell wildcard matching remain case-sensitive?

Expected answerable: True

Fact `tempfile-mkstemp`:

Creates a temporary file in the most secure manner possible.  There are
   no race conditions in the file's creation, assuming that the platform
   properly implements the :const:`os.O_EXCL` flag for :func:`os.open`.  The
   file is readable and writable only by the creating user ID.  If the
   platform uses permission bits to indicate whether a file is executable,
   the file is executable by no one.  The file descriptor is not inherited
   by child processes.

Alternative `tempfile-mkstemp`:
- `python314:tempfile` revision `487aeabf01be281fd1e2534b326c33cca4d9fab4db1c04d32e58439c9f6346bc` extracted-text characters [10319, 10787)

Fact `fnmatch-fnmatchcase`:

Test whether the filename string *name* matches the pattern string *pat*,
   returning ``True`` or ``False``;
   the comparison is case-sensitive and does not apply :func:`os.path.normcase`.

Alternative `fnmatch-fnmatchcase`:
- `python314:fnmatch` revision `ef43e86ccd5745a41dba7f40537fd6c4ce8c2a528fa99324728ef4f44e145b71` extracted-text characters [3005, 3198)

Review decision / disagreements / resolution: **pending**

## compound-collections-Counter-heapq-heappop

held_out / collections+heapq / multi_source / draft

What does collections.Counter count; and which element is returned by heapq.heappop?

Expected answerable: True

Fact `collections-Counter`:

A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
    It is a collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values.  Counts are allowed to be
    any integer value including zero or negative counts.  The :class:`Counter`
    class is similar to bags or multisets in other languages.

Alternative `collections-Counter`:
- `python314:collections` revision `bc9fc65ad959f756ad0a5ba72ab0f834deb201c3e8ea19e1a206f9bd4d05eb10` extracted-text characters [10146, 10524)

Fact `heapq-heappop`:

Pop and return the smallest item from the *heap*, maintaining the min-heap
   invariant.  If the heap is empty, :exc:`IndexError` is raised.  To access the
   smallest item without popping it, use ``heap[0]``.

Alternative `heapq-heappop`:
- `python314:heapq` revision `676347c86a675a3f9071e92276e823c496e763176dccd563a5e051dd09044225` extracted-text characters [2660, 2872)

Review decision / disagreements / resolution: **pending**

## compound-decimal-localcontext-fractions-limit_denominator

held_out / decimal+fractions / multi_source / draft

How does decimal.localcontext isolate context changes; and what does Fraction.limit_denominator approximate?

Expected answerable: True

Fact `decimal-localcontext`:

Return a context manager that will set the current context for the active thread
   to a copy of *ctx* on entry to the with-statement and restore the previous context
   when exiting the with-statement. If no context is specified, a copy of the
   current context is used.  The *kwargs* argument is used to set the attributes
   of the new context.

Alternative `decimal-localcontext`:
- `python314:decimal` revision `196268ea1cacb789e58cbe9c4f5168e555142042c1fb2c8a18f5b705e97b3e65` extracted-text characters [39486, 39837)

Fact `fractions-limit_denominator`:

Finds and returns the closest :class:`Fraction` to ``self`` that has
      denominator at most max_denominator.  This method is useful for finding
      rational approximations to a given floating-point number:

Alternative `fractions-limit_denominator`:
- `python314:fractions` revision `5703ddbab6122520e383cfb4374fc0b35ee61337ba989db9a2bd059a8383aca4` extracted-text characters [6218, 6434)

Review decision / disagreements / resolution: **pending**

## compound-glob-escape-argparse-parse_known_args

held_out / glob+argparse / multi_source / draft

How can glob.escape treat wildcard characters literally; and how does parse_known_args handle unrecognized command-line arguments?

Expected answerable: True

Fact `glob-escape`:

Escape all special characters (``'?'``, ``'*'`` and ``'['``).
   This is useful if you want to match an arbitrary literal string that may
   have special characters in it.  Special characters in drive/UNC
   sharepoints are not escaped, e.g. on Windows
   ``escape('//?/c:/Quo vadis?.txt')`` returns ``'//?/c:/Quo vadis[?].txt'``.

Alternative `glob-escape`:
- `python314:glob` revision `6c29d54b0a5d497f67a55e9204156d6a3fe7c302d9c4239788e2bf1c24504aa1` extracted-text characters [4460, 4793)

Fact `argparse-parse_known_args`:

Sometimes a script only needs to handle a specific set of command-line
   arguments, leaving any unrecognized arguments for another script or program.
   In these cases, the :meth:`~ArgumentParser.parse_known_args` method can be
   useful.

Alternative `argparse-parse_known_args`:
- `python314:argparse` revision `46c9dc41aa479d4f068b644149ca4cb12c4076ef25ddd2e547e50becb611c40a` extracted-text characters [82128, 82370)

Review decision / disagreements / resolution: **pending**

## unsupported-1

development / json+pickle / unsupported / draft

What is the internal Project Juniper API key rotation schedule?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-2

development / csv+gzip / unsupported / draft

Who owns the Acme payroll CSV export in our team?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-3

development / csv+gzip / unsupported / draft

What gzip compression level does our private backup service mandate?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-4

development / pathlib+shutil / unsupported / draft

Which directory contains our private workbench production credentials?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-5

development / statistics+itertools / unsupported / draft

What was the p95 latency of our service yesterday?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-6

development / re+bisect / unsupported / draft

Which regex did our team approve in ticket INTERNAL-928?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-7

held_out / base64+hashlib / unsupported / draft

What is our organization's private signing key encoded in Base64?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-8

held_out / bz2+sqlite3 / unsupported / draft

What is the password for our private reporting database?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-9

held_out / tempfile+fnmatch / unsupported / draft

Which filenames did our latest private deployment remove?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-10

held_out / collections+heapq / unsupported / draft

What heap size limit did our internal capacity review approve?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-11

held_out / decimal+fractions / unsupported / draft

Who approved our company's accounting rounding policy?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## unsupported-12

held_out / glob+argparse / unsupported / draft

Which command deployed our private application last Friday?

Expected answerable: False

Review decision / disagreements / resolution: **pending**

## stress-revision

development / juniper-stress / revision / draft

Under revision 2, how many retries are permitted for JN-481?

Expected answerable: True

Fact `revision`:

JN-481 now allows five retries before operator escalation.

Alternative `revision`:
- `stress:retry-new.md` revision `f0cfe05b61ca05abbfddbbfed34ead46b7033daa152020d39ea86ccecd63f2d1` extracted-text characters [68, 126)

Alternative `revision-alternative`:
- `stress:retry-copy.md` revision `d4021474303e3649238d0f23ea296cc916568be7351cbae87b600d84a9527311` extracted-text characters [41, 99)

Review decision / disagreements / resolution: **pending**

## stress-old-revision

development / juniper-stress / revision / draft

Under revision 1, how many retries were permitted for JN-481?

Expected answerable: True

Fact `old-revision`:

Revision 1 allows two retries for JN-481 before operator escalation.

Alternative `old-revision`:
- `stress:retry-old.md` revision `5bd58e8c336e10d2c19aa03ef5efe7fd6ad88aad6eb4d4052d7e0b823cbe652e` extracted-text characters [36, 104)

Review decision / disagreements / resolution: **pending**

## stress-distractor

development / juniper-stress / hard_distractor / draft

How many retries are permitted for JN-482, the other subsystem?

Expected answerable: True

Fact `distractor`:

JN-482 allows nine retries.

Alternative `distractor`:
- `stress:retry-distractor.md` revision `fe8a1ce83a0731a8746a224b224028ecb420994f29fcce7920c4cebdccb72435` extracted-text characters [41, 68)

Review decision / disagreements / resolution: **pending**

## pdf-two-page

held_out / tempfile+fnmatch / multi_page / draft

In the fnmatch handout, how do case-sensitive matching and filtering a list of filenames work?

Expected answerable: True

Fact `pdf-case`:

Test whether the filename string *name* matches the pattern string *pat*,
   returning ``True`` or ``False``;
   the comparison is case-sensitive and does not apply :func:`os.path.normcase`.

Alternative `fnmatch-fnmatchcase-pdf-alternative`:
- `python314:fnmatch-pdf` revision `ac393dc047e2b294804c60022762465fcc45cad8a65ba3214dc76bab9143abdd` extracted-text characters [0, 185)

Fact `pdf-filter`:

Construct a list from those elements of the :term:`iterable` of filename
   strings *names* that match the pattern string *pat*.
   It is the same as ``[n for n in names if fnmatch(n, pat)]``,
   but implemented more efficiently.

Alternative `fnmatch-filter-pdf-alternative`:
- `python314:fnmatch-pdf` revision `ac393dc047e2b294804c60022762465fcc45cad8a65ba3214dc76bab9143abdd` extracted-text characters [185, 187)

Review decision / disagreements / resolution: **pending**
