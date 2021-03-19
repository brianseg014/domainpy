
from setuptools import setup, find_packages


setup(
    name='domainpy',
    version='0.1.0',
    description='A library for DDD, ES, CQRS, TDD + BDD and microservices',
    author='Brian Estrada',
    author_email='brianseg014@gmail.com',
    packages=find_packages(),
    license='MIT',
    url='https://github.com/brianseg014/domainpy',
    download_url='https://github.com/brianseg014/domainpy/archive/v0.0.1.tar.gz',
    keywords=['ddd', 'event sourcing', 'CQRS'],
    install_requires=['boto3']
)
