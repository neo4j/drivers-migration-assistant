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
    #ex.   example-projects/python/movies.py::import neo4j.Bookmark::>> Importing `neo4j.Bookmark` and its submodules has been deprecated. Everything should be imported directly from `neo4j` instead.
    to_hash = source.path.strip() + '::' + \
              source.lines[message['meta']['line']].strip() + '::' + \
              click.unstyle(message['content'].split('\n')[0]).strip()
    return sha256(to_hash.encode()).hexdigest()
