
from distutils.core import setup
from setuptools import find_packages

options = {'apk': {'debug': None,
                   'requirements': 'sdl2,pyjnius,kivy,python3',
                   'android-api': 29,
                   'ndk-api': 21,
                   'ndk-dir': '/home/sandy/android/android-ndk-r20',
                   'sdk-dir': '/home/sandy/android/android-sdk',
                   'wakelock': None,
                   'orientation': 'landscape',
                   'dist-name': 'camera2test',
                   'ndk-version': '10.3.2',
                   'package': 'net.inclem.camera2',
                   'permission': 'CAMERA',
                   'arch': 'arm64-v8a',
                   'add-source': 'java',
                   # 'window': None,
                   }}

packages = find_packages()
print('packages are', packages)

setup(
    name='camera2 test',
    version='0.1',
    description='camera',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=find_packages(),
    options=options,
    package_data={
        'camera2': ['*.py', '*.png', '*.kv']
    }
)
