import re


def match_var(var_name, value):
    if value.startswith('?!'):
        re.compile(value[2:])
        return f'(#not-match? @{var_name} "{value[2:]}")'
    else:
        re.compile(value)
        return f'(#match? @{var_name} "{value}")'
