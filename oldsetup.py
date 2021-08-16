#NOT CURRENTLY IN USE. Kept as an artifact for reference if needed.
from setuptools import setup, find_packages

setup(
    name='sparky',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'keyring',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        sparky=main:cli
    ''',
)