
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
    install_requires=['boto3==1.17.109'],
    extras_require={
        'dev': [
            'moto[dynamodb,sqs,sns,events]==2.0.10',
            'pytest==6.2.4',
            'coverage==5.5'
        ],
        'doc': [
            'sphinx==4.1.1'
        ]
    }
)
