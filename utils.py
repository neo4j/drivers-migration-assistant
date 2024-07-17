from hashlib import sha256
import click


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
