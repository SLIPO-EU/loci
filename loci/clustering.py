from time import time
from sklearn.cluster import DBSCAN
import numpy as np
import shapely as shp
from geopandas import GeoDataFrame
from hdbscan import HDBSCAN


def dbscan(pois, eps, minpts):
    """Computes clusters using the DBSCAN algorithm.

    Args:
         pois (GeoDataFrame): A POI GeoDataFrame.
         eps (float): The neighborhood radius.
         minpts (integer): The minimum number of points in the neighborhood to be considered as dense.

    Returns:
          A GeoDataFrame containing the clustered POIs and their labels (not including noise points).
    """

    # Prepare list of coordinates
    t0 = time()
    poi_list = [[p.x, p.y] for p in pois['geometry']]
    data_arr = np.array(poi_list)
    del poi_list[:]

    # Run DBSCAN
    db = DBSCAN(eps=eps, min_samples=minpts).fit(data_arr)
    labels = db.labels_
    num_clusters = len(set(labels))
    print('Number of clusters: %d' % (num_clusters-1))

    # Assign cluster labels to initial POIs
    pois['label'] = labels
    pois = pois[pois.label > -1]
    print("Done in %0.3fs." % (time() - t0))

    cluster_borders = pois.groupby(['label'], sort=False)['geometry'].agg([list, np.size])
    geom = [shp.geometry.MultiPoint(x).convex_hull for x in cluster_borders['list']]
    cluster_borders = GeoDataFrame(cluster_borders, crs=pois.crs, geometry=geom)
    cluster_borders.rename(columns={'list': 'contents'}, inplace=True)
    cluster_borders = cluster_borders[['contents', 'geometry', 'size']]

    return pois, cluster_borders


def hdbscan(pois, minpts):
    """Computes clusters using the HDBSCAN algorithm.

    Args:
         pois (GeoDataFrame): A POI GeoDataFrame.
         minpts (integer): The minimum number of points in the neighborhood to be considered as dense.

    Returns:
          A GeoDataFrame containing the clustered POIs and their labels (not including noise points).
    """

    t0 = time()
    poi_list = [[p.x, p.y] for p in pois['geometry']]
    data_arr = np.array(poi_list)
    del poi_list[:]

    # Run HDBSCAN
    clusterer = HDBSCAN(min_cluster_size=minpts)
    labels = clusterer.fit_predict(data_arr)

    num_clusters = len(set(labels))
    print('Number of clusters: %d' % (num_clusters - 1))

    # Assign cluster labels to initial POIs
    pois['label'] = labels
    pois = pois[pois.label > -1]
    print("Done in %0.3fs." % (time() - t0))

    cluster_borders = pois.groupby(['label'], sort=False)['geometry'].agg([list, np.size])
    geom = [shp.geometry.MultiPoint(x).convex_hull for x in cluster_borders['list']]
    cluster_borders = GeoDataFrame(cluster_borders, crs=pois.crs, geometry=geom)
    cluster_borders.rename(columns={'list': 'contents'}, inplace=True)
    cluster_borders = cluster_borders[['contents', 'geometry', 'size']]

    return pois, cluster_borders
