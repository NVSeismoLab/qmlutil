from setuptools import setup

s_args = {
    'name': 'qmlutil',
    'version': '0.3.1',
    'description': 'QuakeML utils for python',
    'author': 'Mark Williams',
    'maintainer': 'Nevada Seismological Laboratory',
    'url': 'https//github.com/NVSeismoLab/qmlutil',
    'packages': [
        'qmlutil',
        'qmlutil.aux',
        'qmlutil.css',
        'qmlutil.data',  # TODO: add static files IMPORTANT!!
        'qmlutil.lib',
        'qmlutil.ichinose',
    ],
    'package_data': {
        'qmlutil' : [
            'data/*.rng',
            'lib/README',
        ],
    },
}

setup(**s_args)

