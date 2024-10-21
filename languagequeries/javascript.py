from ._common import match_var


class JSQueries:

    def function(self, name):
        return f"""
            (call_expression
              function: (member_expression) @function
              {match_var('function', name)}
            )
        """

    def method(self, name):
        return self.property(name)

    def property(self, name):
        return f"""
            (member_expression
              property: (property_identifier) @property
              {match_var('property', name)}
            )
        """

    def function_arg(self, function_name, arg):
        return f"""
            (call_expression
              function: (member_expression) @function
              arguments: (arguments) @args
              {match_var('function', function_name)}
              {match_var('args', arg)}
            )
        """

    def _import_for_namespace(self):
        regex = '\\\\bneo4j-driver\\\\b'
        return f"""
            (variable_declarator
              name: (identifier) @alias
              value: (call_expression
                function: (identifier) @function_call
                arguments: (arguments) @name
                {match_var('function_call', 'require')}
                {match_var('name', regex)}
              ) @root
            )
        """

    def _parse_import_alias(self, match, source_lines):
        line = source_lines[match[1]['root'].range.start_point[0]]
        splitted = line.strip().split(' ')
        pkg_name = 'neo4j'  # no sub-packages in js
        imported_as = splitted[1]
        return pkg_name, imported_as
