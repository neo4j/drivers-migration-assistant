from ._common import match_var


class GoQueries:

    def function(self, name):
        return f"""
            (call_expression
              function: [
                (selector_expression) @function_name
                (identifier) @function_name
              ]
              {match_var('function_name', name)}
            )
        """

    def method(self, name):
        return f"""
            (call_expression
              function: (selector_expression
                field: (field_identifier) @method_name
                {match_var('method_name', name)}
            ))
        """

    def type(self, name):
        return f"""
            (type
              (identifier) @type_name
              (#eq? @type_name "{name}"))
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
                (selector_expression) @function_name
                (identifier) @function_name
              ]
              arguments: (argument_list) @args
              {match_var('function_name', function_name)}
              {match_var('args', arg)}
            )
        """
