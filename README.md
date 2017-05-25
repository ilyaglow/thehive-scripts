Scripts
-------

# Case to pdf converter

## Install

```
cd case-to-pdf && pip install pipenv && pipenv install
```

## Usage

```
usage: case_grabber.py [-h] -s URL -u USER -p PASSWORD -c CASE -o OUTPUT

optional arguments:
  -h, --help            show this help message and exit
  -s URL, --url URL     TheHive server URL
  -u USER, --user USER  Username
  -p PASSWORD, --password PASSWORD
                        User password
  -c CASE, --case CASE  Case ID, could be retrieved from case URL
  -o OUTPUT, --output OUTPUT
                        PDF output filename

```
