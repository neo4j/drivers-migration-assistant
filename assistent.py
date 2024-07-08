import click
import json
from sys import exit
#import textwrap as tw
from glob import iglob
from tree_sitter import Language, Parser
from packaging.version import Version


welcome_warning = '''
This is an assistant migrator for Neo4j language libraries (drivers).

...

To continue, type Y to confirm you've read this info or anything else to quit: '''


@click.command()
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
    help='Skip the initial warning.'
)
@click.option(
    '--rough-parsing', '-R', 'rough_parsing', is_flag=True, flag_value=True,
    help='Use a coarser parser. This is likely to surface more matches, but with more possible false positives as well.'
)
def parse(path, language_name, context_lines, version, accept_warning, rough_parsing):

    language, queries = include_language(language_name)
    warn_user(accept_warning)

    file_paths = iglob(path.strip(), recursive=True)
    for file_path in file_paths:
        click.echo('\n\n\033[92;1;4mFile:\033[24m ' + file_path + '\033[0m', nl=False)

        source_text = open(file_path).read()
        source_lines = source_text.split("\n")

        parser = Parser(language)
        tree = parser.parse(bytes(source_text, 'utf8'))

        messages = []

        changes_json = json.loads(open(f'changelogs/{language_name}.json').read())
        for change in changes_json:
            captures = []
            for pattern in change['patterns']:
                if isinstance(pattern['pattern'], str):
                    query = getattr(queries, pattern['type'])(pattern['pattern'])
                elif isinstance(pattern['pattern'], list):
                    query = getattr(queries, pattern['type'])(*pattern['pattern'])
                else:
                    raise ValueError('Change identifier must be str or list.')

                matches = language.query(query)
                captures += clean_captures(matches.captures(tree.root_node), pattern)

            for capture in captures:
                output = ''
                node = capture[0]

                if is_deprecated(change, version):
                    color_code = '93'
                elif is_removed(change, version):
                    color_code = '91'
                else:
                    continue
                output += f'\n\n\033[{color_code};1m>> ' + change['msg'].format(**change) + '\033[0m\n\n'
                #click.echo("\n\n" + tw.indent(tw.fill("\033[91;1m" + change['msg'] + "\033[0m"), '  '))

                matched_line_n = node.range.start_point[0]
                for i in range(
                    max(matched_line_n - context_lines, 0),
                    min(matched_line_n + context_lines + 1, len(source_lines))
                ):
                    if i == matched_line_n:
                        # highlight the matched text
                        line_content  = source_lines[i][:node.range.start_point[1]]
                        line_content += f'\033[46m{source_lines[i][node.range.start_point[1]:node.range.end_point[1]]}\033[0m'
                        line_content += source_lines[i][node.range.end_point[1]:]
                    else:
                        line_content = source_lines[i]
                    output += f'  \033[1m{i}\033[0m {line_content}\n'

                if change.get('deprecated'):
                    output += '\n  \033[1;4m' + 'Deprecated in:' + '\033[0m ' + change.get('deprecated')
                if change.get('removed'):
                    output += '\n  \033[1;4m' + 'Removed in:' + '\033[0m ' + change.get('removed')
                if change.get('ref'):
                    refs = change.get('ref')
                    if isinstance(refs, str):
                        refs = [refs, ]
                    for link in refs:
                        output += '\n  \033[1;4m' + 'Docs:' + '\033[0m ' + link
                output += '\n'

                messages.append({
                    'meta': {
                        'line': matched_line_n,
                        'col_start': node.range.start_point[1],
                        'col_end': node.range.end_point[1]
                    },
                    'content': output
                })

        messages.sort(key=lambda msg: (msg['meta']['line'], msg['meta']['col_start']))  # sort by line number; break ties by starting col number
        for msg in messages:
            click.echo(msg['content'], nl=False)  # click.echo removes ANSI codes when output to file

    click.echo('\n\033[1;4m' + 'Library full manual:' + f'\033[0m https://neo4j.com/docs/{language_name}-manual/current/ \n')


def include_language(language_name):
    if language_name == 'python':
        import tree_sitter_python as tslang
        from languagequeries.python import PythonQueries
        queries = PythonQueries()
    elif language_name == 'go':
        import tree_sitter_go as tslang
        from languagequeries.go import GoQueries
        queries = GoQueries()
    else:
        raise ValueError('Invalid language. Valid choices are: python, java, go, javascript, dotnet.')

    language = Language(tslang.language())

    return language, queries


def warn_user(accept_warning):
    if not accept_warning:
        agree = input(welcome_warning)
        if agree.lower() != 'y':
            print("You don't YOLO much, do you?")
            exit()


def is_deprecated(change, version):
    return change.get('deprecated') and Version(change['deprecated']) <= Version(version)
def is_removed(change, version):
    return change.get('removed') and Version(change['removed']) <= Version(version)


def clean_captures(captures, pattern):
    '''
    Pattern change entries having a list identifier result in as many matches as list elements.
    (Normally?) Only the last match is relevant.
    '''
    if isinstance(pattern['pattern'], str):
        step_size = 1
    elif isinstance(pattern['pattern'], list):
        step_size = len(pattern['pattern'])

    return captures[step_size-1::step_size]


if __name__ == '__main__':
    parse()
