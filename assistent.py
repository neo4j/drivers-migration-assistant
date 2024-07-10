import click
import json
from sys import exit
import re
#import textwrap as tw
from glob import iglob
from tree_sitter import Language, Parser
from packaging.version import Version


color_deprecated = '93'  # bright red
color_removed = '91'  # bright yellow
color_code_highlight = '46'  # light blue

intro = '''
This is the assistant migrator for Neo4j language libraries (drivers). It scans your codebase and raises issues you should address before upgrading to a more recent version. It doesn't automatically rewrite your code; it only points at where action is needed, providing in-context information on how each hit should be addressed.
'''
welcome_warning = intro + '''
Be aware that:
- The assistant can detect the largest majority of the changes you need to do in your code, but there is a small percentage of changelog entries that can't be surfaced in this form. For a thorough list of changes across versions, see https://neo4j.com/docs/{language_name}-manual/current/migration/ .
- Some of the hits may be false positives, so evaluate each hit.
- Implicit function calls and other hard to parse expressions will not be surfaced by the default parser. To broaden the search radius, use --rough-parsing. The coarser parser is likely to return more false positives, so the best course of action is to run the assistant with the default parser, fix all the surfaced hits, and then run it again with the rough parser.
- Your Cypher queries may also need changing, but this tool doesn't analyze them. See https://neo4j.com/docs/cypher-manual/current/deprecations-additions-removals-compatibility/ .

To continue, type Y to confirm you've carefully read this info or anything else to quit: '''


@click.command(help=intro)
@click.help_option('--help', '-h')
@click.argument('path')
@click.option(
    '--language', '-l', 'language_name', required=True,
    help='What language the project to migrate is in (one of: python, java, go, javascript, dotnet).'
)
@click.option(
    '--context-lines', '-c', 'context_lines', default=3, show_default=True,
    help='Number of surrounding lines to show around each hit, both before and after.'
)
@click.option(
    '--version', default='6.0', show_default=True,
    help='What version of the library to test compatibility against.'
)
@click.option(
    '--accept-warning', 'accept_warning', is_flag=True, flag_value=True,
    help='Accept and skip the opening warning.'
)
@click.option(
    '--no-output-colors', 'no_output_colors', is_flag=True, flag_value=True,
    help="Don't enrich output with colors."
)
@click.option(
    '--rough-parsing', '-R', 'rough_parsing', is_flag=True, flag_value=True,
    help='Use a coarser parser. This is likely to surface more matches, though with a higher rate of false positives.'
)
def parse(path, language_name, context_lines, version, accept_warning, no_output_colors, rough_parsing):
    assistent = DriverMigrationAssistent(language_name, context_lines, version, no_output_colors, rough_parsing)
    warn_user(accept_warning, language_name)
    file_paths = iglob(path.strip(), recursive=True)
    deprecated_count = 0; removed_count = 0;
    for file_path in file_paths:
        messages = assistent.process_file(file_path)
        for msg in messages:
            assistent.print_message(msg['content'])

        deprecated_count += assistent.source.deprecated_count
        removed_count += assistent.source.removed_count

        assistent.print_message(
            '\n\n\033[1;4m' + 'Deprecations in file:' +
            f'\033[0;{color_deprecated}m {assistent.source.deprecated_count}\033[0m \n')
        assistent.print_message(
            '\033[1;4m' + 'Removals in file:' +
            f'\033[0;{color_removed}m {assistent.source.removed_count}\033[0m \n')

        assistent.print_message('\n' + '-'*50)

    assistent.print_message(
        '\n\n\033[1;4m' + 'Total deprecations:' +
        f'\033[0;{color_deprecated}m {deprecated_count}\033[0m\n')
    assistent.print_message(
        '\033[1;4m' + 'Total removals:' +
        f'\033[0;{color_removed}m {removed_count}\033[0m\n')

    assistent.print_message(
        '\n\033[1;4m' + 'Library full manual:' +
        f'\033[0m https://neo4j.com/docs/{language_name}-manual/current/')
    assistent.print_message(
        '\n\033[1;4m' + 'Migration page:' +
        f'\033[0m https://neo4j.com/docs/{language_name}-manual/current/migration/ \n\n')


def warn_user(accept_warning, language_name):
    if not accept_warning:
        agree = input(welcome_warning.format(language_name=language_name))
        if agree.lower() != 'y':
            print("You don't YOLO much, do you?")
            exit()


class DriverMigrationAssistent:

    def __init__(self, language_name, context_lines, version, no_output_colors, rough_parsing):
        self.language_name = language_name
        self.version = version
        self.context_lines = context_lines
        self.no_output_colors = no_output_colors
        self.rough_parsing = rough_parsing
        self.language, self.queries = self.include_language()

    def include_language(self):
        if self.language_name == 'python':
            import tree_sitter_python as tslang
            from languagequeries.python import PythonQueries
            queries = PythonQueries()
        elif self.language_name == 'go':
            import tree_sitter_go as tslang
            from languagequeries.go import GoQueries
            queries = GoQueries()
        else:
            raise ValueError('Invalid language. Valid choices are: python, java, go, javascript, dotnet.')

        language = Language(tslang.language())
        return language, queries

    def process_file(self, file_path):
        self.print_message('\n\n\033[92;1;4mFile:\033[24m ' + file_path + '\033[0m')
        self.source = File(file_path, self.language)
        messages = []

        changes_json = json.loads(open(f'changelogs/{self.language_name}.json').read())
        for change in changes_json:
            captures = []
            for pattern in change['patterns']:
                if self.rough_parsing:
                    captures += self.get_captures_for_re_pattern(pattern)
                else:
                    captures += self.get_captures_for_ts_pattern(pattern)

            for capture in captures:
                msg = self.process_capture(capture[0], capture[1], change)
                if msg != False:
                    messages.append(msg)

        self.source.deprecated_count = self.count_deprecations(messages)
        self.source.removed_count = self.count_removals(messages)

        # sort msgs by source line number; break ties by starting col number
        messages.sort(key=lambda msg: (msg['meta']['line'], msg['meta']['col_start']))
        return messages

    def get_captures_for_ts_pattern(self, pattern):
        if pattern.get('ts_pattern') == None:
            return []

        if isinstance(pattern['ts_pattern'], str):
            query = getattr(self.queries, pattern['ts_type'])(pattern['ts_pattern'])
        elif isinstance(pattern['ts_pattern'], list):
            query = getattr(self.queries, pattern['ts_type'])(*pattern['ts_pattern'])
        else:
            raise ValueError('Change identifier must be str or list.')

        matches = self.language.query(query)
        captures = self.uniqueify_ts_captures(matches.captures(self.source.ast.root_node), pattern)
        return [(c[0].range.start_point, c[0].range.end_point) for c in captures]  # only extract relevant bits

    def uniqueify_ts_captures(self, captures, pattern):
        '''
        Pattern change entries consisting of a list yield as many matches as
        list elements, from tree-sitter. (Normally?) Only the last match is relevant.
        '''
        if isinstance(pattern['ts_pattern'], str):
            step_size = 1
        elif isinstance(pattern['ts_pattern'], list):
            step_size = len(pattern['ts_pattern'])

        return captures[step_size-1::step_size]

    def get_captures_for_re_pattern(self, pattern):
        captures = []

        if pattern.get('re_pattern') == None:
            return captures

        for i in range(len(self.source.lines)):
            match = re.search(pattern['re_pattern'], self.source.lines[i])
            if match != None:
                captures.append(
                    (
                        (i, match.start()),
                        (i, match.end())
                    )
                )

        return captures

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
                line_content  = self.source.lines[i][:match_start]
                line_content += f'\033[{color_code_highlight}m{self.source.lines[i][match_start:match_end]}\033[0m'
                line_content += self.source.lines[i][match_end:]
            else:
                line_content = self.source.lines[i]
            output += f'  \033[1m{i}\033[0m {line_content}\n'

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


class File:

    def __init__(self, file_path, language):
        self.text = open(file_path).read()
        self.lines = self.text.split('\n')
        self.ast = Parser(language).parse(bytes(self.text, 'utf8'))
        self.deprecated_count = 0
        self.removed_count = 0


if __name__ == '__main__':
    parse()
