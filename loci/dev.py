import csv
import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import random
import folium
from folium.plugins import MarkerCluster
from loci import analytics
import math
import numpy as np
import networkx as nx
from loci import index
from time import time
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.model_selection import GridSearchCV
from geopandas import GeoDataFrame
import shapely as shp


csv.field_size_limit(sys.maxsize)


def read_user_locations_csv(input_file, col_user_id='user_id', col_lon='lon', col_lat='lat', col_sep=';',
                            source_crs={'init': 'EPSG:4326'}, target_crs={'init': 'EPSG:4326'},
                            min_lon= -180.0, max_lon= 180.0,
                            min_lat=-90.0, max_lat= 90.0):
    """Creates a POI GeoDataFrame from an input CSV file.

    Args:
        input_file (string): Path to the input csv file.
        col_id (string): Name of the column containing the POI id (default: `id`).
        col_name (string): Name of the column containing the POI name (default: `name`).
        col_lon (string): Name of the column containing the POI longitude (default: `lon`).
        col_lat (string): Name of the column containing the POI latitude (default: `lat`).
        col_kwds (string): Name of the column containing the POI keywords (default: `kwds`).
        col_sep (string): Column delimiter (default: `;`).
        kwds_sep (string): Keywords delimiter (default: `,`).
        source_crs (string): Coordinate Reference System of input data (default: `EPSG:4326`).
        target_crs (string): Coordinate Reference System of the GeoDataFrame to be created (default: `EPSG:4326`).
        keep_other_cols (bool): Whether to keep the rest of the columns in the csv file (default: `False`).

    Returns:
        A POI GeoDataFrame with columns `id`, `name` and `kwds`.
    """

    def lon_lat_to_point(lon, lat):
        try:
            if math.isnan(lon) is False and math.isnan(lat) is False:
                return Point(lon, lat)
            else:
                return float('NaN')
        except:
            return float('NaN')

    lines = []
    with open(input_file, "r") as f:
        reader = csv.reader(f, delimiter=col_sep)
        for line in reader:
            if len(line) == 9:
                try:
                    lon = float(line[7])
                    lat = float(line[8])
                    user_id = line[1]
                    if lon >= min_lon and lon <= max_lon and lat >= min_lat and lat <= max_lat:
                        point = lon_lat_to_point(lon, lat)
                        if point is not float('NaN'):
                            lines.append([user_id, point])
                        #lines.append([user_id, lon, lat])
                except:
                    ()

    #pois = pd.DataFrame(lines, columns=['user_id', 'lon', 'lat'])
    pois = pd.DataFrame(lines, columns=['user_id', 'geometry'])
    print(pois.head(n=10))

    gpois = gpd.GeoDataFrame(pois, crs=source_crs, geometry=pois['geometry']).to_crs(target_crs)

    print(gpois.head(n=10))


def assign_colors_and_get_map(clusterDF, points=False, polygons=False):
    colors = []
    for x in range(clusterDF.index.size):
        r = lambda: random.randint(0,255)
        colors.append({'fillColor': '#%02X%02X%02X' % (r(),r(),r()), 'weight': 2, 'color': 'black', 'fillOpacity': 0.8})

    clusterDF['style'] = colors

    poly_bbox = analytics.bbox(clusterDF)
    center_point = poly_bbox.centroid

    m = folium.Map(location=[center_point.y, center_point.x], zoom_start=11, tiles='OpenStreetMap', width=900, height=600)

    if polygons is True or (points is False and polygons is False):
        folium.GeoJson(clusterDF[['geometry', 'style']]).add_to(m)
    else:
        for l, s, label in zip(clusterDF['contents'], clusterDF['style'], clusterDF.index):
            marker_cluster = MarkerCluster().add_to(m)
            for p in l:
                folium.Marker(
                    location=[p.y, p.x],
                    popup= 'cluster_' + str(label),
                    tooltip='cluster_' + str(label),
                    icon=folium.Icon(color='white', icon_color=s['fillColor'], icon='info-sign')
                ).add_to(marker_cluster)

    return m


def dbscan_2D(pois, eps, minpts):
    """Computes clusters using the DBSCAN algorithm implementation described in Section 2.2 of the paper "DBSCAN Revisited".

    Args:
         pois (GeoDataFrame): A POI GeoDataFrame.
         eps (float): The neighborhood radius.
         minpts (integer): The minimum number of points in the neighborhood to be considered as dense.

    Returns:
          A GeoDataFrame containing the clustered POIs and their labels (not including noise points).
    """

    class Cell:
        def __init__(self, is_core_cell, poi_list):
            self.is_core_cell = is_core_cell
            self.poi_list = poi_list

    class Poi:
        def __init__(self, poi, is_core_poi):
            self.poi = poi
            self.is_core_poi = is_core_poi

    cell_width = eps / math.sqrt(2.0)
    cell_height = cell_width

    grid_pois, num_of_columns, num_of_rows = index.grid(pois, cell_width=cell_width, cell_height=cell_height)
    grid_pois.set_index('cell_id', inplace=True)

    def get_key_nb_cell_ids(key):
        (row, column) = divmod(key, num_of_columns)

        nb_cid_list = [
            row * num_of_columns + column - 1,
            row * num_of_columns + column + 1
        ]

        for x in range(row-1, row+2, 2):
            for y in range(column-1, column+2):
                nb_cid_list.append(x * num_of_columns + y)

        for x in range(row-2, row+3, 4):
            for y in range(column-1, column+2):
                nb_cid_list.append(x * num_of_columns + y)

        for y in range(column - 2, column + 3, 4):
            for x in range(row-1, row+2):
                nb_cid_list.append(x * num_of_columns + y)

        return nb_cid_list

    t0 = time()

    pois.set_index('id', inplace=True)

    cell_dict = dict()
    for row in grid_pois.itertuples(index=True):
        id_list = getattr(row, "contents")
        if len(id_list) < minpts:
            cell_dict[getattr(row, "Index")] = Cell(False, [Poi(pois.loc[id]['geometry'], False) for id in id_list])
        else:
            cell_dict[getattr(row, "Index")] = Cell(True, [Poi(pois.loc[id]['geometry'], True) for id in id_list])


    for key, cell in cell_dict.items():
        if cell.is_core_cell is False:

            cell_poi_list = cell.poi_list
            num_of_pois_in_this_cell = len(cell_poi_list)

            nb_cell_ids = get_key_nb_cell_ids(key)
            for poi in cell_poi_list:
                counter = num_of_pois_in_this_cell
                has_more_than_minpts = False
                for nb_cell_id in nb_cell_ids:
                    nb_cell_pois = (cell_dict.get(nb_cell_id) or Cell(False, [])).poi_list
                    for nb_poi in nb_cell_pois:
                        if poi.poi.distance(nb_poi.poi) <= eps:
                            counter += 1
                            if counter >= minpts:
                                poi.is_core_poi = True
                                cell.is_core_cell = True
                                has_more_than_minpts = True
                                break

                    if has_more_than_minpts:
                        break

    # Build the Graph
    g = nx.Graph()

    for key, cell in cell_dict.items():
        if cell.is_core_cell:
            nb_cell_ids = get_key_nb_cell_ids(key)
            for nb_cell_id in nb_cell_ids:
                found_edge = False
                nb_cell = cell_dict.get(nb_cell_id) or Cell(False, [])
                if nb_cell.is_core_cell:
                    for poi in cell.poi_list:
                        for nb_poi in nb_cell.poi_list:
                            if poi.poi.distance(nb_poi.poi) <= eps:
                                g.add_edge(key, nb_cell_id)
                                found_edge = True
                                break

                        if found_edge:
                            break

    #Find connected components.
    conn_comp_gen = nx.connected_components(g)

    cellID_clusterID_dic = dict()
    i = 0
    for xSet in conn_comp_gen:
        for cell_id in xSet:
            cellID_clusterID_dic[cell_id] = i
        i += 1

    print('Number of clusters: %d' % i)

    def assign_cluster_id(row):
        cluster_id = cellID_clusterID_dic.get(row['cell_id'], -1)
        #Check if poi is Border Poi.
        if cluster_id == -1:
            p = Poi(row['geometry'], False)
            cell_id = row['cell_id']
            nb_cell_ids = get_key_nb_cell_ids(cell_id)
            for nb_cell_id in nb_cell_ids:
                nb_cell = cell_dict.get(nb_cell_id) or Cell(False, [])
                if nb_cell.is_core_cell:
                    for nb_poi in nb_cell.poi_list:
                        if nb_poi.is_core_poi and p.poi.distance(nb_poi.poi) <= eps:
                            return cellID_clusterID_dic.get(nb_cell_id, -1)

            return -1
        else:
            return cluster_id

    pois['cluster_id'] = pois.apply(lambda row: assign_cluster_id(row), axis=1)

    del cellID_clusterID_dic
    del cell_dict

    pois.drop('cell_id', axis=1, inplace=True)

    # Filter out noise points.
    pois = pois[(pois.cluster_id != -1)]

    print("Done in %0.3fs." % (time() - t0))

    return pois


def lda(gdf, label_col='label', kwd_col='kwds', num_of_topics=5):

    #Create a "document" for each cluster
    cluster_kwds = dict()
    for index, row in gdf.iterrows():
        cluster_id, kwds = row[label_col], row[kwd_col]
        if cluster_id not in cluster_kwds:
            cluster_kwds[cluster_id] = ''
        for w in kwds:
            cluster_kwds[cluster_id] += w + ' '

    # Vectorize the corpus
    vectorizer = CountVectorizer()
    corpus_vectorized = vectorizer.fit_transform(cluster_kwds.values())

    #Build the model
    search_params = {'n_components': [num_of_topics]}
    lda = LatentDirichletAllocation(n_jobs=-1)
    model = GridSearchCV(lda, param_grid=search_params, n_jobs=-1, cv=3)
    model.fit(corpus_vectorized)
    lda_model = model.best_estimator_

    #Top keywords per Topic
    n_words = 10
    keywords = np.array(vectorizer.get_feature_names())
    topic_keywords = []
    for topic_weights in lda_model.components_:
        top_keyword_locs = (-topic_weights).argsort()[:n_words]
        k = keywords.take(top_keyword_locs)
        topic_keywords.append(k)

    topic_keywords = pd.DataFrame(topic_keywords)
    topic_keywords.columns = ['Kwd ' + str(i) for i in range(topic_keywords.shape[1])]
    topic_keywords.index = ['Topic ' + str(i) for i in range(topic_keywords.shape[0])]

    #Topics per cluster
    lda_output = lda_model.transform(corpus_vectorized)
    topic_names = ["Topic" + str(i) for i in range(lda_model.n_components)]
    cluster_names = cluster_kwds.keys()
    df_cluster_topic = pd.DataFrame(np.round(lda_output, 2), columns=topic_names, index=cluster_names).sort_index()
    dominant_topic = np.argmax(df_cluster_topic.values, axis=1)
    df_cluster_topic['Dominant Topic'] = dominant_topic

    #Compute cluster borders
    cluster_borders = gdf.groupby([label_col], sort=False)['geometry'].agg([list, np.size])
    geom = [shp.geometry.MultiPoint(x).convex_hull for x in cluster_borders['list']]
    cluster_borders = GeoDataFrame(cluster_borders, crs=gdf.crs, geometry=geom).drop(columns=['list'])

    #Assign topic labels to clusters
    cluster_borders_labeled = pd.merge(cluster_borders,
                                       df_cluster_topic,
                                       left_index=True,
                                       right_index=True,
                                       how='inner')

    return cluster_borders_labeled, topic_keywords
