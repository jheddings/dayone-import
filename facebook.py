#!/usr/bin/env python3

import json
import argparse

from datetime import datetime, timezone

import dayone

# TODO character encodings are not correct...
# https://stackoverflow.com/questions/52747566/what-encoding-facebook-uses-in-json-files-from-data-export

################################################################################
# load all entries from the given JSON export from Facebook
def load_posts(fb_posts_file, journal):
    fb_posts = None

    with open(fb_posts_file) as fp:
        fb_posts = json.load(fp)

    for post in fb_posts:
        entry = fb_post_as_entry(post)
        entry.tags.append('Facebook')
        entry.tags.append('Facebook-Post')

        journal.add(entry)

################################################################################
def fb_post_as_entry(fb_post):
    entry = dayone.Entry()

    if 'tags' in fb_post:
        entry.tags = fb_post['tags']

    if 'title' in fb_post:
        entry.title = fb_post['title']

    if 'data' in fb_post:
        parse_fb_post_data(fb_post['data'], entry)

    if 'attachments' in fb_post:
        parse_fb_post_attachments(fb_post['attachments'], entry)

    # assume times are UTC
    if 'timestamp' in fb_post:
        entry.timestamp = datetime.fromtimestamp(fb_post['timestamp'], tz=timezone.utc)

    # for tracking / debugging...
    #entry.tags.append(f'debug-ts-{fb_post["timestamp"]}')

    return entry

################################################################################
def parse_fb_post_data(fb_post_data, entry):
    # XXX do we want to look for hashtags in the post and add entry tags?

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
    # XXX figure out a more graceful way of handling photos and videos...
    if 'media_metadata' not in fb_media:
        return

    # posts seem to have redundant information, so let's try to quiet the noise...
    has_existing_content = entry.body is not None

    uri = fb_media['uri']
    media_meta = fb_media['media_metadata']

    if 'title' in fb_media and entry.title is None:
        entry.title = fb_media['title']

    if 'photo_metadata' in media_meta:
        photo = dayone.Photo(fb_media['uri'])
        entry.photos.append(photo)
        entry.append(photo.markdown())
        parse_fb_photo_metadata(media_meta['photo_metadata'], entry)

    # FIXME handle videos properly...
    if 'video_metadata' in media_meta:
        entry.append(f'\n```video://{uri}```')

    # posts seem to have redundant information, so let's try to quiet the noise...
    if 'description' in fb_media and not has_existing_content:
        entry.append(f'> {fb_media["description"]}')

################################################################################
def parse_fb_photo_metadata(fb_photo_meta, entry):
    if 'latitude' in fb_photo_meta and entry.place is None:
        lat = fb_photo_meta['latitude']
        lng = fb_photo_meta['longitude']

        entry.place = dayone.Place.lookup([lat, lng], reverse=True)

################################################################################
def parse_fb_video_metadata(fb_photo_meta, entry):
    pass

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

        entry.append(entry.place.markdown())

    if 'url' in fb_place:
        text = f'<{fb_place["url"]}>'
        entry.append(text)

    if 'address' in fb_place:
        entry.append(fb_place['address'])

################################################################################
def parse_fb_external_context(fb_ext, entry):
    if 'url' in fb_ext:
        # TODO generate small previews of external websites

        if 'name' in fb_ext:
            text = f'[{fb_ext["name"]}]({fb_ext["url"]})'
        else:
            text = f'<{fb_ext["url"]}>'

        entry.append(text)

################################################################################
## MAIN ENTRY

argp = argparse.ArgumentParser()
argp.add_argument('--posts', help='exported posts data')
#argp.add_argument('--photos', help='exported photo album data')
#argp.add_argument('--videos', help='exported video posts')
args = argp.parse_args()

journal = dayone.Journal(name='Facebook Import')

if args.posts is not None:
    entries = load_posts(args.posts, journal)

# TODO make this an argument
journal.export('fb_journal.zip')

