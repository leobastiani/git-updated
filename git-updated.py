#!python3
#encoding=utf-8

"""Usage:
  git-updated <path>... [options]

Options:
  -h --help   Show this screen.
  -d --debug  Show version.
"""
from __future__ import print_function, division, absolute_import
from docopt import docopt
import sys
from pathlib import Path
import subprocess
import colorama
import os
import glob
import contextlib
import glob

colorama.init(autoreset=True)

arguments = docopt(__doc__)
DEBUG = arguments['--debug'] or sys.flags.debug
def debug(*args):
    if DEBUG:
        print(*args)

# https://stackoverflow.com/a/42441759
@contextlib.contextmanager
def working_directory(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(prev_cwd)

def command(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

def printRepo(path, **kwargs):
    print('Repository\t%s' % (path.absolute()), **kwargs)

def check_repository(path):
    with working_directory(path):
        if not (path / '.git').is_dir():
            printRepo(path, end='\t')
            print(colorama.Fore.RED + "ins't a repository")
            return 1
        if command('git status -s'):
            printRepo(path, end='\t')
            print(colorama.Fore.RED + "has files that aren't commited.")
            return 2
        command('git fetch')
        output = command('git log --branches --not --remotes')
        if output:
            printRepo(path, end='\t')
            print(colorama.Fore.RED + "should be pushed")
            return 3
        printRepo(path, end='\t')
        print(colorama.Fore.GREEN + 'OK!')
        return 0

def main():
    for path in arguments['<path>']:
        if '*' in path:
            for p in glob.glob(path):
                p = Path(p)
                if p.is_dir():
                    last_ret = check_repository(p)
                    if last_ret:
                        ret = last_ret
        else:
            return check_repository(Path(path))

if __name__ == '__main__':
    sys.exit(main())
