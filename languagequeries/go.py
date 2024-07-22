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

    def import_from_statement__module_name(self, name):
        return f"""
            (import_from_statement
              module_name: (dotted_name) @module_name
              (#eq? @module_name "{name}")
            )
        """

    def import_from_statement__name(self, module_name, name):
        return f"""
            (import_from_statement
              module_name: (dotted_name) @module_name
              (#eq? @module_name "{module_name}")
              name: (dotted_name) @name
              (#eq? @name "{name}")
            )
        """

    def import_statement__name(self, name):
        return f"""
            (import_statement
              name: (dotted_name) @name
              (#eq? @name "{name}")
            )
        """

    def method__kwarg(self, method_name, kwarg_name):
        return f"""
            (call
              function: (attribute
                attribute: (identifier) @method_name
                (#eq? @method_name "{method_name}")
              )
              arguments: (argument_list
                (keyword_argument
                  name: (identifier) @kwarg_name
                  (#eq? @kwarg_name "{kwarg_name}")
                )
              )
            )
        """
