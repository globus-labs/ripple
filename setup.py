from setuptools import setup

readme_text = ''
with open('README.rst', 'r') as f:
    readme_text = f.read()

setup(
    name='ripple',
    version='1.0.2',
    author='ryan',
    install_requires=['sqlalchemy', 'psycopg2', 'boto3', 'watchdog'],
    packages=['ripple', 'ripple.observers', 'ripple.observers.posix',
              'ripple.runners', 'ripple.runners.shell',
              'ripple.runners.slurm',
              'ripple.observers.lustre'],
    package_data={'': ['*.ini']},
    entry_points={'console_scripts':
                  ['ripple = ripple.cli:main']},

    long_description=readme_text
)
