# define classes for creating Day One journal entries

import json
import yaml
import geocoder
import uuid

from datetime import datetime
from PIL import Image, UnidentifiedImageError
from zipfile import ZipFile

################################################################################
class Journal:

    #---------------------------------------------------------------------------
    def __init__(self, name=None):
        self.entries = list()
        self.name = name

    #---------------------------------------------------------------------------
    def add(self, entry):
        self.entries.append(entry)

    #---------------------------------------------------------------------------
    def export(self, filename):
        data = self.json()
        content = json.dumps(data)

        # TODO make sure the journal name is file safe if specified internally
        name = 'journal.json' if self.name is None else f'{self.name}.json'

        # TODO add photos to zip file
        with ZipFile(filename, 'w') as myzip:
            myzip.writestr(name, content)

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

    #---------------------------------------------------------------------------
    def __repr__(self):
        return "Entry(%s)" % (self.title)

    #---------------------------------------------------------------------------
    def append(self, text):
        if self.body is None:
            self.body = text
        else:
            self.body += f'\n{text}'

    #---------------------------------------------------------------------------
    def text(self):
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
            'text' : self.text()
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

    #---------------------------------------------------------------------------
    def md5(self):
        import hashlib

        md5 = hashlib.md5()
        with open(self.path, 'rb') as infile:
            md5.update(infile.read())

        return md5

    #---------------------------------------------------------------------------
    def json(self):
        # Day One uses the MD5 hash of the file to identify it by name in the export
        md5 = self.md5()

        photo_meta = {
            'md5' : md5.hexdigest()
        }

        if self.timestamp is not None:
            photo_meta['date'] = _isotime(self.timestamp)

        try:
            img = Image.open(self.path)

            photo_meta['width'] = img.width
            photo_meta['height'] = img.height
            photo_meta['type'] = img.format

        except UnidentifiedImageError:
            pass

        return photo_meta

################################################################################
class Place:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.name = None
        self.city = None
        self.state = None
        self.country = None
        self.longitude = None
        self.latitude = None

    #---------------------------------------------------------------------------
    # TODO apply rate limit to API calls - https://docs.mapbox.com/api/#rate-limits
    def lookup(query, reverse=False):
        place = Place()

        # TODO use the provider preference from the config
        api_key = config['mapbox']['key']

        if reverse is True:
            loc = geocoder.mapbox(query, method='reverse', key=api_key)
        else:
            loc = geocoder.mapbox(query, key=api_key)

        place.name = loc.address
        place.latitude = loc.lat
        place.longitude = loc.lng
        place.city = loc.city
        place.state = loc.state
        place.country = loc.country

        return place
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
class Weather:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.sunrise = None
        self.sunset = None
        self.conditions = None
        self.temperature = None

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
        timestamp = datetime.now()

    return timestamp.strftime('%Y-%m-%dT%H:%M:%S')

################################################################################
## load the config file

# TODO improve error handling...
config = None

with open('dayone.yaml') as fp:
    config = yaml.load(fp, Loader=yaml.Loader)

