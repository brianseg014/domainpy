
from setuptools import setup, find_packages


setup(
    name='domainpy',
    version='0.2.0',
    description='A library for DDD, ES, CQRS, TDD + BDD and microservices',
    author='Brian Estrada',
    author_email='brianseg014@gmail.com',
    packages=find_packages(),
    license='MIT',
    url='https://github.com/mymamachef/domainpy',
    download_url='https://github.com/mymamachef/domainpy/archive/v0.2.0.tar.gz',
    keywords=['ddd', 'event sourcing', 'CQRS'],
    install_requires=[
        'boto3==1.17.109',
        'typeguard==2.12.1',
        'typing_extensions==3.10.0.0 ; python_version<="3.7"'
    ]
)
