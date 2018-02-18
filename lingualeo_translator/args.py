"""Args processing module."""
import os
import argparse


__all__ = (
    'prepare_parser',
    'DEFAULT_CONFIG_FILENAME',
)

DEFAULT_CONFIG_FILENAME = "lingualeo.yml"
DESCRIPTION_TEXT = """
    Set mandatory arguments email, password either in a config file
    or in the command line. The config file can be set in the command line
    using the argument --config. Also the file {0} will be seek in
    the current directory and in the home directory of the current user.
    In the case of many config files are being found they will be meld in the
    next order (home directory, current directory, command line argument).
    Example of config file: lingualeo_config_example.yml
""".format(DEFAULT_CONFIG_FILENAME)


def check_config(filename):
    """Check config existence."""
    if not os.path.isfile(filename):
        raise argparse.ArgumentTypeError(
            'Filename is not exists: {0}'.format(filename))
    return filename


def prepare_parser():
    """Handle the command line arguments."""
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
        '-s',
        '--sound',
        action='store_true',
        dest='sound',
        default=False,
        help='Play words pronounciation')

    parser.add_argument(
        '-d',
        '--debug',
        action='store_true',
        dest='debug',
        default=False,
        help='Debug requests')

    parser.add_argument(
        '-f',
        '--force',
        action='store_true',
        dest='force',
        default=False,
        help='Force add words')

    parser.add_argument(
        '--player',
        required=False,
        action='store',
        dest='player',
        type=str,
        help='Media player for word pronounciation')

    parser.add_argument(
        '-t',
        '--translate',
        required=False,
        nargs='+',
        action='store',
        dest='translate',
        type=str,
        help='Set custom translate')

    parser.add_argument(
        'word',
        metavar='WORD',
        type=str,
        nargs='+',
        help='Word to translate')

    return parser
