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

class Repo:
    def __init__(self, path):
        self.path = path
        self.result = -1
        self.command = ''
        self.report = ''

    def check_repository(self):
        if not self.path.exists() or not self.path.is_dir():
            self.report = colorama.Fore.RED + "directory doesn't exist" + colorama.Style.RESET_ALL
            self.result = 1
            return self.result

        with working_directory(self.path):
            if not Path('.git').is_dir():
                self.report = colorama.Fore.RED + "ins't a repository" + colorama.Style.RESET_ALL
                self.result = 2
                return self.result

            if command('git status -s'):
                self.report = colorama.Fore.RED + "has files that aren't commited." + colorama.Style.RESET_ALL
                self.command = f'pushd "{self.path.absolute()}" && git status && popd'
                self.result = 3
                return self.result

            command('git fetch')
            output = command('git log --branches --not --remotes')
            if output:
                self.report = colorama.Fore.RED + "should be pushed" + colorama.Style.RESET_ALL
                self.command = f'pushd "{self.path.absolute()}" && git log --branches --not --remotes && popd'
                self.result = 4
                return self.result

            self.report = colorama.Fore.GREEN + "OK!" + colorama.Style.RESET_ALL
            self.result = 0
            return self.result

    def __repr__(self):
        return f'Repo(path: {repr(self.path)}, result: {repr(self.result)}, command: {repr(self.command)}, report: {repr(self.report)})'


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

def main():
    repos = []

    for path in arguments['<path>']:
        if '*' in path:
            for p in glob.glob(path):
                path = Path(p).absolute()
                if path.is_dir():
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
    sys.exit(main())
