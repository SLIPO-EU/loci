from time import time
from sklearn.cluster import DBSCAN
import numpy as np
from shapely.geometry import MultiPoint
from geopandas import GeoDataFrame
from hdbscan import HDBSCAN


def compute_clusters(pois, alg='hdbscan', min_pts=None, eps=None):
    """Computes clusters using the DBSCAN or the HDBSCAN algorithms.

    Args:
         pois (GeoDataFrame): A POI GeoDataFrame.
         alg (string): The clustering algorithm to use (dbscan or hdbscan; default: hdbscan).
         min_pts (integer): The minimum number of neighbors for a dense point.
         eps (float): The neighborhood radius.

    Returns:
          A GeoDataFrame containing the clustered POIs and their labels, a GeoDataFrame containing the POIs that are
          not part of any cluster, and a GeoDataFrame containing the cluster borders.
    """

    # Prepare list of coordinates
    poi_list = [[p.x, p.y] for p in pois['geometry']]
    data_arr = np.array(poi_list)
    del poi_list[:]

    # Compute the clusters
    t0 = time()
    if alg == 'dbscan':
        clusterer = DBSCAN(eps=eps, min_samples=min_pts).fit(data_arr)
        labels = clusterer.labels_
        num_clusters = len(set(labels))
    else:
        clusterer = HDBSCAN(min_cluster_size=min_pts, min_samples=min_pts)
        labels = clusterer.fit_predict(data_arr)
        num_clusters = len(set(labels))

    print("Done in %0.3fs." % (time() - t0))

    # Assign cluster labels to initial POIs
    pois['cluster_id'] = labels

    # Separate POIs that are inside clusters from those that are noise
    pois_in_clusters = pois.loc[pois['cluster_id'] > -1]
    pois_noise = pois.loc[pois['cluster_id'] == -1]

    # Compute cluster borders using convex hull
    cluster_borders = pois_in_clusters.groupby(['cluster_id'], sort=False)['geometry'].agg([list, np.size])
    geom = [MultiPoint(x).convex_hull for x in cluster_borders['list']]
    cluster_borders = GeoDataFrame(cluster_borders, crs=pois.crs, geometry=geom)
    cluster_borders = cluster_borders.drop('list', axis=1)
    cluster_borders = cluster_borders[['geometry', 'size']]
    cluster_borders = cluster_borders.sort_values(by='size', ascending=False)
    cluster_borders = cluster_borders.reset_index()

    print('Number of clusters: %d' % (num_clusters - 1))
    print('Number of clustered POIs: %d' % (len(pois_in_clusters)))
    print('Number of outlier POIs: %d' % (len(pois_noise)))

    return pois_in_clusters, pois_noise, cluster_borders
