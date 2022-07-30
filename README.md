# PagerDuty Utils

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/pagerduty-utils/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/pagerduty-utils/main)
[![Python package](https://github.com/Preocts/pagerduty-utils/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/pagerduty-utils/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/Preocts/pagerduty-utils/branch/main/graph/badge.svg?token=ABlYTJMwLN)](https://codecov.io/gh/Preocts/pagerduty-utils)

A growing collection of small CLI scripts I've written for managing a PagerDuty
instance.

## Requirements

- [Python](https://python.org) >= 3.8
- [httpx](https://pypi.org/project/httpx/)
- [secretbox](https://pypi.org/project/secretbox/)

---

Install scripts: Replace `@X.X.X` with the release number desired or exclude to
pull `main` branch.

```bash
pip install git+https://github.com/Preocts/pagerduty-utils@X.X.X
```

---

## Command line scripts:

All scripts will require a PagerDuty API v2 token. A script that needs write
access will call this requirement out, otherwise read-only is acceptable. The
token can be provided at the command line with the `--token` flag, in a `.env`
file under `PAGERDUTY_TOKEN`, or in the environ under the same key.

Some scripts, mainly read/write, will require the login email of a user in the
instance. These will be called out and can be provided with the `--email` flag,
in an `.env` file under `PAGERDUTY_EMAIL`, or in the environ under the same
name.

All scripts accept the `--logging-level` flag which defaults to `INFO`.

---

## Tools / Reports

### Coverage Gap Report

Identify schedules that are lacking 100% coverage.

```shell
usage: coverage-gap-report [-h] [--logging-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--token TOKEN] [--email EMAIL]

Pagerduty command line utilities.

optional arguments:
  -h, --help            show this help message and exit
  --logging-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: $LOGGING_LEVEL | INFO)
  --token TOKEN         PagerDuty API Token (default: $PAGERDUTY_TOKEN)
  --email EMAIL         PagerDuty Email (default: $PAGERDUTY_EMAIL)

See: https://github.com/Preocts/pagerduty-utils
```

Outputs:

| filename                          | contents                                       |
| --------------------------------- | ---------------------------------------------- |
| schedule_gap_reportYYYY-MM-DD.csv | All schedules names, url links, and coverage % |

---

# Local developer installation

It is **strongly** recommended to use a virtual environment
([`venv`](https://docs.python.org/3/library/venv.html)) when working with python
projects. Leveraging a `venv` will ensure the installed dependency files will
not impact other python projects or any system dependencies.

The following steps outline how to install this repo for local development. See
the [CONTRIBUTING.md](CONTRIBUTING.md) file in the repo root for information on
contributing to the repo.

**Windows users**: Depending on your python install you will use `py` in place
of `python` to create the `venv`.

**Linux/Mac users**: Replace `python`, if needed, with the appropriate call to
the desired version while creating the `venv`. (e.g. `python3` or `python3.8`)

**All users**: Once inside an active `venv` all systems should allow the use of
`python` for command line instructions. This will ensure you are using the
`venv`'s python and not the system level python.

---

## Installation steps

Clone this repo and enter root directory of repo:

```console
$ git clone https://github.com/Preocts/paderduty-utils
$ cd pagerduty-utils
```

Create the `venv`:

```console
$ python -m venv venv
```

Activate the `venv`:

```console
# Linux/Mac
$ . venv/bin/activate

# Windows
$ venv\Scripts\activate
```

The command prompt should now have a `(venv)` prefix on it. `python` will now
call the version of the interpreter used to create the `venv`

Install editable library and development requirements:

```console
# Update pip and tools
$ python -m pip install --upgrade pip

# Install editable version of library
$ python -m pip install --editable .[dev]
```

Install pre-commit [(see below for details)](#pre-commit):

```console
$ pre-commit install
```

---

## Misc Steps

Run pre-commit on all files:

```console
$ pre-commit run --all-files
```

Run tests:

```console
$ tox [-r] [-e py3x]
```

Build dist:

```console
$ python -m pip install --upgrade build

$ python -m build
```

To deactivate (exit) the `venv`:

```console
$ deactivate
```
---

## Note on flake8:

`flake8` is included in the `requirements-dev.txt` of the project. However it
disagrees with `black`, the formatter of choice, on max-line-length and two
general linting errors. `.pre-commit-config.yaml` is already configured to
ignore these. `flake8` doesn't support `pyproject.toml` so be sure to add the
following to the editor of choice as needed.

```ini
--ignore=W503,E203
--max-line-length=88
```

---

## [pre-commit](https://pre-commit.com)

> A framework for managing and maintaining multi-language pre-commit hooks.

This repo is setup with a `.pre-commit-config.yaml` with the expectation that
any code submitted for review already passes all selected pre-commit checks.
`pre-commit` is installed with the development requirements and runs seemlessly
with `git` hooks.

---

## Makefile

This repo has a Makefile with some quality of life scripts if the system
supports `make`.  Please note there are no checks for an active `venv` in the
Makefile.

| PHONY             | Description                                                           |
| ----------------- | --------------------------------------------------------------------- |
| `init`            | Update pip to newest version                                          |
| `install`         | install the project                                                   |
| `install-test`    | install test requirements and project as editable install             |
| `install-dev`     | install development/test requirements and project as editable install |
| `build-dist`      | Build source distribution and wheel distribution                      |
| `clean-artifacts` | Deletes python/mypy artifacts, cache, and pyc files                   |
| `clean-tests`     | Deletes tox, coverage, and pytest artifacts                           |
| `clean-build`     | Deletes build artifacts                                               |
| `clean-all`       | Runs all clean scripts                                                |