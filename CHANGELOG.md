# Development version

* Add optional dependency on *fontra* for cases where *fontconfig* is not available by providing the *fontra* extra. (Many thanks to *chrismaster* for the initial implementation/recommendation and *NCBM* as the maintainer of *fontra* for the quick enhancement of adding the missing bits for better *fontconfig* compatibility.)

# Version 0.3.0 - 2024-08-19

* Add API for printing images.
* Migrate to `pyproject.toml`.
* Update bundled Bootstrap to version 5.3.3 and Bootstrap Icons to version 1.11.3.

# Version 0.2.1 - 2024-03-16

* Fix printing of umlauts and special characters which would previously fail due to *bottle* oddities.

# Version 0.2.0 - 2023-11-23

* Fix undefined variables introduced due to the migration.
* Add tests.
* Add type hints, including *mypy*.
* Ignore the annoying `brother_ql.devicedependent` message which only has been fixed in Git, but not on PyPI.
* Patch *brother_ql* itself to ensure compatibility with `Pillow>=10`.
* Avoid defaulting to high quality output for now, as there is no proper implementation for it yet and this would raise errors for die cut labels and lead to downscaling followed by upscaling for endless labels.

# Version 0.1.0 - 2023-08-13

* First packaged version.
