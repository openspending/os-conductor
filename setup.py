from setuptools import setup, find_packages

__version__ = '0.0.1'

setup(
    name='os_conductor',
    version=__version__,
    description='Conductor for OpenSpending',
    long_description='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='api fiscal datapackage babbage openspending',
    author='OpenSpending',
    author_email='info@openspending.org',
    url='https://github.com/openspending/os-conductor',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'test']),
    namespace_packages=[],
    package_data={
        '': ['*.json'],
    },
    zip_safe=False,
    install_requires=[
        # We're using requirements.txt
    ],
    tests_require=[
        'tox',
    ]
)
