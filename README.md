## brother\_ql\_web

This is a web service to print labels on Brother QL label printers. While it is primarily focused on the API/GUI part, the corresponding functionality is provided as a library as well.

You need a considerably recent Python 3 version for this software to work.

![Screenshot](./brother_ql_web/static/images/screenshots/Label-Designer_Desktop.png)

The web interface is [responsive](https://en.wikipedia.org/wiki/Responsive_web_design).
There is also a screenshot showing [how it looks on a smartphone](./static/images/screenshots/Label-Designer_Phone.png)

### Installation

The easiest way to use this package is to install it from PyPI:

    pip install brother_ql_web

Alternatively, you can use brother_ql_web without installing it, straight out of an unpacked source tarball or a VCS checkout.

It is also possible to install it from source for the current interpreter with:

    pip install .


In addition to the Python package requirements itself, `fontconfig` should be installed on your system. It is used to identify and inspect fonts on your machine. This package is pre-installed on many Linux distributions. If you are using a Mac, you might want to use [Homebrew](https://brew.sh) to install `fontconfig` using [`brew install fontconfig`](https://formulae.brew.sh/formula/fontconfig).

If you are not able to install or use `fontconfig` for some reasons, `fontra` is available as a fallback. You can install it using the `fontra` extra.

### Configuration file

Grab a copy of the [example configuration file](https://github.com/FriedrichFroebel/brother_ql_web/blob/master/config.example.json) and adjust it to your needs. You can store this file on your device wherever you want - just make sure to remember the full path as you will have to pass it to the CLI.

Some special notes about the values:

* Setting the log level to *DEBUG* will enable the debug mode of *bottle* as well. Additionally, this avoids sending the commands to the printer itself. You most likely do not want to use the *DEBUG* level unless you know what you are doing.

### Startup

To start the server, either run `brother_ql_web` (only works if installed) or `python -m brother_ql_web`. You will always have to pass the path to your configuration file to use.

The most basic call will look like this:

    python -m brother_ql_web --configuration $HOME/printers/brother_ql_web/configuration_dev.json

Additional parameters might be passed and will overwrite the values configured in your configuration file. Please refer to the `--help` flag to learn more about the possible flags you might pass.

#### Running with Docker compose

To start the server with Docker compose, create your configuration file `config.json` in the repository root, then run `docker compose up`.

### Usage

Once it is running, access the web interface by opening the page with your browser.

If you run it on your local machine, go to <http://localhost:8013> (You can change the default port 8013 using the `--port` argument). You will then be forwarded by default to the interactive web GUI located at `/labeldesigner`.

All in all, the web server offers:

* a web GUI allowing you to print your labels at `/labeldesigner`,
* an API at `/api/print/text?text=Your_Text&font_size=100&font_family=Minion%20Pro%20(%20Semibold%20)`
  to print a label containing 'Your Text' with the specified font properties.
* an API at `/api/print/image` to print a label image passed through the `image` file value.

### About this fork

This repository contains my personal fork of the original repository.

At the moment, there is no real activity in the upstream project, with the last change happening in January 2020. In the meantime, some dependencies got outdated and *Pillow* deprecated and dropped some methods which break the whole application.

Additionally, I think that it makes more sense to let everyone install this package from PyPI and pass a configuration file parameter to it for customization instead of basically hardcoding the configuration file path to `config.json` in the current application directory.

At the moment there are no plans to submit any pull request to the upstream repository.

#### Differences from upstream

  * Package requires Python ≥ 3.9.
  * Migrate to a package-based structure.
  * Ensure compatibility with latest dependency versions.
  * Upgrade Bootstrap and drop jQuery as Bootstrap does not rely on it anymore.
  * Conform to PEP 8 coding style.
  * Add some more printing options, like the number of labels to print for a session.
  * Add support for printing images directly.
  * Provide fallback for `fontconfig`.

### License

This software is published under the terms of the GPLv3, see the LICENSE file in the repository.

Parts of this package are redistributed software products from third-parties. They are subject to different licenses:

* [Bootstrap](https://github.com/twbs/bootstrap) v5.3.3, MIT License
* [Bootstrap Icons](https://github.com/twbs/icons) v1.11.3, MIT License
  * The CSS files received some minor modification to allow the font files to be loaded from the parent directory.
