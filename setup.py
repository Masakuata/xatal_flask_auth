from setuptools import setup

setup(
	name='xfss',
	version='0.8.3',
	description='A package to handle auth on flask. Made by Xatal',
	url='https://github.com/Masakuata/xatal_flask_auth',
	download_url="https://pypi.org/project/xf-auth/",
	author='Edson Manuel Carballo Vera',
	author_email='edsonmanuelcarballovera@gmail.com',
	license='MIT License',
	packages=['xfss'],
	install_requires=[
		'cryptography==3.1.1',
		"Flask~=2.2.2",
		"Werkzeug~=2.2.2",
		"requests~=2.28.1",
		"setuptools~=60.2.0",
		"validators==0.20.0"
	],

	classifiers=[
		'Development Status :: 2 - Pre-Alpha',
		'Framework :: Flask',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
		'Topic :: Internet :: WWW/HTTP :: Session'
	],
)
