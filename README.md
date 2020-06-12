# dayone-import Utility Scripts

These scripts are for helping import data into the Day One journal app.  In most cases,
they are not as robust as they should be for widespread use.

In general, these scripts will take input from another service and output JSON data that
can be imported into Day One.

## Facebook

The script operates on the JSON export data from your Facebook account.

## Kayak

The script operates on the trips.html file.

## Configuration

TODO document the config file...

Generally, `dayone.yaml` needs to provide the API keys for doing geolocation lookups.

## Dependencies

These scripts use a number of libraries to assist with procesing:

- PyYAML - for loading config files
- Geocoder - for looking up places

