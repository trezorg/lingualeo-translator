#!/usr/bin/env python
# -*- coding: utf8 -*-
"""Lingualeo API module."""
from __future__ import print_function
import os
import sys
import re
import codecs
import logging
import subprocess
from collections import (
    namedtuple,
    OrderedDict,
)
from functools import partial

import yaml
import requests
from six.moves import filter
from colorama import (
    init as colorama_init,
    Fore,
)

from .args import (
    prepare_parser,
    DEFAULT_CONFIG_FILENAME,
)

logging.basicConfig()
logger = logging.getLogger('lingualeo')
logger.setLevel(logging.DEBUG)

Translate = namedtuple(
    'Translate', 'exists, words, sound_url, transcription, custom')
BIG_RUSSIAN_ALPHABET = u'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
ALPHABET = set(
    BIG_RUSSIAN_ALPHABET +
    BIG_RUSSIAN_ALPHABET.lower() +
    u'-. '
)
AUTH_URL = 'http://api.lingualeo.com/api/login'
TRANSLATE_URL = 'http://api.lingualeo.com/gettranslates'
ADD_WORD_URL = 'http://api.lingualeo.com/addword'
DEFAULT_CONFIGS = [
    os.path.expanduser("~/{0}".format(DEFAULT_CONFIG_FILENAME)),
    os.path.join(os.path.curdir, DEFAULT_CONFIG_FILENAME)
]


def _print_color_line(text, color, new_line=True):
    message = u'{0}{1}{2}'.format(color, text, Fore.RESET)
    print(message, **({} if new_line else {'end': ' '}))


def _filter_config_files(*args):
    for filename in args:
        if filename and os.path.isfile(filename):
            yield filename


def _read_config(filename):
    try:
        fln = codecs.open(filename, encoding='utf-8')
        return yaml.load(fln.read())
    except Exception as err:
        logger.error(err)
        return {}


def _meld_configs(result, *options):
    result = result or {}
    for option in options:
        option = {k: v for k, v in option.items() if v}
        for key, value in option.items():
            if isinstance(value, (list, tuple)):
                values = result.get(key, [])
                values.extend(value)
                result[key] = list(set(values))
            elif isinstance(value, dict):
                values = result.get(key, {})
                values.update(value)
                result[key] = values
            else:
                result[key] = value
    return result


def _read_configs(*args):
    result = {}
    for filename in args:
        config = _read_config(filename)
        result = _meld_configs(result, config)
    return result


def _check_absent_options(options, names):
    return [name for name in names if name not in options]


def _check_options(options):
    absent_options = _check_absent_options(options, [
        'email',
        'password',
        'add',
        'word',
        'debug',
        'force',
        'sound',
    ])
    if absent_options:
        _print_color_line(
            'Absent parameters: {0}.\nYou should set them either in the'
            ' config file or in the command line.\n'.format(absent_options),
            Fore.RED)
        return False
    return True


def prepare_options():
    """Parse arguments."""
    parser = prepare_parser()
    args_options = {
        k: v for k, v in vars(parser.parse_args()).items() if v is not None
    }
    allowed_configs = DEFAULT_CONFIGS + [args_options.get("config")]
    config_files = list(_filter_config_files(*allowed_configs))
    options = _read_configs(*config_files)
    should_add = options.get('add')
    should_debug = options.get('debug')
    should_force = options.get('force')
    should_sound = options.get('sound')
    options.update(args_options)
    options['add'] = options['add'] or should_add
    options['debug'] = options['debug'] or should_debug
    options['force'] = options['force'] or should_force
    options['sound'] = options['sound'] or should_sound
    if not _check_options(options):
        parser.print_help()
        return
    return options


def make_request(url, session=None, method='GET', params=None, data=None):
    """Http request processing."""
    if session is None:
        session = requests.Session()
    handler = getattr(session, method.lower())
    return handler(url, params=params, data=data)


def debug_request(response):
    """Debug logging."""
    logger.debug('Status code: {0}\nResponse: {1}'.format(
        response.status_code, response.content))


def lingualeo_auth(func, email, password, debug=False):
    """Lingualeo auth processing."""
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


def fix_translate_string(word):
    """Translated word processing."""
    return re.sub(r'\s+\.\s*', u'. ', re.sub(r'\s+', u' ', word)).lower()


def print_translated_words(word, words, transcription=None):
    """Color printing."""
    _print_color_line(
        u'{0}{1}:'.format(
            word,
            u'' if not transcription else u' ({0})'.format(transcription)),
        Fore.GREEN
    )
    print(u'\n'.join(words))


def lingualeo_translate(func, word, debug=False):
    """Translating word."""
    translate_response = func(TRANSLATE_URL, params={'word': word})
    if debug:
        debug_request(translate_response)
    if translate_response.status_code != 200:
        _print_color_line(u'Cannot translate word {0}'.format(word), Fore.RED)
        return
    translate_json_response = translate_response.json()
    if translate_json_response.get('error_msg'):
        _print_color_line(translate_json_response['error_msg'], Fore.RED)
        return
    translates = translate_json_response['translate']
    if not translates:
        _print_color_line(u'Cannot translate word {0}'.format(word), Fore.RED)
        return
    is_exist = translate_json_response['is_user']
    sound_url = translate_json_response.get('sound_url')
    transcription = translate_json_response.get('transcription')
    vote_word_pairs = (
        (
            translate.get('votes', 0),
            fix_translate_string(
                u''.join(s for s in word if s in ALPHABET).strip())
        )
        for translate in translates
        for word in re.split(r'\s*?[:,;]+\s*?', translate['value'].strip())
    )
    sorted_words = (
        word for _, word in
        sorted(filter(lambda x: len(x[1]) > 1, vote_word_pairs), reverse=True)
    )
    # remove duplicates
    words = list(OrderedDict.fromkeys(sorted_words))
    _print_color_line(u'Found {0} word'.format(
        'existing' if is_exist else 'new'), Fore.RED)
    print_translated_words(word, words, transcription)
    return Translate(is_exist, words, sound_url, transcription, False)


def lingualeo_add(func, word, translate_response, debug=False):
    """Add wordto Lingualeo dictionary."""
    add_response = func(ADD_WORD_URL, method='POST', data={
        'word': word,
        'tword': u', '.join(translate_response.words)
    })
    if debug:
        debug_request(add_response)
    if add_response.status_code != 200:
        _print_color_line(u'Cannot add word {0}'.format(word), Fore.RED)
        return
    add_json_response = add_response.json()
    if add_json_response.get('error_msg'):
        _print_color_line(add_json_response['error_msg'], Fore.RED)
        return
    _print_color_line(u'{0} {1} word'.format(
        'Updated' if translate_response.exists else 'Added',
        'existing' if translate_response.exists else 'new'
    ), Fore.RED)
    if translate_response.custom:
        print_translated_words(
            word, translate_response.words, translate_response.transcription)
    return add_json_response


def lingualeo_play_sound(url, player):
    """Pronunciation of translated word."""
    params = player.split()
    params.append(url)
    with open(os.devnull, 'w') as fp:
        subprocess.Popen(
            params, stdout=fp, stderr=subprocess.STDOUT).wait()


def process_translating(word, email, password, player=None,
                        add=False, debug=False, force=False, sound=False,
                        translate=None):
    """Main translating function."""
    session = requests.Session()
    make_request_part = partial(make_request, session=session)
    colorama_init()
    auth_response = lingualeo_auth(make_request_part, email, password, debug)
    if auth_response is None:
        return
    translate_response = lingualeo_translate(make_request_part, word, debug)
    if translate_response is None:
        return
    if sound:
        if player is None:
            logger.warning(
                'You did not set a player either'
                ' in config file or with command line.'
                ' On example mplayer, mpg123')
        else:
            lingualeo_play_sound(translate_response.sound_url, player)
    if translate is not None:
        translate_response_dict = translate_response._asdict()
        translate_response_dict['custom'] = True
        translate_response = Translate(**translate_response_dict)
    if (add and
            (not translate_response.exists or force) and
            translate_response.words):
        return lingualeo_add(
            make_request_part, word, translate_response, debug)
    return translate_response


def main():
    """Enter point."""
    options = prepare_options()
    if options is None:
        sys.exit(1)
    result = process_translating(**options)
    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()
