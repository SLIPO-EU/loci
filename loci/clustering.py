import pandas as pd
import geopandas

from pandas import merge
from time import time
from sklearn.cluster import DBSCAN
import numpy as np
from shapely.ops import cascaded_union
from geopandas import GeoDataFrame
from hdbscan import HDBSCAN
from shapely.geometry import MultiPoint


def compute_clusters(pois, alg='dbscan', min_pts=None, eps=None, n_jobs=1):
    """Computes clusters using the DBSCAN or the HDBSCAN algorithm.

    Args:
         pois (GeoDataFrame): A POI GeoDataFrame.
         alg (string): The clustering algorithm to use (dbscan or hdbscan; default: dbscan).
         min_pts (integer): The minimum number of neighbors for a dense point.
         eps (float): The neighborhood radius.
         n_jobs (integer): Number of parallel jobs to run in the algorithm (default: 1)

    Returns:
          A GeoDataFrame containing the clustered POIs and their labels. The value of parameter `eps` for each cluster
          is also returned (which varies in the case of HDBSCAN).
    """

    # Prepare list of coordinates
    poi_list = [[p.x, p.y] for p in pois['geometry']]
    data_arr = np.array(poi_list)
    del poi_list[:]

    # Compute the clusters
    t0 = time()
    if alg == 'hdbscan':
        clusterer = HDBSCAN(min_cluster_size=min_pts, min_samples=min_pts, core_dist_n_jobs=n_jobs)
        labels = clusterer.fit_predict(data_arr)
        num_of_clusters = len(set(labels))

        tree = clusterer.condensed_tree_.to_pandas()
        cluster_tree = tree[tree.child_size > 1]
        chosen_clusters = clusterer.condensed_tree_._select_clusters()

        eps_per_cluster = cluster_tree[cluster_tree.child.isin(chosen_clusters)].\
            drop("parent", axis=1).drop("child", axis=1).reset_index().drop("index", axis=1)
        eps_per_cluster['lambda_val'] = eps_per_cluster['lambda_val'].apply(lambda x: 1 / x)
        eps_per_cluster.rename(columns={'lambda_val': 'eps', 'child_size': 'cluster_size'}, inplace=True)

    else:
        clusterer = DBSCAN(eps=eps, min_samples=min_pts, n_jobs=n_jobs).fit(data_arr)
        labels = clusterer.labels_

        num_of_clusters = len(set(labels))
        num_of_clusters_no_noise = set(labels)
        num_of_clusters_no_noise.discard(-1)
        num_of_clusters_no_noise = len(num_of_clusters_no_noise)

        eps_per_cluster = pd.DataFrame({'eps': [eps] * num_of_clusters_no_noise})
        eps_per_cluster['cluster_size'] = 0

    print("Done in %0.3fs." % (time() - t0))

    # Assign cluster labels to initial POIs
    pois['cluster_id'] = labels

    # Separate POIs that are inside clusters from those that are noise
    pois_in_clusters = pois.loc[pois['cluster_id'] > -1]
    pois_noise = pois.loc[pois['cluster_id'] == -1]

    print('Number of clusters: %d' % num_of_clusters)
    print('Number of clustered POIs: %d' % (len(pois_in_clusters)))
    print('Number of outlier POIs: %d' % (len(pois_noise)))

    return pois_in_clusters, eps_per_cluster


def cluster_shapes(pois, shape_type=1, eps_per_cluster=None):
    """Computes cluster shapes.

    Args:
         pois (GeoDataFrame): The clustered POIs.
         shape_type (integer): The methods to use for computing cluster shapes (allowed values: 1-3).
         eps_per_cluster (DataFrame): The value of parameter eps used for each cluster (required by methods 2 and 3).

    Returns:
          A GeoDataFrame containing the cluster shapes.
    """

    t0 = time()

    if shape_type == 2:
        cluster_borders = pois.groupby(['cluster_id'], sort=False)['geometry'].agg([list, np.size])
        join_df = merge(cluster_borders, eps_per_cluster, left_index=True, right_index=True, how='inner')
        cluster_list = []
        for index, row in join_df.iterrows():
            eps = row['eps']
            cluster_i = []
            for p in row['list']:
                cluster_i.append(p.buffer(eps))

            cluster_list.append(cascaded_union(cluster_i))

        join_df['geometry'] = cluster_list
        join_df['cluster_id'] = join_df.index
        join_df.reset_index(drop=True, inplace=True)
        join_df.drop(['list', 'cluster_size'], axis=1, inplace=True)

        cluster_borders = GeoDataFrame(join_df, crs=pois.crs, geometry='geometry')
        cluster_borders = cluster_borders[['cluster_id', 'size', 'geometry']]

    elif shape_type == 3:
        eps_dict = dict()
        for index, row in eps_per_cluster.iterrows():
            eps_dict[index] = row['eps']

        circles_from_pois = pois.copy()
        cid_size_dict = dict()
        circles = []
        for index, row in circles_from_pois.iterrows():
            cid = row['cluster_id']
            circles.append(row['geometry'].buffer(eps_dict[cid]))
            cid_size_dict[cid] = cid_size_dict.get(cid, 0) + 1

        circles_from_pois['geometry'] = circles

        s_index = pois.sindex

        pois_in_circles = geopandas.sjoin(pois, circles_from_pois, how="inner", op='intersects')
        agged_pois_per_circle = pois_in_circles.groupby(['cluster_id_left', 'index_right'],
                                                        sort=False)['geometry'].agg([list])

        poly_list = []
        cluster_id_list = []
        for index, row in agged_pois_per_circle.iterrows():
            pois_in_circle = row['list']
            lsize = len(pois_in_circle)
            if lsize >= 3:
                poly = MultiPoint(pois_in_circle).convex_hull
                poly_list.append(poly)
                cluster_id_list.append(index[0])

        temp_df = pd.DataFrame({
            'cluster_id': cluster_id_list,
            'geometry': poly_list
        })

        grouped_poly_per_cluster = temp_df.groupby(['cluster_id'], sort=False)['geometry'].agg([list])

        cluster_size_list = []
        poly_list = []
        for index, row in grouped_poly_per_cluster.iterrows():
            poly_list.append(cascaded_union(row['list']))
            cluster_size_list.append(cid_size_dict[index])

        grouped_poly_per_cluster['geometry'] = poly_list
        grouped_poly_per_cluster.drop(['list'], axis=1, inplace=True)

        cluster_borders = GeoDataFrame(grouped_poly_per_cluster, crs=pois.crs, geometry='geometry')
        cluster_borders['cluster_id'] = cluster_borders.index
        cluster_borders['size'] = cluster_size_list

    # type == 1 (default)
    else:
        cluster_borders = pois.groupby(['cluster_id'], sort=False)['geometry'].agg([list, np.size])
        cluster_borders['list'] = [MultiPoint(l).convex_hull for l in cluster_borders['list']]
        cluster_borders.rename(columns={"list": "geometry"}, inplace=True)
        cluster_borders.sort_index(inplace=True)
        cluster_borders = GeoDataFrame(cluster_borders, crs=pois.crs, geometry='geometry')
        cluster_borders.reset_index(inplace=True)

    print("Done in %0.3fs." % (time() - t0))

    return cluster_borders
