# define classes for creating Day One journal entries

import json

from datetime import datetime

################################################################################
class Journal:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.entries = list()
        self.name = None

    #---------------------------------------------------------------------------
    def add(self, entry):
        self.entries.append(entry)

    #---------------------------------------------------------------------------
    def json(self):
        entries = list()

        for entry in self.entries:
            entry_json = entry.json()
            entries.append(entry_json)

        journal_json = {
            'metadata' : {
                'version': '1.0'
            },
            'entries' : entries
        }

        return journal_json

################################################################################
class Entry:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.title = None
        self.body = None
        self.tags = list()
        self.place = None
        self.weather = None

        self.timestamp = datetime.now()

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
            'creationDate' : self.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            'tags' : self.tags,
            'text' : self.text()
        }

        if self.place is not None:
            entry['location'] = self.place.json()

        return entry

################################################################################
class Location:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.name = None
        self.city = None
        self.state = None
        self.country = None
        self.longitude = None
        self.latitude = None

    #---------------------------------------------------------------------------
    def json(self):
        return {
            'country' : self.country,
            'placeName' : self.name,
            'latitude' : self.latitude,
            'longitude' : self.longitude,
            'localityName' : self.city,
            'region' : {
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
