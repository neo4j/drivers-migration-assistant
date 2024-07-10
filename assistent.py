import json
import re
from packaging.version import Version
import click

from parsers import TreeSitterParser, RegexParser
from utils import File
from config import *


class DriverMigrationAssistent:

    def __init__(self, language_name, context_lines, version, no_output_colors, regex_parser):
        self.language_name = language_name
        self.version = version
        self.context_lines = context_lines
        self.no_output_colors = no_output_colors
        if regex_parser:
            self.parser = RegexParser()
        else:
            self.parser = TreeSitterParser(language_name)

    def process_file(self, file_path):
        self.print_message('\n\n\033[92;1;4mFile:\033[24m ' + file_path + '\033[0m')
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

        self.source.deprecated_count = self.count_deprecations(messages)
        self.source.removed_count = self.count_removals(messages)

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
            color_code = color_deprecated
        elif self.is_removed(change):
            color_code = color_removed
        else:
            return False
        output += f'\n\n\033[{color_code};1m>> ' + change['msg'].format(**change) + '\033[0m\n\n'
        #click.echo("\n\n" + tw.indent(tw.fill("\033[91;1m" + change['msg'] + "\033[0m"), '  '))

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
                line_content += f'\033[{color_code_highlight}m{self.source.lines[i][match_start:match_end]}\033[0m'
                line_content += self.source.lines[i][match_end:]
                output += f'  > \033[1m{i}\033[0m {line_content}\n'
            else:
                line_content = self.source.lines[i]
                output += f'    \033[1m{i}\033[0m {line_content}\n'

        if change.get('deprecated'):
            output += '\n  \033[1;4m' + 'Deprecated in:' + '\033[0m ' + change.get('deprecated')
        if change.get('removed'):
            output += '\n  \033[1;4m' + 'Removed in:' + '\033[0m ' + change.get('removed')
        if change.get('ref'):
            refs = change.get('ref')
            if isinstance(refs, str):
                refs = [refs, ]  # make iterable
            for link in refs:
                output += '\n  \033[1;4m' + 'Docs:' + '\033[0m ' + link
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
               Version(change['deprecated']) <= Version(self.version))

    def is_removed(self, change):
        return (change.get('removed') != None and
               Version(change['removed']) <= Version(self.version))

    def print_message(self, message):
        if self.no_output_colors:
            # see ANSI escape sequences https://stackoverflow.com/a/33206814
            message = re.sub(r'(3|4|9|10)[0-7]', '', message)
        # click.echo removes ANSI codes when output to file
        click.echo(message, nl=False)
