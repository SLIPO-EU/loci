from pandas import DataFrame, merge
from time import time
from sklearn.cluster import DBSCAN
import numpy as np
from shapely.ops import cascaded_union
from geopandas import GeoDataFrame
from hdbscan import HDBSCAN


def compute_clusters(pois, alg='hdbscan', min_pts=None, eps=None, cluster_shapes=True):
    """Computes clusters using the DBSCAN or the HDBSCAN algorithm.

    Args:
         pois (GeoDataFrame): A POI GeoDataFrame.
         alg (string): The clustering algorithm to use (dbscan or hdbscan; default: hdbscan).
         min_pts (integer): The minimum number of neighbors for a dense point.
         eps (float): The neighborhood radius.
         cluster_shapes (Boolean): Whether to return cluster shapes (default: True).

    Returns:
          A GeoDataFrame containing the clustered POIs and their labels, a GeoDataFrame containing the POIs that are
          not part of any cluster, and (optionally) a GeoDataFrame containing the cluster shapes.
    """

    # Prepare list of coordinates
    poi_list = [[p.x, p.y] for p in pois['geometry']]
    data_arr = np.array(poi_list)
    del poi_list[:]

    # Compute the clusters
    t0 = time()
    if alg == 'hdbscan':
        clusterer = HDBSCAN(min_cluster_size=min_pts, min_samples=min_pts)
        labels = clusterer.fit_predict(data_arr)
        num_of_clusters = len(set(labels))

        tree = clusterer.condensed_tree_.to_pandas()
        cluster_tree = tree[tree.child_size > 1]
        chosen_clusters = clusterer.condensed_tree_._select_clusters()

        cluster_tree_chosen = cluster_tree[cluster_tree.child.isin(chosen_clusters)].drop("parent", axis=1).drop("child", axis=1).reset_index().drop("index", axis=1)
        cluster_tree_chosen['lambda_val'] = cluster_tree_chosen['lambda_val'].apply(lambda x: 1 / x)
        cluster_tree_chosen.rename(columns={'lambda_val': 'eps', 'child_size': 'cluster_size'}, inplace=True)

    else:
        clusterer = DBSCAN(eps=eps, min_samples=min_pts).fit(data_arr)
        labels = clusterer.labels_

        num_of_clusters = len(set(labels))
        num_of_clusters_no_noise = set(labels)
        num_of_clusters_no_noise.discard(-1)
        num_of_clusters_no_noise = len(num_of_clusters_no_noise)

        cluster_tree_chosen = DataFrame({'eps': [eps] * num_of_clusters_no_noise})
        cluster_tree_chosen['cluster_size'] = 0

    print("Done in %0.3fs." % (time() - t0))

    # Assign cluster labels to initial POIs
    pois['cluster_id'] = labels

    # Separate POIs that are inside clusters from those that are noise
    pois_in_clusters = pois.loc[pois['cluster_id'] > -1]
    pois_noise = pois.loc[pois['cluster_id'] == -1]

    print('Number of clusters: %d' % num_of_clusters)
    print('Number of clustered POIs: %d' % (len(pois_in_clusters)))
    print('Number of outlier POIs: %d' % (len(pois_noise)))

    cluster_borders = None
    if cluster_shapes:
        # Compute cluster shapes
        cluster_borders = pois_in_clusters.groupby(['cluster_id'], sort=False)['geometry'].agg([list, np.size])
        join_df = merge(cluster_borders, cluster_tree_chosen, left_index=True, right_index=True, how='inner')
        cluster_list = []
        for index, row in join_df.iterrows():
            eps = row['eps']
            cluster_i = []
            for p in row['list']:
                cluster_i.append(p.buffer(eps))

            cluster_list.append(cascaded_union(cluster_i))

        join_df['geometry'] = cluster_list
        join_df.reset_index(drop=True, inplace=True)
        join_df.drop(['list', 'cluster_size'], axis=1, inplace=True)

        cluster_borders = GeoDataFrame(join_df, crs=pois.crs, geometry='geometry')
        cluster_borders['cluster_id'] = cluster_borders.index

    return pois_in_clusters, pois_noise, cluster_borders
