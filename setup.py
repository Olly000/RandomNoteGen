from setuptools import setup

setup(
    name='RandomNoteGen',
    version='0.1',
    packages=['RandomNoteGen'],
    url='https://github.com/Olly000/RandomNoteGen',
    license='',
    author='Olly000',
    author_email='',
    description='Generates random MIDI notes.',
    install_requires=[
        'mido',
        'pygame'
    ]
)
