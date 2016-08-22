from setuptools import setup

setup(
    name='qgpkg',
    version='0.0.0',
    author='Pirmin Kalberer',
    author_email='pka@sourcepole.ch',
    packages=['qgisgpkg', 'qgpkg_cli'],
    url='https://github.com/pka/qgpkg',
    license='LICENSE.txt',
    description='Store QGIS map information in GeoPackages.',
    long_description=open('README.rst').read(),
    # tests_require=['nose'],
    # test_suite='nose.collector',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    entry_points={
        'console_scripts': ['ogr = gpkg_cli.gpkg:main'],
    }
    )
