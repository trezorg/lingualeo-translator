#!/usr/bin/python
from __future__ import print_function
import os
import sys
import codecs
import logging
import argparse
import yaml
import requests
from functools import partial
from colorama import init as colorama_init, Fore


logging.basicConfig()
logger = logging.getLogger('lingualeo')
logger.setLevel(logging.DEBUG)

AUTH_URL = 'http://api.lingualeo.com/api/login'
TRANSLATE_URL = 'http://api.lingualeo.com/gettranslates'
ADD_WORD_URL = 'http://api.lingualeo.com/addword'
DEFAULT_CONFIG_FILENAME = "lingualeo.yml"
DEFAULT_CONFIGS = [
    os.path.expanduser("~/{}".format(DEFAULT_CONFIG_FILENAME)),
    os.path.join(os.path.curdir, DEFAULT_CONFIG_FILENAME)
]
DESCRIPTION_TEXT = """
    Set mandatory arguments email, password either in a config file
    or in the command line. The config file can be set in the command line
    using the argument --config. Also the file {0} will be seek in
    the current directory and in the home directory of the current user.
    In the case of many config files are being found they will be meld in the
    next order (home directory, current directory, command line argument).
    Example of config file: lingualeo_config_example.yml
""".format(DEFAULT_CONFIG_FILENAME)


def _print_color_line(text, color, new_line=True):
    message = u'{}{}{}'.format(color, text, Fore.RESET)
    kwargs = {} if new_line else {'end': ' '}
    print(message, **kwargs)


def filter_config_files(*args):
    for filename in args:
        if filename and os.path.isfile(filename):
            yield filename


def read_config(filename):
    try:
        fln = codecs.open(filename, encoding='utf-8')
        return yaml.load(fln.read())
    except Exception as err:
        logger.error(err)
        return {}


def meld_configs(result, *options):
    result = result or {}
    for option in options:
        option = {k: v for k, v in option.items() if v}
        for key, value in option.items():
            if isinstance(value, (list, tuple)):
                values = result.get(key, [])
                values.extend(value)
                result[key] = list(set((values)))
            elif isinstance(value, dict):
                values = result.get(key, {})
                values.update(value)
                result[key] = values
            else:
                result[key] = value
    return result


def read_configs(*args):
    result = {}
    for filename in args:
        config = read_config(filename)
        result = meld_configs(result, config)
    return result


def check_absent_options(options, names):
    return [name for name in names if name not in options]


def check_options(options):
    absent_options = check_absent_options(options, [
        'email',
        'password',
        'add',
        'word',
        'debug',
    ])
    if absent_options:
        _print_color_line(
            'Absent parameters: {}.\nYou should set them either in the'
            ' config file or in the command line.\n'.format(absent_options),
            Fore.RED)
        return False
    return True


def check_config(filename):
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(
            'Filename is not exists: %s' % filename)
    return filename


def prepare_parser():
    """
    Handle the command line arguments
    """
    parser = argparse.ArgumentParser(
        prog="lingualeo",
        description="\n".join(
            [s.lstrip() for s in DESCRIPTION_TEXT.splitlines()]),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-e',
        '--email',
        required=False,
        action='store',
        dest='email',
        type=str,
        help='Lingualeo login email')

    parser.add_argument(
        '-p',
        '--password',
        required=False,
        action='store',
        dest='password',
        type=str,
        help='Lingualeo login password')

    parser.add_argument(
        '-c',
        '--config',
        required=False,
        action='store',
        dest='config',
        type=check_config,
        help='Config file')

    parser.add_argument(
        '-a',
        '--add',
        action='store_true',
        dest='add',
        default=False,
        help='Add to lingualeo dictionary')

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        dest='debug',
        default=False,
        help='Debug requests')

    parser.add_argument(
        'word',
        metavar='WORD',
        type=str,
        help='Word to translate')

    return parser


def prepare_options():
    parser = prepare_parser()
    args_options = {
        k: v for k, v in vars(parser.parse_args()).items() if v is not None
    }
    allowed_configs = DEFAULT_CONFIGS + [args_options.get("config")]
    config_files = list(filter_config_files(*allowed_configs))
    options = read_configs(*config_files)
    should_add = options.get('add')
    should_debug = options.get('debug')
    options.update(args_options)
    if should_add is True:
        options['add'] = True
    if should_debug is True:
        options['debug'] = True
    if not check_options(options):
        parser.print_help()
        return
    return options


def make_request(url, session=None, method='GET', params=None, data=None):
    if session is None:
        session = requests.Session()
    handler = getattr(session, method.lower())
    return handler(url, params=params, data=data)


def debug_request(response):
    logger.debug('Status code: {0}\nResponse: {1}'.format(
        response.status_code, response.content))


def lingualeo_auth(func, email, password, debug=False):
    auth_response = func(AUTH_URL, method='POST', data={
        'email': email,
        'password': password
    })
    if debug:
        debug_request(auth_response)
    if auth_response.status_code != 200:
        _print_color_line(
            u'Cannot authenticate against Lingualeo. Check email and password',
            Fore.RED)
        return
    auth_json_response = auth_response.json()
    if auth_json_response.get('error_msg'):
        _print_color_line(auth_json_response['error_msg'], Fore.RED)
        return
    return auth_json_response


def lingualeo_translate(func, word, debug=False):
    translate_response = func(TRANSLATE_URL, params={
        'word': word
    })
    if debug:
        debug_request(translate_response)
    if translate_response.status_code != 200:
        _print_color_line(u'Cannot translate word {}'.format(word), Fore.RED)
        return
    translate_json_response = translate_response.json()
    if translate_json_response.get('error_msg'):
        _print_color_line(translate_json_response['error_msg'], Fore.RED)
        return
    translate = translate_json_response['translate'][0]
    is_exist = translate["is_user"]
    tword = translate["value"]
    _print_color_line(u'{0} word'.format(
        'Existing' if is_exist else 'New'), Fore.WHITE, new_line=False)
    _print_color_line(u'{0}: {1}'.format(word, tword), Fore.GREEN)
    return translate


def lingualeo_add(func, word, tword, debug=False):
    add_response = func(ADD_WORD_URL, method='POST', data={
        'word': word,
        'tword': tword
    })
    if debug:
        debug_request(add_response)
    if add_response.status_code != 200:
        _print_color_line(u'Cannot add word {}'.format(word), Fore.RED)
        return
    add_json_response = add_response.json()
    if add_json_response.get('error_msg'):
        _print_color_line(add_json_response['error_msg'], Fore.RED)
        return
    _print_color_line(u'Added word {0} -> {1}'.format(word, tword), Fore.RED)
    return add_json_response


def main():
    options = prepare_options()
    if options is None:
        sys.exit(1)
    email = options['email']
    password = options['password']
    add = options['add']
    word = options['word']
    debug = options['debug']
    session = requests.Session()
    make_request_func = partial(make_request, session=session)
    colorama_init()
    auth_response = lingualeo_auth(make_request_func, email, password, debug)
    if auth_response is None:
        sys.exit(1)
    translate_response = lingualeo_translate(make_request_func, word, debug)
    if translate_response is None:
        sys.exit(1)
    if add:
        tword = translate_response['value']
        lingualeo_add(make_request_func, word, tword, debug)


if __name__ == "__main__":
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()
