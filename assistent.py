import json
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from languagequeries.python import PythonQueries


language_name = 'python'
language = Language(tspython.language())
queries = PythonQueries()


def main():
    source_text = open('example-projects/python/movies.py').read()
    source_lines = source_text.split("\n")

    parser = Parser(language)
    tree = parser.parse(bytes(source_text, 'utf8'))

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
        for el in captures:
            node = el[0]
            print("\n\n\033[91;1m" + change['msg'] + "\033[0m")
            if change.get('ref'):
                print('\033[1;4m' + 'Docs:' + '\033[0m', change.get('ref'))

            print('\n', end='')
            line_n = node.range.start_point[0]
            for i in range(max(line_n - 2, 0), min(line_n + 3, len(source_lines))):
                print_line(source_lines, i)


def print_line(source_lines, line_n):
    print(f'\033[1m{line_n}\033[0m {source_lines[line_n]}')


def clean_captures(captures, change):
    '''

    '''
    if isinstance(change['identifier'], str):
        step_size = 1
    elif isinstance(change['identifier'], list):
        step_size = len(change['identifier'])

    return captures[step_size-1::step_size]


if __name__ == '__main__':
    main()
