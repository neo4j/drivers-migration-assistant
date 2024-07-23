import re
from tree_sitter import Language, Parser


'''
Backslashes in ts_patterns should be escaped twice.
Backslashes in re_patterns should be escaped once.
Example:

"patterns": [
  {
    "ts_pattern": [
      "?!config\\.Config",
      "\\\\bConfig\\\\b"
     ],
    "ts_type": "type",
    "re_pattern": "\\b(?<!config\\.)Config\\b"
  }
]
'''


class TreeSitterParser:

    def __init__(self, language_name):
        if language_name == 'python':
            import tree_sitter_python as tslang
            from languagequeries.python import PythonQueries
            self.queries = PythonQueries()
        elif language_name == 'go':
            import tree_sitter_go as tslang
            from languagequeries.go import GoQueries
            self.queries = GoQueries()
        else:
            raise ValueError('Invalid language. Valid choices are: python, java, go, javascript, dotnet.')

        self.language = Language(tslang.language())

    def set_source(self, source):
        self.source = source
        self.ast = Parser(self.language).parse(bytes(self.source.text, 'utf8'))

    def get_captures_for_pattern(self, pattern):
        if pattern.get('ts_pattern') == None:
            return []

        if isinstance(pattern['ts_pattern'], str):
            query = getattr(self.queries, pattern['ts_type'])(pattern['ts_pattern'])
        elif isinstance(pattern['ts_pattern'], list):
            query = getattr(self.queries, pattern['ts_type'])(*pattern['ts_pattern'])
        else:
            raise ValueError('Change identifier must be str or list.')

        matches = self.language.query(query)
        if pattern.get('ts_uniqueify') != None and pattern.get('ts_uniqueify') == 'True':
            captures = self.uniqueify_captures(matches.captures(self.ast.root_node), pattern)
        else:
            captures = matches.captures(self.ast.root_node)
        return [(c[0].range.start_point, c[0].range.end_point) for c in captures]  # only extract relevant bits

    def uniqueify_captures(self, captures, pattern):
        '''
        Pattern change entries consisting of a list yield as many matches as
        list elements, from tree-sitter. (Normally?) Only the last match is relevant.
        '''
        if isinstance(pattern['ts_pattern'], str):
            step_size = 1
        elif isinstance(pattern['ts_pattern'], list):
            step_size = len(pattern['ts_pattern'])

        return captures[step_size-1::step_size]


class RegexParser:

    def set_source(self, source):
        self.source = source

    def get_captures_for_pattern(self, pattern):
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
