# wallabag-to-linkding

Load Wallabag JSON export file into linkding via REST API.

## Prerequisites

The script uses [Python](https://www.python.org/)
with the [httpx](https://www.python-httpx.org/) package,
which must be installed as a system package,
or in a virtual environment.

Export all entries from Wallabag to a JSON file.

Set the name of this file as well as your linkding URL and API token at the top of the script file.

Alternatively, set these values in the environment variables
`WALLABAG_JSON_FILE`, `LINKDING_API_URL` and  `LINKDING_API_TOKEN`.

## Running the script

When everything is set, simply run the script using Python:

```sh
python wallabag-to-linkding.py
```
