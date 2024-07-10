import click
from sys import exit
#import textwrap as tw
from glob import iglob

from config import *
from assistent import DriverMigrationAssistent


intro = '''
This is the migration assistent for Neo4j language libraries (drivers). It scans your codebase and raises issues you should address before upgrading to a more recent version.
It doesn't automatically rewrite your code; it only points at where action is needed, providing in-context information on how each hit should be addressed.
'''
welcome_warning = intro + '''
Be aware that:
- The assistent can detect the largest majority of the changes you need to do in your code, but there is a small percentage of changelog entries that can't be surfaced in this form. For a thorough list of changes across versions, see https://neo4j.com/docs/{language_name}-manual/current/migration/ .
- Some of the hits may be false positives, so evaluate each hit.
- Implicit function calls and other hard to parse expressions will not be surfaced by the default parser. To broaden the search radius, use --regex-parser. The regex parser is likely to return more false positives, so the best course of action is to run the assistent with the default parser, fix all the surfaced hits, and then run it again with the regex parser.
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
    help='Use a coarser parser. This is likely to surface more matches, though with a higher rate of false positives.'
)
@click.option(
    '--interactive', '-I', 'interactive', is_flag=True, flag_value=True,
    help=''
)
@click.option(
    '--show-ignored', 'show_ignored', is_flag=True, flag_value=True,
    help=''
)
def assist(path, language_name, context_lines, version, accept_warning, no_output_colors, regex_parser, interactive, show_ignored):
    assistent = DriverMigrationAssistent(language_name, context_lines, version, no_output_colors, regex_parser)
    warn_user(accept_warning, language_name)
    file_paths = []
    for file_path in path:
        file_paths += iglob(file_path.strip(), recursive=True)

    deprecated_count = 0; removed_count = 0;
    for file_path in file_paths:
        messages = assistent.process_file(file_path)
        for i in range(len(messages)):
            msg = messages[i]

            if not show_ignored and assistent.should_ignore_msg(msg):
                click.secho(
                    '\n' + f'  ({i+1}/{len(messages)}) ' + 'Ignored',
                    fg='blue', bold=True, nl=False)
                continue

            if not interactive:
                click.secho(
                    '\n\n\n' + f'  ({i+1}/{len(messages)}) ',
                    fg='blue', bold=True, nl=False)

            assistent.print_message(msg['content'])

            if interactive:
                click.echo('\n\n', nl=False)
                choice = click.prompt(click.style(
                    f'  ({i+1}/{len(messages)}) ' + 'What to do? [(n) Next, (i) Ignore forever]',
                    fg='blue', bold=True
                ))
                if choice == 'i':
                    assistent.set_ignore_msg(msg)


        deprecated_count += assistent.source.deprecated_count
        removed_count += assistent.source.removed_count

        '''assistent.print_message(
            '\n\n\033[1;4m' + 'Deprecations in file:' +
            f'\033[0;{color_deprecated}m {assistent.source.deprecated_count}\033[0m \n')
        assistent.print_message(
            '\033[1;4m' + 'Removals in file:' +
            f'\033[0;{color_removed}m {assistent.source.removed_count}\033[0m \n')
        '''
        assistent.print_message('\n\n' + '-'*50)

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
        print(welcome_warning.format(language_name=language_name))
        agree = click.confirm('Have you carefully read this info?')
        if not agree:
            print("You don't YOLO much, do you?")
            exit()


if __name__ == '__main__':
    assist()
