from setuptools import setup

setup(
   name='loci',
   version='0.1',
   description='A high-level library for analyzing Points and Areas of Interest',
   author='Panagiotis Kalampokis, Dimitris Skoutas',
   author_email='pkalampokis@imis.athena-innovation.gr, dskoutas@imis.athena-innovation.gr',
   packages=['loci'],
   install_requires=['geopandas', 'shapely', 'pandas', 'numpy', 'matplotlib', 'folium', 'scikit-learn', 'hdbscan',
                     'scipy', 'networkx', 'wordcloud']
)
