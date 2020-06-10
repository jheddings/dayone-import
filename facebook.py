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
        entries.append(entry)

    return entries

################################################################################
def fb_post_as_entry(fb_post):
    entry = dayone.Entry()

    if 'data' in fb_post:
        parse_fb_post_data(fb_post['data'], entry)

    if 'title' in fb_post:
        entry.title = fb_post['title']

    if 'tags' in fb_post:
        entry.tags = fb_post['tags']

    # assume times are UTC
    if 'timestamp' in fb_post:
        entry.timestamp = datetime.fromtimestamp(fb_post['timestamp'])

    return entry

################################################################################
def parse_fb_post_data(fb_post_data, entry):
    for entry_data in fb_post_data:
        if 'post' in entry_data:
            entry.body = entry_data['post']

################################################################################
## MAIN ENTRY

argp = argparse.ArgumentParser()

argp.add_argument('--posts', help='exported posts data')
#argp.add_argument('--photos', help='exported photo album data')
#argp.add_argument('--videos', help='exported video posts')

args = argp.parse_args()

journal = dayone.Journal()

if args.posts is not None:
    entries = load_posts(args.posts)
    journal.entries.extend(entries)

journal_json = journal.json()
print(json.dumps(journal_json, indent=4))

