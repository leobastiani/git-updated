import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="git-updated",
    version="1.0.4",
    author="Leonardo Guarnieri de Bastiani",
    author_email="leogbastiani@gmail.com",
    description="Check if your local packages are up to date with origin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leobastiani/git-updated",
    install_requires=[
        'docopt',
        'pathlib',
        'colorama',
        'tabulate',
        'tqdm'
    ],
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': ['git-updated=git_updated:main'],
    },
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ]
)
