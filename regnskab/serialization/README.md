Regnskab serialization
======================

Run `dump.py` to output a JSON dump of the database to stdout.
Run `load.py` to read a JSON dump on stdin and save it to the database.

The Django models are described in a tree structure in `models.py`
in the `regnskab/serialization` directory. Dumping and loading data
requires a traversal of the defined tree structure.

* The `dump()` method on the classes in `models.py`
  is implemented in the base class `Data` in `base.py`.
* `RegnskabData().dump()` in `models.py` returns a single dict
  containing all interesting database data.
* `dump.py` simply runs `json.dump` on this dump.
* `load.py` calls `RegnskabData().load()` on the dump
  to get a list of callback objects (defined in `callback.py`).
* The `load()` method on the classes in `models.py`
  is implemented in `Data`.
