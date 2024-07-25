from ._common import match_var


class GoQueries:

    def function(self, name):
        return f"""
            (call_expression
              function: (selector_expression) @function
              {match_var('function', name)}
            )
        """

    def method(self, name):
        return f"""
            (call_expression
              function: (selector_expression
                field: (field_identifier) @method
                {match_var('method', name)}
            ))
        """

    def property(self, name):
        return f"""
            (selector_expression
              field: (field_identifier) @property
              {match_var('property', name)}
            )
        """

    def type(self, *args):
        '''
        Allows for complex type queries, such as
        (_
          type: (_) @type_name
          (#match? @type_name "Config")
          (#not-match? @type_name "config\\.Config")
        )
        '''
        conditions = ''
        for arg in args:
            conditions += f'''{match_var('type', arg)}
              '''
        return f"""
            (_
              type: (_) @type
              {conditions}
            )
        """

    def import_dec(self, name):
        return f"""
            (import_spec
              path: (interpreted_string_literal) @name
              {match_var('name', name)}
            )
        """

    def function_arg(self, function_name, arg):
        return f"""
            (call_expression
              function: [
                (selector_expression) @function
                (identifier) @function
              ]
              arguments: (argument_list) @args
              {match_var('function', function_name)}
              {match_var('args', arg)}
            )
        """

    def _import_for_namespace(self):
        regex = '\\\\bneo4j\\\\b'
        return f"""
            (import_spec
              name: (package_identifier)? @alias
              path: (interpreted_string_literal) @name
              {match_var('name', regex)}
            ) @root
        """

    def _parse_import_alias(self, match, source_lines):
        line = source_lines[match[1]['root'].range.start_point[0]]
        splitted = line.strip()[1:-1].split('/')
        pkg_name = splitted[-1]
        imported_as = splitted[-1]
        if match[1].get('alias') != None:
            imported_as = line[match[1]['alias'].range.start_point[1]:match[1]['alias'].range.end_point[1]]
        return pkg_name, imported_as
