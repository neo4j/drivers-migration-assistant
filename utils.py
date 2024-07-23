from hashlib import sha256
import click
from glob import iglob
import os.path


class Color:
    deprecated = 'bright_yellow'
    removed = 'bright_red'
    code_highlight = 'cyan'
    interactive_prompt = 'blue'
    file = 'green'


class File:
    def __init__(self, file_path):
        self.path = file_path
        self.text = open(file_path).read()
        self.lines = self.text.split('\n')
        self.deprecated_count = 0
        self.removed_count = 0


def hash_message(message, source):
    #ex: example-projects/python/movies.py::import neo4j.Bookmark::import_neo4j.Bookmark
    to_hash = source.path.strip() + '::' + \
              source.lines[message['meta']['line']].strip() + '::' + \
              message['meta']['change_id'].strip()
    return sha256(to_hash.encode()).hexdigest()


def parse_path(path):
    '''
    Expand a path into paths to files. Supports globbing.
    '''
    file_paths = []
    for file_path in path:
        if os.path.isdir(file_path.strip()):  # expand dirs to include files and subdirs
            file_path = os.path.join(file_path, '**', '*')
        all_file_paths = iglob(file_path.strip(), recursive=True)
        for path in all_file_paths:
            if not os.path.isdir(path):  # ignore dir paths, as they've been expanded into their files
                file_paths.append(path)
    return file_paths
