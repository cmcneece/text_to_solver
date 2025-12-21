import os
from setuptools import setup, find_packages

# Read the README file for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.rst')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

setup(
    name='text_to_solver',
    version='3.0.0',
    description='Easy to set-up non-linear solver with dynamic systems and programmatic API',
    long_description=read_readme(),
    long_description_content_type='text/x-rst',
    url='https://github.com/colinjmcneece/text_to_solver',
    author='Colin J. McNeece',
    author_email='colinjmcneece@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'numpy>=1.15.0',
        'scipy>=1.1.0',
        'sympy>=1.3',
        'pandas>=0.23.0',
    ],
    extras_require={
        'visualization': [
            'matplotlib>=3.5.0',
        ],
    },
    python_requires='>=3.7',
    zip_safe=False,
)
