# define classes for creating Day One journal entries

import json
import yaml
import geocoder
import hashlib
import uuid

from datetime import datetime
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
        name = 'journal.json' if self.name is None else '{0}.json'.format(self.name)

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
            self.body += '\n{0}'.format(text)

    #---------------------------------------------------------------------------
    def text(self):
        text = ''

        if self.title is not None:
            text += '# {0}\n'.format(self.title)

        if self.body is not None:
            text += self.body

        return text

    #---------------------------------------------------------------------------
    def json(self):
        entry = {
            'uuid' : self.id.hex,
            'creationDate' : self.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            'tags' : self.tags,
            'text' : self.text()
        }

        if self.place is not None:
            entry['location'] = self.place.json()

        if self.timezone is not None:
            entry['timeZoneName'] = self.timezone.tzname

        if self.weather is not None:
            entry['weather'] = self.weather.json()

        #if len(self.photos) > 0:
        #    entry['photos'] = self._json_photos()

        return entry

    #---------------------------------------------------------------------------
    def _json_photos(self):
        photos_meta = list()

        for photo in self.photos:
            photo_meta = self._json_photo(photo)

            if photo_meta is not None:
                photos_meta.append(photo_meta)

        return photos_meta

    #---------------------------------------------------------------------------
    def _json_photo(self, photo):
        photo_meta = None

        # FIXME need a way to reference the local photo file
        # this requires an MD5 of the photo with an identifier...  use photo name?

        try:
            img = Image.open(photo)

            photo_meta = {
                'width' : img.width,
                'height' : img.height,
                'type' : img.format
            }
        except:
            photo_meta = None

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
            "sunsetDate" : self.sunset.strftime('%Y-%m-%dT%H:%M:%S'),
            "sunriseDate" : self.sunrise.strftime('%Y-%m-%dT%H:%M:%S'),
            #"weatherCode" : "mostly-cloudy-night",
            "conditionsDescription" : self.conditions,
            "temperatureCelsius" : self.temperature
        }


################################################################################
## load the config file

# TODO improve error handling...
config = None

with open('dayone.yaml') as fp:
    config = yaml.load(fp, Loader=yaml.Loader)

