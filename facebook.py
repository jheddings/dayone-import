#!/usr/bin/env python3

import json
import argparse

from datetime import datetime

import dayone

################################################################################
# load all entries from the given JSON export from Facebook
def load_posts(fb_posts_file):
    fb_posts = None
    entries = list()

    with open(fb_posts_file) as fp:
        fb_posts = json.load(fp)

    for post in fb_posts:
        entry = fb_post_as_entry(post)
        entry.tags.append('Facebook')
        entry.tags.append('Facebook-Post')
        entries.append(entry)

    return entries

################################################################################
def fb_post_as_entry(fb_post):
    entry = dayone.Entry()

    if 'data' in fb_post:
        parse_fb_post_data(fb_post['data'], entry)

    if 'attachments' in fb_post:
        parse_fb_post_attachments(fb_post['attachments'], entry)

    if 'title' in fb_post:
        entry.title = fb_post['title']

    if 'tags' in fb_post:
        entry.tags = fb_post['tags']

    # assume times are UTC
    if 'timestamp' in fb_post:
        entry.timestamp = datetime.fromtimestamp(fb_post['timestamp'])

    # for tracking / debugging...
    #entry.tags.append('debug-ts-{0}'.format(fb_post['timestamp']))

    return entry

################################################################################
def parse_fb_post_data(fb_post_data, entry):
    for data in fb_post_data:
        if 'post' in data:
            entry.append(data['post'])

        if 'media' in data:
            parse_fb_media(data['media'], entry)

        if 'place' in data:
            parse_fb_place(data['place'], entry)

        if 'external_context' in data:
            parse_fb_external_context(data['external_context'], entry)

################################################################################
def parse_fb_post_attachments(fb_attachments, entry):
    for attachment in fb_attachments:
        data = attachment['data']
        parse_fb_post_data(data, entry)

################################################################################
def parse_fb_media(fb_media, entry):
    if 'uri' in fb_media:
        entry.photos.append(fb_media['uri'])

    if 'media_metadata' in fb_media:
        parse_fb_media_metadata(fb_media['media_metadata'], entry)

################################################################################
def parse_fb_media_metadata(fb_media_meta, entry):
    if 'photo_metadata' in fb_media_meta:
        parse_fb_photo_metadata(fb_media_meta['photo_metadata'], entry)

################################################################################
def parse_fb_photo_metadata(fb_photo_meta, entry):
    if 'latitude' in fb_photo_meta and entry.place is None:
        lat = fb_photo_meta['latitude']
        lng = fb_photo_meta['longitude']

        entry.place = dayone.Place.lookup([lat, lng], reverse=True)

################################################################################
def parse_fb_place(fb_place, entry):
    if 'coordinate' in fb_place:
        coord = fb_place['coordinate']
        lng = coord['longitude']
        lat = coord['latitude']

        entry.place = dayone.Place.lookup([lat, lng], reverse=True)

        #TODO set entry timezone

        if entry.place is not None:
            if 'name' in fb_place:
                entry.place.name = fb_place['name']

    if 'url' in fb_place:
        text = '<{0}>'.format(fb_place['url'])
        entry.append(text)

    if 'address' in fb_place:
        entry.append(fb_place['address'])

################################################################################
def parse_fb_external_context(fb_ext, entry):
    if 'url' in fb_ext:
        text = '<{0}>'.format(fb_ext['url'])
        entry.append(text)

################################################################################
## MAIN ENTRY

argp = argparse.ArgumentParser()
argp.add_argument('--posts', help='exported posts data')
#argp.add_argument('--photos', help='exported photo album data')
#argp.add_argument('--videos', help='exported video posts')
args = argp.parse_args()

journal = dayone.Journal(name='Facebook_Import')

if args.posts is not None:
    entries = load_posts(args.posts)
    journal.entries.extend(entries)

# TODO make this an argument
journal.export('fb_journal.zip')

