# define classes for creating Day One journal entries

import json

from datetime import datetime

################################################################################
class Journal:

    #---------------------------------------------------------------------------
    def __init__(self):
        self.entries = list()

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

        self.timestamp = datetime.now()

    #---------------------------------------------------------------------------
    def __repr__(self):
        return "Entry(%s)" % (self.title)

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

        return entry

