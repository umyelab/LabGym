'''
Copyright (C)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)#fulltext. 

For license issues, please contact:

Dr. Bing Ye
Life Sciences Institute
University of Michigan
210 Washtenaw Avenue, Room 5403
Ann Arbor, MI 48109-2216
USA

Email: bingye@umich.edu
'''



from setuptools import setup,find_packages
import pathlib
import os

path=pathlib.Path(__file__).parent.resolve()

try:
    with open(os.path.join(path,'README.md'),encoding='utf-8') as readme:
        long_description=readme.read()
except Exception:
    long_description=''


setup(name='LabGym',version='1.6',author='Yujia Hu',
    author_email='henryhu@umich.edu',
    description='Quantification of user-defined animal behaviors',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/umyelab/LabGym',
    platform='any',
    packages=find_packages(),
    package_data={
        '':['*.txt','*.png','*.pb','*.jpg','*.csv','*.index','*.data-00000-of-00001']
    },
    license='GNU General Public License v3 (GPLv3)',
    classifiers=[
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: OS Independent',
    ],
    keywords='quantification of user-defined behaviors',
    python_requires='>=3.9',
    install_requires=[
    'tensorflow>=2.6.0',
    'matplotlib>=3.4.3',
    'moviepy>=1.0.3',
    'opencv-contrib-python>=4.5.3.56',
    'opencv-python>=4.5.3',
    'openpyxl>=3.0.9',
    'pandas>=1.3.3',
    'pathlib>=1.0.1',
    'scikit-learn>=1.0',
    'scikit-image>=0.18.3',
    'seaborn>=0.11.2',
    'wxPython>=4.1.1',
    ]  
)
