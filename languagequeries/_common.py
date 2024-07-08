import re


def match_var(var_name, value):
    re.compile(value)
    return f'(#match? @{var_name} "{value}")'
