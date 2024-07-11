import json
import re
from packaging.version import Version, InvalidVersion
import click
from sys import exit

from parsers import TreeSitterParser, RegexParser
from utils import File, hash_message, Color as color


class DriverMigrationAssistent:

    def __init__(self, language_name, context_lines, version, no_output_colors, regex_parser):
        self.language_name = language_name
        self.context_lines = context_lines
        self.no_output_colors = no_output_colors
        try:
            self.version = Version(version)
        except InvalidVersion as e:
            print(f'Version `{version}` is not a valid PEP 440 version.')
            exit(1)
        if regex_parser:
            self.parser = RegexParser()
        else:
            self.parser = TreeSitterParser(language_name)

    def process_file(self, file_path):
        self.print_msg(click.style(f'File: {file_path}\n', fg=color.file, bold=True))
        self.source = File(file_path)
        self.parser.set_source(self.source)

        messages = []
        changes_json = json.loads(open(f'changelogs/{self.language_name}.json').read())
        for change in changes_json:
            captures = []
            for pattern in change['patterns']:
                captures += self.parser.get_captures_for_pattern(pattern)

            for capture in captures:
                msg = self.process_capture(capture[0], capture[1], change)
                if msg != False:
                    messages.append(msg)

        self.source.deprecated_count += self.count_deprecations(messages)
        self.source.removed_count += self.count_removals(messages)

        # sort msgs by source line number; break ties by starting col number
        messages.sort(key=lambda msg: (msg['meta']['line'], msg['meta']['col_start']))
        return messages

    def process_capture(self, start_point, end_point, change):
        '''
        start_point: tuple of (row, col) where hit starts.
        end_point: tuple of (row, col) where hit ends.
        change: change entry from which hit resulted.
        '''
        output = ''

        if self.is_deprecated(change):
            msg_color = color.deprecated
        elif self.is_removed(change):
            msg_color = color.removed
        else:
            return False
        output += click.style(change['msg'].format(**change) + '\n\n', fg=msg_color, bold=True)

        matched_line_n = start_point[0]
        for i in range(
            max(matched_line_n - self.context_lines, 0),
            min(matched_line_n + self.context_lines + 1, len(self.source.lines))
        ):
            if i == matched_line_n:
                # highlight the matched text
                match_start = start_point[1]
                match_end = end_point[1]
                line_content = self.source.lines[i][:match_start]
                line_content += click.style(self.source.lines[i][match_start:match_end], bg=color.code_highlight)
                line_content += self.source.lines[i][match_end:]
                output += '  > '  # text-highlight offending line
            else:
                line_content = self.source.lines[i]
                output += '    '
            output += click.style(i, bold=True) + ' ' + line_content + '\n'

        if change.get('deprecated') != None:
            output += '\n  ' + click.style('Deprecated in: ', bold=True) + change.get('deprecated')
        if change.get('removed') != None:
            output += '\n  ' + click.style('Removed in: ', bold=True) + change.get('removed')
        if change.get('ref') != None:
            refs = change.get('ref')
            if isinstance(refs, str):
                refs = [refs, ]  # make iterable
            for link in refs:
                output += '\n  ' + click.style('Docs: ', bold=True) + link
        output += '\n'

        return {
            'meta': {
                'line': matched_line_n,
                'col_start': start_point[1],
                'col_end': end_point[1],
                'deprecated': self.is_deprecated(change),
                'removed': self.is_removed(change)
            },
            'content': output
        }

    def count_deprecations(self, messages):
        return sum(msg['meta']['deprecated'] for msg in messages)

    def count_removals(self, messages):
        return sum(msg['meta']['removed'] for msg in messages)

    def is_deprecated(self, change):
        return (change.get('deprecated') != None and
               Version(change['deprecated']) <= self.version)

    def is_removed(self, change):
        return (change.get('removed') != None and
               Version(change['removed']) <= self.version)

    def print_msg(self, message):
        if self.no_output_colors:
            # see ANSI escape sequences https://stackoverflow.com/a/33206814
            message = re.sub(r'(3|4|9|10)[0-7]', '', message)
        # click.echo removes all ANSI codes when output to file
        click.echo(message)

    def set_ignore_msg(self, message):
        if not self.is_ignored_msg(message):  # no double entries
            f = open('ignore.db', 'a')
            f.write(hash_message(message, self.source) + '\n')

    def is_ignored_msg(self, message):
        try:
            f = open('ignore.db', 'r')
        except:
            return False

        hashes = [h.strip() for h in f.readlines()]
        if hash_message(message, self.source) in hashes:
            # Ignored msgs shouldn't count in counters
            if message['meta']['removed']:
                self.source.removed_count -= 1
            if message['meta']['deprecated']:
                self.source.deprecated_count -= 1
            return True

        return False
