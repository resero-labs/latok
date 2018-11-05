import versioneer
import sys

from os import path


def configuration(parent_package='', top_path=None):
    from numpy.distutils.misc_util import Configuration

    config = Configuration('latok',
                           parent_package,
                           top_path)
    config.add_extension('latok',
                         [
                             'latok/core/src/latok/latok.c'
                         ],
                         include_dirs=['latok/core/src/latok'])

    return config


if __name__ == "__main__":

    args = sys.argv[1:]

    run_build = True
    other_commands = ['egg_info', 'install_egg_info', 'rotate']
    for command in other_commands:
        if command in args:
            run_build = False

    here = path.abspath(path.dirname(__file__))
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()

    metadata = dict(
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description = 'Document Clustering',
        long_description = long_description,
        url='https://hq-stash.corp.proofpoint.com/scm/tresero/latok.git',
        author = "Proofpoint-Labs",
        author_email='resero-labs@proofpoint.com',
        license = 'MIT',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            # Set this topic to what works for you
            'Topic :: Python :: Library',
            # Pick your license as you wish (should match "license" above)
            'License :: MIT',
            'Programming Language :: Python :: 3.6',
        ],
        platforms = ["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
        configuration=configuration,
        install_requires=[
            "numpy==1.15.3",
            "dataclasses==0.6",
        ],
        extras_require={
            'dev': [
                'wheel'
                'vmprof'
            ],
            'test': [
                'pylint',
                'pytest',
                'pytest-cov',
            ],
        },
        setup_requires=[
            'numpy>=0.15.0',
        ]
    )

    # This import is here because it needs to be done before importing setup()
    # from numpy.distutils, but after the MANIFEST removing and sdist import
    # higher up in this file.
    from setuptools import setup

    if run_build:
        from numpy.distutils.core import setup
        metadata['configuration'] = configuration
    else:
        # Don't import numpy here - non-build actions are required to succeed
        # without Numpy for example when pip is used to install Scipy when
        # Numpy is not yet present in the system.
        metadata['name'] = 'latok'

    setup(**metadata)
