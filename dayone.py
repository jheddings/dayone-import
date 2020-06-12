# define classes for handling Day One journal entries

import re
import os
import json
import uuid

import logging
import logging.config

# TODO add support for videos

from datetime import datetime, timezone
from zipfile import ZipFile

################################################################################
class Journal:

    #---------------------------------------------------------------------------
    def __init__(self, name=None):
        self.entries = list()
        self.name = name

        self.logger = logging.getLogger('dayone.Journal')
        self.logger.info(f'New journal: {self.name}')

    #---------------------------------------------------------------------------
    def add(self, entry):
        self.logger.debug(f'Adding journal entry: {entry.id.hex} -- {entry.title}')
        self.entries.append(entry)

    #---------------------------------------------------------------------------
    # TODO add import() for testing
    #def import(self, filename):

    #---------------------------------------------------------------------------
    # TODO determine if the parameter is a filename or ZipFile
    def export(self, filename):
        self.logger.info(f'Begin journal export: {filename}')

        with ZipFile(filename, 'w') as myzip:
            self._zip_journal(myzip)

            for entry in self.entries:
                for photo in entry.photos:
                    photo.export(myzip)

    #---------------------------------------------------------------------------
    def _zip_journal(self, myzip):
        data = self.json()
        content = json.dumps(data, indent=4)

        # make sure the journal name is file safe
        if self.name is None:
            arcname = 'journal.json'
        else:
            safename = re.sub(r'[^a-zA-Z0-9 _-]', '', self.name)
            arcname = f'{safename}.json'

        self.logger.debug(f'journal data: {arcname} - {len(content)} bytes')
        myzip.writestr(arcname, content)

    #---------------------------------------------------------------------------
    def json(self):
        entries = list()

        for entry in self.entries:
            data = entry.json()
            entries.append(data)

        data = {
            'metadata' : {
                'version': '1.0'
            },
            'entries' : entries
        }

        return data

################################################################################
class Entry:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.id = uuid.uuid4()
        self.title = None
        self.body = None
        self.tags = list()
        self.place = None
        self.weather = None
        self.photos = list()

        self.timestamp = datetime.now()
        self.timezone = None

        self.logger = logging.getLogger('dayone.Entry')

    #---------------------------------------------------------------------------
    def __repr__(self):
        return "Entry(%s)" % (self.id.hex)

    #---------------------------------------------------------------------------
    def append(self, text):
        if self.body is None:
            self.body = text
        else:
            self.body += f'\n{text}'

    #---------------------------------------------------------------------------
    def markdown(self):
        text = ''

        if self.title is not None:
            text += f'# {self.title}\n'

        if self.body is not None:
            text += self.body

        return text

    #---------------------------------------------------------------------------
    def json(self):
        entry = {
            'uuid' : self.id.hex,
            'creationDate' : _isotime(self.timestamp),
            'tags' : self.tags,
            'text' : self.markdown()
        }

        if self.place is not None:
            entry['location'] = self.place.json()

        if self.timezone is not None:
            entry['timeZoneName'] = self.timezone.tzname

        if self.weather is not None:
            entry['weather'] = self.weather.json()

        if len(self.photos) > 0:
            entry['photos'] = self._json_photos()

        return entry

    #---------------------------------------------------------------------------
    def _json_photos(self):
        photos_meta = list()

        for photo in self.photos:
            photo_meta = photo.json()

            if photo_meta is not None:
                photos_meta.append(photo_meta)

        return photos_meta

################################################################################
# TODO add support for remote photos, e.g. specify using path or uri
class Photo:

    #---------------------------------------------------------------------------
    def __init__(self, path):
        self.id = uuid.uuid4().hex
        self.path = path
        self.timestamp = None

        self.logger = logging.getLogger('dayone.Photo')
        self.logger.debug(f'New photo: {self.id} -- {self.path}')

    #---------------------------------------------------------------------------
    def markdown(self):
        # TODO add support for picture captions / alt text
        return f'![{self.id}](dayone-moment://{self.id})'

    #---------------------------------------------------------------------------
    def digest(self):
        import hashlib

        md5 = hashlib.md5()
        with open(self.path, 'rb') as infile:
            md5.update(infile.read())

        return md5.hexdigest()

    #---------------------------------------------------------------------------
    def json(self):
        # Day One uses the MD5 hash of the file to identify it by name in the export
        photo_meta = {
            'identifier' : self.id,
            'md5' : self.digest()
        }

        if self.timestamp is not None:
            photo_meta['date'] = _isotime(self.timestamp)

        return photo_meta

    #---------------------------------------------------------------------------
    # TODO determine if the parameter is a filename or ZipFile
    def export(self, myzip):

        # TODO get extension from photo type
        arcname = f'photos/{self.digest()}.jpeg'

        # only add the photo if it doesn't exist in the archive...

        try:
            info = myzip.getinfo(arcname)
            self.logger.debug(f'photo exists in archive - skipping: {self.path}')

        except KeyError:
            self.logger.debug(f'adding photo to archive: {self.path} => {arcname}')
            myzip.write(self.path, arcname=arcname)

################################################################################
class Place:

    # TODO add timeZone support
    # http://api.geonames.org/timezone?lat=47.01&lng=10.2&username=demo

    #---------------------------------------------------------------------------
    def __init__(self):
        self.name = None
        self.city = None
        self.state = None
        self.country = None
        self.longitude = None
        self.latitude = None

        self.logger = logging.getLogger('dayone.Place')

    #---------------------------------------------------------------------------
    # TODO apply rate limit to API calls - https://docs.mapbox.com/api/#rate-limits
    def lookup(query, reverse=False):
        import geocoder

        place = Place()

        place.logger.debug(f'Looking up place (reverse:{reverse}) -- {query}')

        # TODO use the provider preference from the config
        api_key = config['mapbox']['key']

        if reverse is True:
            loc = geocoder.mapbox(query, method='reverse', key=api_key)
        else:
            loc = geocoder.mapbox(query, key=api_key)

        place.logger.debug(f'> result: {loc}')

        place.name = loc.address
        place.latitude = loc.lat
        place.longitude = loc.lng
        place.city = loc.city
        place.state = loc.state
        place.country = loc.country

        return place

    #---------------------------------------------------------------------------
    def markdown(self):
        text = ''

        if self.name is not None:
            text += f'## {self.name}\n'

        location = ', '.join(filter(None, (self.city, self.state, self.country)))
        if location is not None and len(location) > 0:
            text += location + '\n'

        if self.latitude is not None and self.longitude is not None:
            text += f'GPS: {self.latitude}, {self.longitude}'

        return text

    #---------------------------------------------------------------------------
    def json(self):
        return {
            'placeName' : self.name,
            'latitude' : self.latitude,
            'longitude' : self.longitude,

            'localityName' : self.city,
            'administrativeArea' : self.state,
            'country' : self.country,

            # TODO confirm we need this section
            'region' : {
                'identifier' : self.name,
                'radius' : 75,
                'center' : {
                    'latitude' : self.latitude,
                    'longitude' : self.longitude,
                }
            }
        }

################################################################################
# XXX this is still mostly a stub...
class Weather:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.sunrise = None
        self.sunset = None
        self.conditions = None
        self.temperature = None

        self.logger = logging.getLogger('dayone.Weather')

    #---------------------------------------------------------------------------
    def json(self):
        return {
            "sunsetDate" : _isotime(self.sunset),
            "sunriseDate" : _isotime(self.sunrise),
            #"weatherCode" : "mostly-cloudy-night",
            "conditionsDescription" : self.conditions,
            "temperatureCelsius" : self.temperature
        }

################################################################################
# utility method for formatting timestamps
def _isotime(timestamp):
    if timestamp is None:
        return None

    # Day One expects UTC timestamps
    timestamp = timestamp.astimezone(tz=timezone.utc)

    return timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

################################################################################
## load the config file

import yaml

# TODO improve error handling...
config = None

with open('dayone.yaml') as fp:
    config = yaml.load(fp, Loader=yaml.Loader)

if 'logging' in config:
    logging.config.dictConfig(config['logging'])

# TODO add __main__ section for local testing

