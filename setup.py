import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='bkref',
    version='0.0.1',
    author='John Ensley',
    author_email='johnensley17@gmail.com',
    description='Scrape data from Basketball Reference',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ensley/bkref',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    install_requires=[
        'click',
        'beautifulsoup4',
        'pandas',
        'requests',
        'lxml',
    ],
    entry_points='''
        [console_scripts]
        bkref=bkref.script:cli
    ''',
)
