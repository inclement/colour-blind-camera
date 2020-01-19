
from distutils.core import setup
from setuptools import find_packages

options = {'apk': {'debug': None,
                   'requirements': 'sdl2,pyjnius,kivy==master,python3',
                   'android-api': 29,
                   'ndk-api': 21,
                   'ndk-dir': '/home/sandy/android/android-ndk-r20',
                   'sdk-dir': '/home/sandy/android/android-sdk',
                   'wakelock': None,
                   'orientation': 'landscape',
                   'dist-name': 'camera2test',
                   'ndk-version': '10.3.2',
                   'package': 'net.inclem.colourblind',
                   'permission': 'CAMERA',
                   # 'arch': 'armeabi-v7a',
                   'arch': 'arm64-v8a',
                   'add-source': 'java',
                   'icon': 'build_assets/logo.png',
                   'presplash': 'build_assets/splash.png',
                   # 'window': None,
                   }}

packages = find_packages()
print('packages are', packages)

setup(
    name='ColourBlind',
    version='0.3',
    description='camera',
    author='Alexander Taylor',
    author_email='alexanderjohntaylor@gmail.com',
    packages=find_packages(),
    options=options,
    package_data={
        'camera2': ['*.py', '*.png', '*.kv', '*.ttf']
    }
)
