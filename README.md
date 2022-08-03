# PagerDuty Utils

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/pd-utils/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/pd-utils/main)
[![Python package](https://github.com/Preocts/pd-utils/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/pd-utils/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/Preocts/pd-utils/branch/main/graph/badge.svg?token=ABlYTJMwLN)](https://codecov.io/gh/Preocts/pd-utils)

- [PagerDuty Utils](#pagerduty-utils)
  - [Requirements](#requirements)
  - [Command line scripts:](#command-line-scripts)
- [Available scripts](#available-scripts)
  - [Coverage Gap Report](#coverage-gap-report)
  - [Close Old Incidents](#close-old-incidents)
  - [Safelist Gatherer](#safelist-gatherer)
  - [Simple Alert](#simple-alert)
- [Local developer installation](#local-developer-installation)
  - [Installation steps](#installation-steps)
  - [Misc Steps](#misc-steps)
  - [Note on flake8:](#note-on-flake8)
  - [pre-commit](#pre-commit)
  - [Makefile](#makefile)

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
pip install git+https://github.com/Preocts/pd-utils@X.X.X
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

All scripts can be run from the installed shell scripts or by invoking directly
with `python -m pd_utils.script_name`

---

# Available scripts

## Coverage Gap Report

Find gaps in on-call scheduling that could lead to missed alerts.  This report
provides two csv files that:

- List all Schedules found in the instance
- Identify Schedules which are lacking 100% coverage
- List all layers of Escalation Policies in the instance
- Identify layers of Escalation Policies which lack 100% coverage
  - Note: Directly assigning a user target in an escalation policy is
    technically full coverage however in the spirit of sharing on-call and
    avoiding burnout this report does not count direct contacts in the coverage
    measure
  - A column with `has_direct_contact` being `TRUE` but a `is_fully_covered` as
    `FALSE` indicats the on-call rotation needs attention

```shell
usage: coverage-gap-report [-h] [--token TOKEN] [--logging-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--look-ahead LOOK_AHEAD]

Pagerduty command line utilities.

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN         PagerDuty API Token (default: $PAGERDUTY_TOKEN)
  --logging-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: $LOGGING_LEVEL | INFO)
  --look-ahead LOOK_AHEAD
                        Number of days to look ahead for gaps, default 14

See: https://github.com/Preocts/pagerduty-utils
```

Outputs:

| filename                                 | contents                                                            |
| ---------------------------------------- | ------------------------------------------------------------------- |
| schedule_gap_reportYYYY-MM-DD.csv        | All schedules names, url links, and coverage %                      |
| escalation_rule_gap_reportYYYY-MM-DD.csv | All escalation rules (layers) names, url links, and coverage status |

Example results:

`schedule_gap_report...`

```csv
pd_id,name,html_url,coverage,entries
P4TPEME,Preocts Full Coverage,https://preocts.pagerduty.com/schedules/P4TPEME,100.0,"(('2022-07-30T21:40:30Z', '2022-08-13T21:40:30Z'),)"
PG3MDI8,Preocts Coverage Gaps,https://preocts.pagerduty.com/schedules/PG3MDI8,97.9,"(('2022-07-30T21:40:30Z', '2022-07-31T11:30:00Z'), ('2022-07-31T12:00:00Z', '2022-08-01T11:30:00Z'), ('2022-08-01T12:00:00Z', '2022-08-02T11:30:00Z'), ('2022-08-02T12:00:00Z', '2022-08-03T11:30:00Z'), ('2022-08-03T12:00:00Z', '2022-08-04T11:30:00Z'), ('2022-08-04T12:00:00Z', '2022-08-05T11:30:00Z'), ('2022-08-05T12:00:00Z', '2022-08-06T11:30:00Z'), ('2022-08-06T12:00:00Z', '2022-08-07T11:30:00Z'), ('2022-08-07T12:00:00Z', '2022-08-08T11:30:00Z'), ('2022-08-08T12:00:00Z', '2022-08-09T11:30:00Z'), ('2022-08-09T12:00:00Z', '2022-08-10T11:30:00Z'), ('2022-08-10T12:00:00Z', '2022-08-11T11:30:00Z'), ('2022-08-11T12:00:00Z', '2022-08-12T11:30:00Z'), ('2022-08-12T12:00:00Z', '2022-08-13T11:30:00Z'), ('2022-08-13T12:00:00Z', '2022-08-13T21:40:30Z'))"
PRZTRI8,Late shift no gap,https://preocts.pagerduty.com/schedules/PRZTRI8,66.7,"(('2022-07-30T21:40:30Z', '2022-07-31T04:00:00Z'), ('2022-07-31T12:00:00Z', '2022-08-01T04:00:00Z'), ('2022-08-01T12:00:00Z', '2022-08-02T04:00:00Z'), ('2022-08-02T12:00:00Z', '2022-08-03T04:00:00Z'), ('2022-08-03T12:00:00Z', '2022-08-04T04:00:00Z'), ('2022-08-04T12:00:00Z', '2022-08-05T04:00:00Z'), ('2022-08-05T12:00:00Z', '2022-08-06T04:00:00Z'), ('2022-08-06T12:00:00Z', '2022-08-07T04:00:00Z'), ('2022-08-07T12:00:00Z', '2022-08-08T04:00:00Z'), ('2022-08-08T12:00:00Z', '2022-08-09T04:00:00Z'), ('2022-08-09T12:00:00Z', '2022-08-10T04:00:00Z'), ('2022-08-10T12:00:00Z', '2022-08-11T04:00:00Z'), ('2022-08-11T12:00:00Z', '2022-08-12T04:00:00Z'), ('2022-08-12T12:00:00Z', '2022-08-13T04:00:00Z'), ('2022-08-13T12:00:00Z', '2022-08-13T21:40:30Z'))"
PQ1AJP1,Morning shift,https://preocts.pagerduty.com/schedules/PQ1AJP1,50.0,"(('2022-07-31T04:00:00Z', '2022-07-31T16:00:00Z'), ('2022-08-01T04:00:00Z', '2022-08-01T16:00:00Z'), ('2022-08-02T04:00:00Z', '2022-08-02T16:00:00Z'), ('2022-08-03T04:00:00Z', '2022-08-03T16:00:00Z'), ('2022-08-04T04:00:00Z', '2022-08-04T16:00:00Z'), ('2022-08-05T04:00:00Z', '2022-08-05T16:00:00Z'), ('2022-08-06T04:00:00Z', '2022-08-06T16:00:00Z'), ('2022-08-07T04:00:00Z', '2022-08-07T16:00:00Z'), ('2022-08-08T04:00:00Z', '2022-08-08T16:00:00Z'), ('2022-08-09T04:00:00Z', '2022-08-09T16:00:00Z'), ('2022-08-10T04:00:00Z', '2022-08-10T16:00:00Z'), ('2022-08-11T04:00:00Z', '2022-08-11T16:00:00Z'), ('2022-08-12T04:00:00Z', '2022-08-12T16:00:00Z'), ('2022-08-13T04:00:00Z', '2022-08-13T16:00:00Z'))"
PA82FR2,Late shift gap,https://preocts.pagerduty.com/schedules/PA82FR2,47.9,"(('2022-07-30T21:40:30Z', '2022-07-31T04:00:00Z'), ('2022-07-31T16:30:00Z', '2022-08-01T04:00:00Z'), ('2022-08-01T16:30:00Z', '2022-08-02T04:00:00Z'), ('2022-08-02T16:30:00Z', '2022-08-03T04:00:00Z'), ('2022-08-03T16:30:00Z', '2022-08-04T04:00:00Z'), ('2022-08-04T16:30:00Z', '2022-08-05T04:00:00Z'), ('2022-08-05T16:30:00Z', '2022-08-06T04:00:00Z'), ('2022-08-06T16:30:00Z', '2022-08-07T04:00:00Z'), ('2022-08-07T16:30:00Z', '2022-08-08T04:00:00Z'), ('2022-08-08T16:30:00Z', '2022-08-09T04:00:00Z'), ('2022-08-09T16:30:00Z', '2022-08-10T04:00:00Z'), ('2022-08-10T16:30:00Z', '2022-08-11T04:00:00Z'), ('2022-08-11T16:30:00Z', '2022-08-12T04:00:00Z'), ('2022-08-12T16:30:00Z', '2022-08-13T04:00:00Z'), ('2022-08-13T16:30:00Z', '2022-08-13T21:40:30Z'))"
```

`escalation_rule_gap_report...`

```csv
policy_id,policy_name,policy_html_url,rule_index,rule_target_names,rule_target_ids,is_fully_covered
P46S1RA,Mind the gap,https://preocts.pagerduty.com/escalation_policies/P46S1RA,1,"('Morning shift', 'Late shift gap')","('PQ1AJP1', 'PA82FR2')",False,False
P46S1RA,Mind the gap,https://preocts.pagerduty.com/escalation_policies/P46S1RA,2,"('Morning shift', 'Late shift no gap')","('PQ1AJP1', 'PRZTRI8')",False,True
P46S1RA,Mind the gap,https://preocts.pagerduty.com/escalation_policies/P46S1RA,3,"('Preocts Full Coverage',)","('P4TPEME',)",False,True
P46S1RA,Mind the gap,https://preocts.pagerduty.com/escalation_policies/P46S1RA,4,"('Preocts Coverage Gaps',)","('PG3MDI8',)",False,False
```

---

## Close Old Incidents

A tool created to enforce the maximum age of incidents on a large scale
implementation of PagerDuty. Runs in two steps:

1. First run scans PagerDuty for incidents that match the critiria for
   auto-closing
2. Second run requires inputfile generated from first run and closes incidents

Default Critiria:

- Any incident *older* than 10 days
- AND, does not have any activy in logs within last 10 days
- AND, does not have a Priority assigned

**Note: This scripts requires read/write to PagerDuty and performs an action
that cannot be reversed. Once an incident is closed it cannot be reopened.**

```shell
usage: close-old-incidents [-h] [--token TOKEN] [--email EMAIL] [--logging-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--inputfile INPUTFILE] [--close-after-days CLOSE_AFTER_DAYS]
                           [--close-active] [--close-priority]

Pagerduty command line utilities.

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN         PagerDuty API Token (default: $PAGERDUTY_TOKEN)
  --email EMAIL         PagerDuty Email (default: $PAGERDUTY_EMAIL)
  --logging-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: $LOGGING_LEVEL | INFO)
  --inputfile INPUTFILE
                        Provide a csv file to work from. If not provided a new file will be created.
  --close-after-days CLOSE_AFTER_DAYS
                        Incidents older than this are considered for closing (default: 10)
  --close-active        When present, old incidents are closed regardless of activity
  --close-priority      When present, consider incidents with priority for closing

See: https://github.com/Preocts/pagerduty-utils
```

Example use: Polling for incidents older than 5 days without priority or activity

Command: `close-old-incidents --token [API_TOKEN] --email [EMAIL] --close-after-days 5`

```shell
(venv) preocts @ Preocts ~/pd-utils (preocts-close-incidents)
└─▶ $ close-old-incidents --token [API_TOKEN] --email [EMAIL] --close-after-days 5
2022-08-02 22:14:25,261 - INFO - close_old_incidents - Pulling incidents from PagerDuty, this can take a while
2022-08-02 22:14:25,759 - INFO - close_old_incidents - Discovered 2 incidents.
2022-08-02 22:14:25,759 - INFO - close_old_incidents - Found 2 open incidents
2022-08-02 22:14:25,759 - INFO - close_old_incidents - Isolated 2 old incidents
2022-08-02 22:14:25,759 - INFO - close_old_incidents - Isolated 1 nonpriority incidents
2022-08-02 22:14:25,759 - INFO - close_old_incidents - Checking incident 0 to 100
2022-08-02 22:14:25,914 - INFO - close_old_incidents - Isolated 1 inactive incidents
2022-08-02 22:14:25,915 - INFO - close_old_incidents - Wrote 1 rows to close-old-incidents-preview-20220802-2214.csv
```

Example use: Closing incidents found in above step

Command `close-old-incidents --token [API_TOKEN] --email [EMAIL] --inputfile close-old-incidents-preview-20220802-2214.csv`

```shell
(venv) preocts @ Preocts ~/pd-utils (preocts-close-incidents)
└─▶ $ close-old-incidents --token [API_TOKEN] --email [EMAIL] --inputfile close-old-incidents-preview-20220802-2214.csv
2022-08-02 22:18:10,383 - INFO - close_old_incidents - Reading input file: close-old-incidents-preview-20220802-2214.csv
2022-08-02 22:18:10,383 - INFO - close_old_incidents - Read 1 inactives, starting actions
2022-08-02 22:18:10,384 - INFO - close_old_incidents - Start close actions on 1 incidents.
2022-08-02 22:18:11,247 - INFO - close_old_incidents - Wrote 1 rows to close-old-incidents-20220802-2218.csv
```

---

## Safelist Gatherer

A lightweight *and completely portable* script for pulling the current webhook
safelist IP addresses from PagerDuty's document site.  This script has no
requirements outside of Python's standard library.  It was written so that I
could build a monitor for when the safelisted IPs changed to avoid any missed
webhook deliveries.

Output to console:

*Optional "us" or "eu" will limit results to that region. Default is both regions*

```bash
$ safelist-gatherer [eu|us]
```

Importing as module:

```py
from pd_utils import safelist_gatherer

full_ip_list = safelist_gatherer.get_all_safelist()
eu_ip_list = safelist_gatherer.get_eu_safelist()
us_ip_list = safelist_gatherer.get_us_safelist()
```

---

## Simple Alert

A stand-alone script with only standard library dependencies for sending an API
v2 alert event to PagerDuty.  Use with the command line or as a drop-in module
for additional scripts.

[PagerDuty alert event documentation](https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgx-send-an-alert-event)

**Note**: "Simple" means simple here. There is no retry logic, little error
handling, and all alerts are delivered a `critical` status.

Console script:

```bash
simple-alert "Routing Key" "Alert Title" "Alert Body" ["dedup_key"]

or

python -m pd_utils.simple_alert "Routing Key" "Alert Title" "Alert Body" ["dedup_key"]
```

Importing as module:

```py
from pd_utils import simple_alert
pd_alert.send_alert(...)
```

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
$ cd pd-utils
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
