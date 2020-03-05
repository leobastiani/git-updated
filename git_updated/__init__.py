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
from tabulate import tabulate
from tqdm import tqdm

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

# list of commands to run at the end
commands = []

def command(cmd):
    debug(f"[{Path.cwd()}]: {cmd}")
    return subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8').strip()

# reports to show in the end
reports = []
def addReport(path, color, message):
    reports.append([path, color + message + colorama.Style.RESET_ALL])

def check_repository(path):
    with working_directory(path):
        if not Path('.git').is_dir():
            addReport(path, colorama.Fore.RED, "ins't a repository")
            return 1
        if command('git status -s'):
            addReport(path, colorama.Fore.RED, "has files that aren't commited.")
            commands.append(f'pushd {path} && git status && popd')
            return 2
        command('git fetch')
        output = command('git log --branches --not --remotes')
        if output:
            addReport(path, colorama.Fore.RED, "should be pushed")
            commands.append(f'pushd {path} && git log --branches --not --remotes && popd')
            return 3
        addReport(path, colorama.Fore.GREEN, "OK!")
        return 0

def main():
    paths = []
    ret = 0

    for path in arguments['<path>']:
        if '*' in path:
            for p in glob.glob(path):
                path = Path(p).absolute()
                if path.is_dir():
                    paths.append(path)
        else:
            paths.append(Path(path).resolve())

    pbar = tqdm(paths)
    for path in pbar:
        pbar.set_description(str(path))
        last_ret = check_repository(path)
        if last_ret:
            ret = last_ret

    print(tabulate(reports))

    if commands:
        print('\nRun the following commands:')
        for c in commands:
            print(f'\t{c}')

    return ret

if __name__ == '__main__':
    sys.exit(main())
