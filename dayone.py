# define classes for handling Day One journal entries

import re
import os
import json
import yaml
import uuid

import logging
import logging.config

# XXX probably need to add a local working directoryto the config,
#     especially a place where photos and videos can be managed

from datetime import datetime, timezone
from zipfile import ZipFile

################################################################################
class Archive:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.journals = list()
        self.logger = logging.getLogger('dayone.Archive')

    #---------------------------------------------------------------------------
    def add(self, journal):
        self.logger.debug(f'Adding journal: {journal.name}')
        self.journals.append(journal)

    #---------------------------------------------------------------------------
    def load(filename):
        archive = Archive()
        archive.logger.info(f'Loading archive: {filename}')

        with ZipFile(filename, 'r') as myzip:
            for arcname in myzip.namelist():

                # import all .json files in archive as journals
                if arcname.endswith('.json'):
                    archive.logger.debug(f'loading journal from archive: {arcname}')
                    raw = myzip.read(arcname)
                    data = json.loads(raw)
                    journal = Journal.deserialize(data)
                    archive.add(journal)

            # TODO import photos - where to extract?
            # TODO import videos - where to extract?

        return archive

    #---------------------------------------------------------------------------
    def save(self, filename):
        self.logger.info(f'Saving archive: {filename}')

        with ZipFile(filename, 'w') as myzip:
            for journal in self.journals:
                self._zip_journal(journal, myzip)

    #---------------------------------------------------------------------------
    def dump(self):
        self.logger.debug(f'dumping archive')

        # dump as YAML with multiple docs in stream
        # XXX this is nice for viewing, but harder to compare against the original
        print('%YAML 1.2')

        for journal in self.journals:
            data = journal.serialize()
            print("---\n" + yaml.dump(data))

    #---------------------------------------------------------------------------
    def _safe_journal_name(self, name):
        if name is None:
            return 'journal'

        # make sure the journal name is file safe
        return re.sub(r'[^a-zA-Z0-9 _-]', '', name)

    #---------------------------------------------------------------------------
    def _zip_journal(self, journal, myzip):
        self._zip_journal_json(journal, myzip)

        for entry in journal.entries:
            for photo in entry.photos:
                self._zip_photo(photo, myzip)

    #---------------------------------------------------------------------------
    def _zip_journal_json(self, journal, myzip):
        # export the journal as json
        data = journal.serialize()
        content = json.dumps(data, indent=4)

        # make sure the journal name is file safe
        arcname = self._safe_journal_name(journal.name)
        arcname = f'{arcname}.json'

        self.logger.debug(f'journal data: {arcname} - {len(content)} bytes')
        myzip.writestr(arcname, content)

    #---------------------------------------------------------------------------
    def _zip_entry_exists(self, myzip, arcname):
        try:
            info = myzip.getinfo(arcname)

            # TODO improve logging information
            self.logger.debug(f'{info}')

        except KeyError:
            pass

        return False

    #---------------------------------------------------------------------------
    def _zip_photo(self, photo, myzip):

        # TODO get extension from photo type
        arcname = f'photos/{photo.digest()}.jpeg'

        # only add the photo if it doesn't exist in the archive...
        if self._zip_entry_exists(myzip, arcname):
            self.logger.debug(f'photo exists in archive - skipping: {photo.path}')

        else:
            self.logger.debug(f'adding photo to archive: {photo.path} => {arcname}')
            myzip.write(photo.path, arcname=arcname)

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
        self.logger.debug(f'Adding journal entry: {entry.id} -- {entry.title}')
        self.entries.append(entry)

    #---------------------------------------------------------------------------
    def serialize(self):
        entries = list()

        for entry in self.entries:
            data = entry.serialize()
            entries.append(data)

        data = {
            'metadata' : {
                'version': '1.0'
            },
            'entries' : entries
        }

        if self.name is not None:
            data['name'] = self.name

        return data

    #---------------------------------------------------------------------------
    def deserialize(data):
        journal = Journal()

        if 'name' in data:
            self.name = data['name']

        for entry_data in data['entries']:
            entry = Entry.deserialize(entry_data)
            journal.add(entry)

        return journal

################################################################################
class Entry:

    #---------------------------------------------------------------------------
    def __init__(self, id=None):
        if id is None:
            self.id = uuid.uuid4()
        else:
            self.id = id

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
        return "Entry(%s)" % (self.id)

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
    def serialize(self):
        entry = {
            'uuid' : self.id.hex,
            'creationDate' : _format_timestamp(self.timestamp),
            'tags' : self.tags,
            'text' : self.markdown()
        }

        if self.place is not None:
            entry['location'] = self.place.serialize()

        if self.timezone is not None:
            entry['timeZoneName'] = self.timezone.tzname

        if self.weather is not None:
            entry['weather'] = self.weather.serialize()

        if len(self.photos) > 0:
            entry['photos'] = self._serialize_photos()

        # TODO process videos

        return entry

    #---------------------------------------------------------------------------
    def _serialize_photos(self):
        data = list()

        for photo in self.photos:
            photo_data = photo.serialize()

            if photo_data is not None:
                data.append(photo_data)

        return data

    #---------------------------------------------------------------------------
    def deserialize(data):
        entry_id = None

        if 'uuid' in data:
            entry_id = uuid.UUID(hex=data['uuid'])

        entry = Entry(id=entry_id)

        if 'tags' in data:
            entry.tags = data['tags']

        if 'creationDate' in data:
            entry.timestamp = _parse_timestamp(data['creationDate'])

        if 'text' in data:
            # TODO split title if present
            text = data['text']
            entry.body = text

        if 'location' in data:
            entry.place = Place.deserialize(data['location'])

        if 'weather' in data:
            entry.weather = Weather.deserialize(data['weather'])

        if 'photos' in data:
            entry.photos = Entry._deserialize_photos(data['photos'])

        # TODO process timeZone
        # TODO process videos

        return entry

    #---------------------------------------------------------------------------
    def _deserialize_photos(data):
        photos = list()

        for photo_data in data:
            photo = Photo.deserialize(photo_data)
            if photo is not None:
                photos.append(photo)

        return photos

################################################################################
# TODO add support for remote photos, e.g. specify using path or uri
# TODO add support for paths to photos embedded in a zipfile
class Photo:

    #---------------------------------------------------------------------------
    def __init__(self, path, id=None):
        if id is None:
            self.id = uuid.uuid4()
        else:
            self.id = id

        self.path = path
        self.timestamp = None

        self.logger = logging.getLogger('dayone.Photo')
        self.logger.debug(f'New photo: {self.id} -- {self.path}')

    #---------------------------------------------------------------------------
    def markdown(self):
        # TODO add support for picture captions / alt text
        return f'![{self.id}](dayone-moment://{self.id.hex})'

    #---------------------------------------------------------------------------
    def digest(self):
        import hashlib

        if self.path is None:
            return None

        md5 = hashlib.md5()
        with open(self.path, 'rb') as infile:
            md5.update(infile.read())

        return md5.hexdigest()

    #---------------------------------------------------------------------------
    def serialize(self):
        # Day One uses the MD5 hash of the file to identify it by name in the export
        data = {
            'identifier' : self.id.hex,
            'md5' : self.digest()
        }

        if self.timestamp is not None:
            data['date'] = _format_timestamp(self.timestamp)

        return data

    #---------------------------------------------------------------------------
    def deserialize(data):
        photo_id = None

        if 'identifier' in data:
            photo_id = uuid.UUID(hex=data['identifier'])

        photo = Photo(path=None, id=photo_id)

        # TODO need to store and deserialize the photo name / md5
        if 'file_reference' in data:
            photo.name = data['file_reference']

        if 'date' in data:
            photo.timestamp = _parse_timestamp(data['date'])

        return photo

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
    def serialize(self):
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

    #---------------------------------------------------------------------------
    def deserialize(data):
        place = Place()

        if 'placeName' in data:
            place.name = data['placeName']

        if 'localityName' in data:
            place.city = data['localityName']

        if 'administrativeArea' in data:
            place.state = data['administrativeArea']

        if 'country' in data:
            place.country = data['country']

        if 'latitude' in data and 'longitude' in data:
            place.latitude = data['latitude']
            place.longitude = data['longitude']

        return place

################################################################################
# XXX this is still mostly a stub...
class Weather:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.conditions = None
        self.temperature = None

        self.logger = logging.getLogger('dayone.Weather')

    #---------------------------------------------------------------------------
    def serialize(self):
        return {
            #"weatherCode" : "mostly-cloudy-night",
            "conditionsDescription" : self.conditions,
            "temperatureCelsius" : self.temperature
        }

    #---------------------------------------------------------------------------
    def deserialize(data):
        wx = Weather()

        if 'temperatureCelsius' in data:
            wx.temperature = data['temperatureCelsius']

        if 'conditionsDescription' in data:
            wx.conditions = data['conditionsDescription']

        return wx

################################################################################
# utility method for formatting timestamps
def _format_timestamp(timestamp):
    if timestamp is None:
        return None

    # Day One expects UTC timestamps
    timestamp = timestamp.astimezone(tz=timezone.utc)

    return timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

################################################################################
# utility method for parsing timestamps
def _parse_timestamp(timestamp):
    ts = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    ts = ts.replace(tzinfo=timezone.utc)

    return ts

################################################################################
def main():
    import argparse

    argp = argparse.ArgumentParser()
    argp.add_argument('--load', help='file to read import data')
    argp.add_argument('--save', help='file to write export data')
    #argp.add_argument('--config', help='use specified config file', default='dayone.yaml')
    args = argp.parse_args()

    archive = None

    if args.load is not None:
        archive = Archive.load(args.load)

    if args.save is not None:
        archive.save(args.save)
    else:
        archive.dump()

################################################################################
## load the config file

# TODO improve error handling...
config = None

with open('dayone.yaml') as fp:
    config = yaml.load(fp, Loader=yaml.Loader)

if 'logging' in config:
    logging.config.dictConfig(config['logging'])

################################################################################
## MAIN ENTRY
if __name__ == '__main__':
    main()

