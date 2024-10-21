import re
from tree_sitter import Language, Parser


'''
Backslashes in ts_patterns should be escaped twice.
Backslashes in re_patterns should be escaped once.
Example:

"patterns": [
  {
    "ts_pattern": [
      "?!config\\\\.Config",
      "\\\\bConfig\\\\b"
     ],
    "ts_type": "type",
    "re_pattern": "\\b(?<!config\\.)Config\\b"
  }
]
'''


def format_pattern_string(pattern_s, change, namespaces):
    if change.get('namespace') != None:
        if namespaces.get(change['namespace']) != None:
            pattern_s = pattern_s.replace('{{namespace}}', namespaces.get(change['namespace']))
        else:
            pattern_s = pattern_s.replace('{{namespace}}', change['namespace'])

    if '{namespace}}' in pattern_s:
        raise ValueError(f'Pattern regex `{pattern_s}` contains `{{{{namespace}}}}` but namespace not given in json entry')

    return pattern_s


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
        elif language_name == 'javascript':
            import tree_sitter_javascript as tslang
            from languagequeries.javascript import JSQueries
            self.queries = JSQueries()
        else:
            # click should prevent ever getting here
            raise ValueError('Invalid language. Valid choices are: python, go, javascript.')

        self.language = Language(tslang.language())

    def set_source(self, source):
        self.source = source
        self.ast = Parser(self.language).parse(bytes(self.source.text, 'utf8'))
        self.namespaces = self.build_namespaces_dict()

    def get_captures_for_pattern(self, pattern, change):
        if pattern.get('ts_pattern') == None:
            return []

        if isinstance(pattern['ts_pattern'], str):
            pattern_formatted = format_pattern_string(pattern['ts_pattern'], change, self.namespaces)
            query = getattr(self.queries, pattern['ts_type'])(pattern_formatted)
        elif isinstance(pattern['ts_pattern'], list):
            pattern_formatted = [format_pattern_string(p, change, self.namespaces) for p in pattern['ts_pattern']]
            query = getattr(self.queries, pattern['ts_type'])(*pattern_formatted)
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

    def build_namespaces_dict(self):
        namespaces_d = {}
        ast = self.ast
        try:
            query = self.queries._import_for_namespace()
        except AttributeError:  # python not implemented
            return namespaces_d
        matches = self.language.query(query).matches(ast.root_node)
        for m in matches:
            if m[1] == {}:
                continue
            pkg_name, imported_as = self.queries._parse_import_alias(m, self.source.lines)
            namespaces_d[pkg_name] = imported_as
        return namespaces_d

class RegexParser:

    def set_source(self, source):
        self.source = source

    def get_captures_for_pattern(self, pattern, change):
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
