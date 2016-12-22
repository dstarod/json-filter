#!/usr/bin/env python3

import json
import sys
import argparse
import re
from argparse import RawTextHelpFormatter

enabled_colors = False
try:
    from pygments import highlight
    from pygments.lexers import JsonLexer
    from pygments.formatters import TerminalFormatter
    enabled_colors = True
except ImportError:
    pass

# TODO https://docs.mongodb.com/v3.0/reference/operator/query/
# Element: $type
# Evaluation: $mod, $text, $where
# Geospatial: $geoWithin, $geoIntersects, $near, $nearSphere
# Array: $all, $elemMatch
# Comments?
# Projection Operators?

NOT_FOUND = '$FiElD%N0T!F0uND&'

# Regex cache
regexps = {}


def exp_regexp(search_string, regex_string):
    """
    Regex filter function
    :param search_string: str
    :param regex_string: str
    :return: bool
    """
    if search_string is NOT_FOUND:
        return False
    if regex_string not in regexps:
        try:
            regexps[regex_string] = re.compile(regex_string)
        except Exception:
            print(error_json("Can't recognize regex {}".format(regex_string)))
            exit(1)

    try:
        result = re.match(regexps[regex_string], str(search_string))
    except Exception:
        print(error_json("Can't match value <{}> by regex {}".format(
            search_string, regex_string)
        ))
        exit(1)

    return result


expressions = {
    # Comparison
    "$gt": lambda x, y: x is not NOT_FOUND and x > y,
    "$gte": lambda x, y: x is not NOT_FOUND and x >= y,
    "$eq": lambda x, y: x is not NOT_FOUND and x == y,
    "$lt": lambda x, y: x is not NOT_FOUND and x < y,
    "$lte": lambda x, y: x is not NOT_FOUND and x <= y,
    "$ne": lambda x, y: x is not NOT_FOUND and x != y,
    "$in": lambda x, y: x is not NOT_FOUND and (set(x) & set(y) if type(x) == list else x in y),
    "$nin": lambda x, y: x is not NOT_FOUND and (not set(x) & set(y) if type(x) == list else x not in y),
    # Element
    "$exists": lambda x, y: x is not NOT_FOUND if y else x is NOT_FOUND,
    # Evaluation
    "$regex": exp_regexp,
    # Array
    "$size": lambda x, y: x is not NOT_FOUND and len(x) == y
}


def get_value(path, data):
    """
    Returns dict value by complex path
    :param path: str - complex path, like "jam.tool" -> {"jam": {"tool": true}}
    :param data: dict
    :return: value or NOT_FOUND
    """
    step = data
    path_parts = path.split('.')
    for path_num, path_part in enumerate(path_parts):
        if path_part not in step:
            # Next path part not found
            return NOT_FOUND

        step = step[path_part]

        if type(step) != dict:
            if path_num < len(path_parts)-1:
                # Found path shorter than expected
                return NOT_FOUND
            return step

    return NOT_FOUND


def gen_lambda(filter_key, filter_value, exp_name='$eq'):
    """
    Generate lambdas set for filters rules
    :param filter_key: str
    :param filter_value: str or dict
    :param exp_name: str - key of the expressions dict
    :return: lambda function
    """

    exp = expressions.get(exp_name, expressions['$eq'])

    if filter_key == '$not' and type(filter_value) == dict:
        return lambda x: not any([
            gen_lambda(fname, frule)(x)
            for fname, frule in filter_value.items()
        ])

    if type(filter_value) == dict:
        return lambda x: all([
            gen_lambda(filter_key, filter_rule, exp_name)(x)
            for exp_name, filter_rule in filter_value.items()
        ])

    if filter_key == '$and' and type(filter_value) == list:
        return lambda x: all([
            gen_lambda(k, v)(x)
            for f in filter_value for k, v in f.items()
        ])

    if filter_key == '$or' and type(filter_value) == list:
        return lambda x: any([
            gen_lambda(k, v)(x)
            for f in filter_value for k, v in f.items()
        ])

    if filter_key == '$nor' and type(filter_value) == list:
        return lambda x: not any([
            gen_lambda(fd_name, fd_value)(x)
            for filter_dict in filter_value
            for fd_name, fd_value in filter_dict.items()
        ])

    return lambda x: exp(
        get_value(filter_key, x),
        filter_value
    )


def make_filter_chain(data, filters):
    """
    Create filter chain based on initial data and filters
    :param data: list - initial data
    :param filters: dict - filters
    :return: filter
    """
    # TODO: $and, $or, $not, $nor
    return filter(
        lambda x: all([
            gen_lambda(field_name, filter_value)(x)
            for field_name, filter_value in filters.items()
        ]),
        data
    )


def flatten(items, empty=[]):
    """
    Flat nested arrays
    :param items: list - nested list
    :param empty: list - flat list
    :return: list - flat list
    """
    for i in items:
        if type(i) == list:
            flatten(i, empty)
        else:
            empty.append(i)
    return empty


def compact_json(data):
    """
    Returns JSON-dumped dict
    :param data:
    :return:
    """
    return json.dumps(
        data,
        ensure_ascii=False, indent=4, separators=(',', ': '), sort_keys=True
    )


def error_json(message):
    return compact_json({'error': message})


def pretty_printable(iterable_data, colorize=False):
    """
    Pretty printing JSON document
    :param iterable_data: filter or list
    :param colorize: bool - colorize output if possible
    """
    result = compact_json(list(iterable_data))
    if colorize and not enabled_colors:
        return error_json("Can't import pygments module")

    if colorize:
        return highlight(result, JsonLexer(), TerminalFormatter())

    return result


if __name__ == '__main__':
    """
    Data:
        Make sure data type is list. Flatten it if need.
        Make sure every element type is dict.
        Filter list of dicts by filters rules.
    Filters:
        Make sure filters type is dict.
        For every field get key as rule name and value as rule for field.
        Make filter with cascade lambdas for every rule
    """

    parser = argparse.ArgumentParser(description='''
    JAM: JSON Mongo-like filter
    How to use:
    wget -qO - "http://rest.com/data" | jam -f \\
    '{"success": false, "errors": {"$size": 2}}'
    ''', formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        '-f', '--filter', type=str, help='Allowed filters: {}'.format(
            ', '.join(expressions.keys())
        )
    )
    parser.add_argument(
        '-ff', '--filter-file', type=str, default='',
        help='File path to filters JSON'
    )
    parser.add_argument(
        '-k', '--key', type=str, default='',
        help='Array field name for incoming map-like JSON'
    )
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='Colorize output (required pygments)'
    )
    args = parser.parse_args()

    data = json.loads(sys.stdin.read())
    filters = {}

    if args.filter_file:
        try:
            with open(args.filter_file) as f:
                filters.update(json.load(f))
        except:
            print(error_json("Can't load filters from file {}".format(
                args.filter_file
            )))
            exit(1)

    if args.filter:
        try:
            filters.update(json.loads(args.filter))
        except Exception as e:
            print(
                error_json(
                    "Can't recognize filters from --filter argument: {}".format(
                        args.filter)))
            exit(1)

    if args.key and type(data) == dict and args.key in data:
        data = data.get(args.key)

    if type(data) != list:
        print(error_json('Expected list, got {}'.format(type(data))))
        exit(1)

    data = flatten(data)

    fset = make_filter_chain(data, filters)
    print(pretty_printable(fset, args.color))
