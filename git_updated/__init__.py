#!python3
#encoding=utf-8

"""Usage:
  git-updated <path>... [options]
  git-updated --full [options]

Options:
  -h --help   Show this screen.
  -d --debug  Show version.
  -f --full  Scan the entire PC.
"""
from __future__ import print_function, division, absolute_import
from docopt import docopt
import sys
from pathlib import Path
import subprocess
import colorama
import os
import re
import glob
import contextlib
from tabulate import tabulate
from tqdm import tqdm
import tempfile

colorama.init(autoreset=True)

arguments = docopt(__doc__)
DEBUG = arguments['--debug'] or sys.flags.debug
IGNORE = [
    Path(tempfile.gettempdir()),
    Path('C:\\$GetCurrent'),
    Path('C:\\$Recycle.Bin'),
    Path('C:\\$Windows.~WS'),
    Path('C:\\$WinREAgent'),
    Path('C:\\System Volume Information'),
    Path('C:\\Windows'),
    Path('C:\\Windows10Upgrade'),
]

def debug(*args):
    if DEBUG:
        print(*args)

def is_subdir(p1, p2):
    """check if p1 is p2 or its subdirectory
    :param str p1: subdirectory candidate
    :param str p2: parent directory
    :returns True if p1,p2 are directories and p1 is p2 or its subdirectory"""
    if os.path.isdir(p1) and os.path.isdir(p2):
        p1, p2 = os.path.realpath(p1), os.path.realpath(p2)
        return p1 == p2 or p1.startswith(p2+os.sep)
    else:
        return False

def isIgnoring(path):
    for ignoringPath in IGNORE:
        if path == ignoringPath: return True
        if is_subdir(path, ignoringPath): return True
        if re.search(r'[\\/]node_modules[\\/]', str(path)): return True
    return False

class Repo:
    def __init__(self, path):
        self.path = path.absolute()
        self.result = -1
        self.command = ''
        self.report = ''
        debug(self)

    def setReport(self, color, message):
        self.report = color + message + colorama.Style.RESET_ALL

    def setCommand(self, command):
        self.command = f'pushd "{self.path.absolute()}" && {command} && popd'

    def __repr__(self):
        return f'Repo(path: {repr(self.path)}, result: {repr(self.result)}, command: {repr(self.command)}, report: {repr(self.report)})'

    def check_repository(self):
        def _check_repository():
            if not self.path.exists() or not self.path.is_dir():
                self.setReport(colorama.Fore.RED, "directory doesn't exist")
                return 0
            with working_directory(self.path):
                dotDirString = command('git rev-parse --show-toplevel')
                dotDirPath = last_exit_code == 0 and Path(dotDirString)
                if dotDirPath != self.path:
                    self.setReport(colorama.Fore.RED, "ins't a repository")
                    return 1
                if command('git status -s'):
                    self.setReport(colorama.Fore.RED, "has files that aren't commited.")
                    self.setCommand('git status')
                    return 2
                command('git fetch')
                output = command('git log --branches --not --remotes')
                if output:
                    self.setReport(colorama.Fore.RED, "should be pushed")
                    self.setCommand('git log --branches --not --remotes')
                    return 3
            self.setReport(colorama.Fore.GREEN, "OK!")
            return 0

        self.result = _check_repository()
        return self.result


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
last_exit_code = 0
def command(cmd):
    debug(f"[{Path.cwd()}]: {cmd}")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    last_exit_code = res.returncode
    return res.stdout.decode('utf-8').strip()

def main():
    repos = []

    for path in arguments['<path>']:
        if '*' in path:
            for p in glob.iglob(path, recursive=True):
                path = Path(p).absolute()
                if path.is_dir() and not isIgnoring(path):
                    repos.append(Repo(Path(path)))
        else:
            repos.append(Repo(Path(path)))

    pbar = tqdm(repos)
    for repo in pbar:
        pbar.set_description(str(repo.path.absolute()))
        repo.check_repository()
    print()

    print(tabulate([[str(repo.path.absolute()), repo.report] for repo in repos]))

    commands = [repo.command for repo in repos if repo.command]
    if commands:
        print('\nRun the following commands:')
        for c in commands:
            print(f'\t{c}')

    return max([repo.result for repo in repos])

if __name__ == '__main__':
    if arguments['--full']:
        print('Searching for repos...')
        arguments['<path>'] = [str(Path(x).parents[0]) for x in glob.iglob(str(Path('/**/.git').absolute()), recursive=True)]
    sys.exit(main())
