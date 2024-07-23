from ._common import match_var


class GoQueries:

    def function(self, name):
        return f"""
            (call_expression
              function: [
                (selector_expression) @function
                (identifier) @function
              ]
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
