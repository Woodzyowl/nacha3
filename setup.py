import re
import setuptools.command.test


class PyTest(setuptools.command.test.test):

    def finalize_options(self):
        setuptools.command.test.test.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        import pytest

        pytest.main(self.test_args)


extras_require = {
    'tests': [
        'pytest >=2.5,<3.0',
        'pytest-cov >=1.7,<2.0',
        'unittest2 >=0.5.1,<0.6',
    ],
}

setuptools.setup(
    name='py-nacha',
    version=(
        re
        .compile(r".*__version__ = '(.*?)'", re.S)
        .match(open('nacha/__init__.py').read())
        .group(1)
    ),
    url='https://github.com/DisruptiveLabs/nacha',
    author='DisruptiveLabs',
    author_email='team+nacha@comanage.com',
    description='NACHA File Generation',
    long_description=open('README.rst', 'r').read(),
    platforms='any',
    include_package_data=True,
    install_requires=[
        'bryl'
    ],
    extras_require=extras_require,
    tests_require=extras_require['tests'],
    packages=setuptools.find_packages('.', exclude=('tests', 'tests.*')),
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='nose.collector',
)
