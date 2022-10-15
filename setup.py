from setuptools import setup

setup(
	name='xf_auth',
	version='0.6.0',
	description='A package to handle auth on flask. Made by Xatal',
	url='https://github.com/Masakuata/xatal_flask_auth',
	author='Edson Manuel Carballo Vera',
	author_email='edsonmanuelcarballovera@gmail.com',
	license='MIT License',
	packages=['xf_auth'],
	install_requires=['cryptography==3.1.1', 'Flask'],

	classifiers=[
		'Development Status :: 2 - Pre-Alpha',
		'Framework :: Flask',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX :: Linux',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
		'Topic :: Internet :: WWW/HTTP :: Session'
	],
)
