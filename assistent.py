import click
import json
import textwrap as tw
from glob import iglob
from tree_sitter import Language, Parser


@click.command()
@click.argument('path')
@click.option(
    '--language', '-l', 'language_name', required=True,
    help='What language the project to migrate is in (one of: python, java, go, javascript, dotnet).'
)
@click.option(
    '--context-lines', '-c', 'context_lines', default=3,
    help='Number of surrounding lines to show around each hit, both before and after.'
)
def parse(path, language_name, context_lines):

    if language_name == 'python':
        import tree_sitter_python
        from languagequeries.python import PythonQueries
        language = Language(tree_sitter_python.language())
        queries = PythonQueries()
    else:
        raise ValueError('Invalid language. Valid choices are: python, java, go, javascript, dotnet.')

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
            if isinstance(change['identifier'], str):
                query = getattr(queries, change['type'])(change['identifier'])
            elif isinstance(change['identifier'], list):
                query = getattr(queries, change['type'])(*change['identifier'])
            else:
                raise ValueError('Change identifier must be str or list.')

            patterns = language.query(query)
            captures = clean_captures(patterns.captures(tree.root_node), change)

            for capture in captures:
                output = ''
                node = capture[0]
                output += '\n\n\033[91;1m>> ' + change['msg'] + '\033[0m\n\n'
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

                if change.get('ref'):
                    output += '\n  \033[1;4m' + 'Docs:' + '\033[0m ' + change.get('ref') + '\n'

                messages.append((matched_line_n, output))

        messages.sort(key=lambda msg: msg[0])  # sort by line number
        for msg in messages:
            click.echo(msg[1], nl=False)  # click.echo removes ANSI codes when output to file

    click.echo('\n\033[1;4m' + 'Library full manual:' + f'\033[0m https://neo4j.com/docs/{language_name}-manual/current/ \n')


def clean_captures(captures, change):
    '''
    Change entries having a list identifier result in as many matches as list elements.
    We are (normally?) only interested in the last match.
    '''
    if isinstance(change['identifier'], str):
        step_size = 1
    elif isinstance(change['identifier'], list):
        step_size = len(change['identifier'])

    return captures[step_size-1::step_size]


if __name__ == '__main__':
    parse()
