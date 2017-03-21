from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

test_deps = ['mock', 'pytest', 'pytest-cov', 'pytest-xdist']

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cfn-resource-timeout',
    version='0.2.2',
    description=(
        'Wrapper decorators for building CloudFormation custom resources'
    ),
    long_description=long_description,
    url='https://github.com/timeoutdigital/cfn-resource-timeout',
    author='Ryan Scott Brown',
    author_email='sb@ryansb.com',
    maintainer='Adam Johnson',
    maintainer_email='adamjohnson@timeout.com',
    license='MIT',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='cloudformation aws cloud custom resource amazon',
    py_modules=["cfn_resource"],
    install_requires=[],
    extras_require={
        'test': test_deps,
    },
    package_data={},
    data_files=[],
    entry_points={},
)
