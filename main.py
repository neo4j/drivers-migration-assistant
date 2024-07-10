import click
from sys import exit
#import textwrap as tw
from glob import iglob

from config import *
from assistent import DriverMigrationAssistent


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
def assist(path, language_name, context_lines, version, accept_warning, no_output_colors, rough_parsing):
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


if __name__ == '__main__':
    assist()
