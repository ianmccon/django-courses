from setuptools import setup, find_packages
 
setup(
    name='django-courses',
    version='0.1.0',
    description='Course',
    author='Hisham Zarka',
    author_email='hzarka@gmail.com',
    url='http://github.com/hzarka/django-courses/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    install_requires=['setuptools', 'BeautifulSoup'],
    package_data = {
        'courses': [
            'fixtures/*.json',
        ],
    },
    zip_safe=False,
)
