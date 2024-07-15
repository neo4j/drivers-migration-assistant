import click
from sys import exit
from glob import iglob

from assistent import DriverMigrationAssistent
from utils import Color as color


intro = '''
This is the migration assistent for Neo4j language libraries (drivers). It scans your codebase and raises issues you should address before upgrading to a more recent version.
It doesn't automatically rewrite your code; it only points at where action is needed, providing in-context information on how each hit should be addressed.
'''
welcome_warning = intro + '''
Points of care:
- The assistent can detect almost all the changes you need to do in your code, but a small percentage of changelog entries can't be surfaced in this form. For a thorough list of changes, see https://neo4j.com/docs/{language_name}-manual/current/migration/ .
- Some of the hits may be false positives, so evaluate each hit.
- Implicit function calls and other hard-to-parse expressions will not be surfaced by the default parser. To broaden the search radius, use the regex parser.
- Your Cypher queries may also need changing, but this tool doesn't analyze them. See https://neo4j.com/docs/cypher-manual/current/deprecations-additions-removals-compatibility/ .
'''


@click.command(help=intro + '\nPATH is the location of project to migrate. Supports globbing.')
@click.help_option('--help', '-h')
@click.argument('path', nargs=-1)
@click.option(
    '--language', '-l', 'language_name', required=True,
    type=click.Choice(['python', 'go', 'javascript', 'java', 'dotnet']),
    help='What language the project to migrate is in.'
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
    '--regex-parser', '-R', 'regex_parser', is_flag=True, flag_value=True,
    help='Use the regex parser (likely to surface more matches, although with a higher rate of false positives).'
)
@click.option(
    '--interactive', '-I', 'interactive', is_flag=True, flag_value=True,
    help='Run the tool interactely, pausing after each entry with option to add it to the ignored list.'
)
@click.option(
    '--show-ignored', 'show_ignored', is_flag=True, flag_value=True,
    help='Include ignored entries in output.'
)
def assist(path, language_name, context_lines, version, accept_warning, no_output_colors, regex_parser, interactive, show_ignored):
    assistent = DriverMigrationAssistent(language_name, context_lines, version, no_output_colors, regex_parser)
    warn_user(accept_warning, language_name)
    file_paths = []
    for file_path in path:
        file_paths += iglob(file_path.strip(), recursive=True)
    assistent.print_msg('\n' + click.style('Files to process: ', bold=True) + str(len(file_paths)) + '\n')

    deprecated_count = 0; removed_count = 0;
    for file_path in file_paths:
        self.print_msg(click.style(f'File: {file_path}\n', fg=color.file, bold=True))
        messages = assistent.process_file(file_path)
        for i in range(len(messages)):
            msg = messages[i]

            if not show_ignored and assistent.is_ignored_msg(msg):
                assistent.print_msg(click.style(
                    f'({i+1}/{len(messages)}) ' + 'Ignored\n',
                    fg='blue', bold=True))
                continue

            assistent.print_msg(click.style(
                f'({i+1}/{len(messages)}) {msg["content"]}',
                fg='blue', bold=True))

            if interactive:
                choice = click.prompt(
                    click.style(
                        'What to do? [(n) Next, (i) Add to ignore list and hide]',
                        fg='blue', bold=True
                    ), type=click.Choice(['n', 'i']), show_choices=False)
                if choice == 'i':
                    assistent.set_ignore_msg(msg)
                assistent.print_msg('')  # newline

        deprecated_count += assistent.source.deprecated_count
        removed_count += assistent.source.removed_count

        assistent.print_msg(
            click.style('\nDeprecations in file: ', bold=True) +
            click.style(assistent.source.deprecated_count, fg=color.deprecated))
        assistent.print_msg(
            click.style('Removals in file: ', bold=True) +
            click.style(assistent.source.removed_count, fg=color.removed) + '\n')

        assistent.print_msg('-'*50)

    assistent.print_msg(click.style('\nTotal deprecations: ', bold=True) + click.style(deprecated_count, fg=color.deprecated))
    assistent.print_msg(click.style('Total removals: ', bold=True) + click.style(removed_count, fg=color.removed))

    assistent.print_msg(click.style('\nLibrary full manual: ', bold=True) + f'https://neo4j.com/docs/{language_name}-manual/current/')
    assistent.print_msg(click.style('Migration guide: ', bold=True) + f'https://neo4j.com/docs/{language_name}-manual/current/migration/' + '\n')


def warn_user(accept_warning, language_name):
    if not accept_warning:
        print(welcome_warning.format(language_name=language_name))
        agree = click.confirm('Have you carefully read this info?')
        if not agree:
            print("You don't YOLO much, do you?")
            exit()


if __name__ == '__main__':
    assist()
