import numpy as np
import matplotlib
from matplotlib import colors
from matplotlib import cm
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from folium.plugins import MarkerCluster
from loci.analytics import bbox, kwds_freq
from wordcloud import WordCloud
from pysal.viz.mapclassify import Natural_Breaks
from pandas import DataFrame, concat
from geopandas import GeoDataFrame
import osmnx


def map_points(pois, tiles='OpenStreetMap', width='100%', height='100%', show_bbox=False):
    """Returns a Folium Map displaying the provided points. Map center and zoom level are set automatically.

    Args:
         pois (GeoDataFrame): A GeoDataFrame containing the POIs to be displayed.
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).
         show_bbox (bool): Whether to show the bounding box of the GeoDataFrame (default: False).

    Returns:
        A Folium Map object displaying the given POIs.
    """

    # Set the crs to WGS84
    if pois.crs['init'] != '4326':
        pois = pois.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the bounding box enclosing the POIs.
    bb = bbox(pois)
    map_center = [bb.centroid.y, bb.centroid.x]

    # Initialize the map
    m = folium.Map(location=map_center, tiles=tiles, width=width, height=height)

    # Automatically set the zoom level
    m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    # Add pois to a marker cluster
    coords, popups = [], []
    for idx, poi in pois.iterrows():
        coords.append([poi.geometry.y, poi.geometry.x])
        label = str(poi['id']) + '<br>' + str(poi['name']) + '<br>' + ' '.join(poi['kwds'])
        popups.append(folium.IFrame(label, width=300, height=100))

    poi_layer = folium.FeatureGroup(name='pois')
    poi_layer.add_child(MarkerCluster(locations=coords, popups=popups))
    m.add_child(poi_layer)

    # folium.GeoJson(pois, tooltip=folium.features.GeoJsonTooltip(fields=['id', 'name', 'kwds'],
    #                                                             aliases=['ID:', 'Name:', 'Keywords:'])).add_to(m)

    if show_bbox:
        folium.GeoJson(bb).add_to(m)

    return m


def map_geometries(gdf, tiles='OpenStreetMap', width='100%', height='100%'):
    """Returns a Folium Map displaying the provided geometries. Map center and zoom level are set automatically.

    Args:
         gdf (GeoDataFrame): A GeoDataFrame containing the geometries to be displayed.
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).

    Returns:
        A Folium Map object displaying the given geometries.
    """

    # Set the crs to WGS84
    if gdf.crs['init'] != '4326':
        gdf = gdf.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the bounding box enclosing the POIs.
    bb = bbox(gdf)
    map_center = [bb.centroid.y, bb.centroid.x]

    # Initialize the map
    m = folium.Map(location=map_center, tiles=tiles, width=width, height=height)

    # Automatically set the zoom level
    m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    # Construct tooltip
    fields = list(gdf.columns.values)
    fields.remove('geometry')
    if 'style' in fields:
        fields.remove('style')
    tooltip = folium.features.GeoJsonTooltip(fields=fields)

    # Add to map
    folium.GeoJson(gdf, tooltip=tooltip).add_to(m)

    return m


def map_geometry(geom, tiles='OpenStreetMap', width='100%', height='100%'):
    """Returns a Folium Map displaying the provided geometry. Map center and zoom level are set automatically.

    Args:
         geom (Shapely Geometry): A geometry to be displayed.
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).

    Returns:
        A Folium Map object displaying the given geometry.
    """

    m = folium.Map(location=[geom.centroid.y, geom.centroid.x], tiles=tiles, width=width, height=height)
    m.fit_bounds(([geom.bounds[1], geom.bounds[0]], [geom.bounds[3], geom.bounds[2]]))

    folium.GeoJson(geom).add_to(m)

    return m


def barchart(data, orientation='Vertical', x_axis_label='', y_axis_label='', plot_title='', bar_width=0.5,
             plot_width=15, plot_height=5, top_k=10):
    """Plots a bar chart with the given data.

    Args:
        data (dict): The data to plot.
        orientation (string): The orientation of the bars in the plot (`Vertical` or `Horizontal`; default: `Vertical`).
        x_axis_label (string): Label of x axis.
        y_axis_label (string): Label of y axis.
        plot_title (string): Title of the plot.
        bar_width (scalar): The width of the bars (default: 0.5).
        plot_width (scalar): The width of the plot (default: 15).
        plot_height (scalar): The height of the plot (default: 5).
        top_k (integer): Top k results (if -1, show all; default: 10).

    Returns:
        A Matplotlib plot displaying the bar chart.
    """

    plt.rcdefaults()
    matplotlib.rcParams['figure.figsize'] = [plot_width, plot_height]

    sort_order = True
    if orientation != 'Vertical':
        sort_order = False

    sorted_by_value = sorted(data.items(), key=lambda kv: kv[1], reverse=sort_order)

    if top_k != -1:
        if orientation != 'Vertical':
            sorted_by_value = sorted_by_value[-top_k:]
        else:
            sorted_by_value = sorted_by_value[0:top_k]

    (objects, performance) = map(list, zip(*sorted_by_value))
    y_pos = np.arange(len(objects))

    if orientation == 'Vertical':
        plt.bar(y_pos, performance, width=bar_width, align='center', alpha=0.5)
        plt.xticks(y_pos, objects)
    else:
        plt.barh(y=y_pos, width=performance, align='center', alpha=0.5)
        plt.yticks(y_pos, objects)

    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_label)
    plt.title(plot_title)

    return plt


def plot_wordcloud(pois, bg_color='black', width=400, height=200):
    """Generates and plots a word cloud from the keywords of the given POIs.

     Args:
        pois (GeoDataFrame): The POIs from which the keywords will be used to generate the word cloud.
        bg_color (string): The background color to use for the plot (default: black).
        width (int): The width of the plot.
        height (int): The height of the plot.
    """

    # Compute keyword frequences
    kf = kwds_freq(pois)

    # Generate the word cloud
    wordcloud = WordCloud(background_color=bg_color, width=width, height=height).generate_from_frequencies(kf)

    # Show plot
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()


def heatmap(pois, tiles='OpenStreetMap', width='100%', height='100%', radius=10):
    """Generates a heatmap of the input POIs.

    Args:
        pois (GeoDataFrame): A POIs GeoDataFrame.
        tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
        width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
        height (integer or percentage): Height of the map in pixels or percentage (default: 100%).
        radius (float): Radius of each point of the heatmap (default: 10).

    Returns:
        A Folium Map object displaying the heatmap generated from the POIs.
    """

    # Set the crs to WGS84
    if pois.crs['init'] != '4326':
        pois = pois.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the gdf's bounding box
    bb = bbox(pois)
    map_center = [bb.centroid.y, bb.centroid.x]

    heat_map = folium.Map(location=map_center, tiles=tiles, width=width, height=height)

    # Automatically set zoom level
    heat_map.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    # List comprehension to make list of lists
    heat_data = [[row['geometry'].y, row['geometry'].x] for index, row in pois.iterrows()]

    # Plot it on the map
    HeatMap(heat_data, radius=radius).add_to(heat_map)

    return heat_map


def map_choropleth(areas, id_field, value_field, fill_color='YlOrRd', fill_opacity=0.6, num_bins=5,
                   tiles='OpenStreetMap', width='100%', height='100%'):
    """Returns a Folium Map showing the clusters. Map center and zoom level are set automatically.

    Args:
         areas (GeoDataFrame): A GeoDataFrame containing the areas to be displayed.
         id_field (string): The name of the column to use as id.
         value_field (string): The name of the column indicating the area's value.
         fill_color (string): A string indicating a Matplotlib colormap (default: YlOrRd).
         fill_opacity (float): Opacity level (default: 0.6).
         num_bins (int): The number of bins for the threshold scale (default: 5).
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).

    Returns:
        A Folium Map object displaying the given clusters.
    """

    # Set the crs to WGS84
    if areas.crs['init'] != '4326':
        areas = areas.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the bounding box enclosing the POIs.
    bb = bbox(areas)
    map_center = [bb.centroid.y, bb.centroid.x]

    # Initialize the map
    m = folium.Map(location=map_center, tiles=tiles, width=width, height=height)

    # Automatically set the zoom level
    m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    threshold_scale = Natural_Breaks(areas[value_field], k=num_bins).bins.tolist()
    threshold_scale.insert(0, areas[value_field].min())

    choropleth = folium.Choropleth(areas, data=areas, columns=[id_field, value_field],
                                   key_on='feature.properties.{}'.format(id_field),
                                   fill_color=fill_color, fill_opacity=fill_opacity,
                                   threshold_scale=threshold_scale).add_to(m)

    # Construct tooltip
    fields = list(areas.columns.values)
    fields.remove('geometry')
    if 'style' in fields:
        fields.remove('style')
    tooltip = folium.features.GeoJsonTooltip(fields=fields)

    choropleth.geojson.add_child(tooltip)

    return m


def map_clusters_with_topics(clusters_topics, viz_type='dominant', col_id='cluster_id', col_dominant='Dominant Topic',
                             colormap='tab10', red='Topic0', green='Topic1', blue='Topic2', single_topic='Topic0',
                             tiles='OpenStreetMap', width='100%', height='100%'):
    """Returns a Folium Map showing the clusters colored based on their topics.

    Args:
         clusters_topics (GeoDataFrame): A GeoDataFrame containing the clusters to be displayed and their topics.
         viz_type (string): Indicates how to assign colors based on topics. One of: 'dominant', 'single', 'rgb'.
         col_id (string): The name of the column indicating the cluster id (default: cluster_id).
         col_dominant (string): The name of the column indicating the dominant topic (default: Dominant Topic).
         colormap (string): A string indicating a Matplotlib colormap (default: tab10).
         red (string): The name of the column indicating the topic to assign to red (default: Topic0).
         green (string): The name of the column indicating the topic to assign to green (default: Topic1).
         blue (string): The name of the column indicating the topic to assign to blue (default: Topic2).
         single_topic (string): The name of the column indicating the topic to use (default: Topic0).
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).

    Returns:
        A Folium Map object displaying the given clusters colored by their topics.
    """

    def style_gen_dominant(row):
        cmap = cm.get_cmap(colormap)
        rgb = cmap(row[col_dominant])
        color = colors.rgb2hex(rgb)
        return {'fillColor': color, 'weight': 2, 'color': 'black', 'fillOpacity': 0.8}

    def style_gen_mixed(row):
        r = round(row[red] * 255) if red is not None else 0
        g = round(row[green] * 255) if green is not None else 0
        b = round(row[blue] * 255) if blue is not None else 0
        color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
        return {'fillColor': color, 'weight': 2, 'color': 'black', 'fillOpacity': 0.8}

    if viz_type == 'single':
        m = map_choropleth(areas=clusters_topics, id_field=col_id, value_field=single_topic, tiles=tiles, width=width,
                           height=height)
    elif viz_type == 'rgb':
        clusters_topics['style'] = clusters_topics.apply(lambda row: style_gen_mixed(row), axis=1)
        m = map_geometries(clusters_topics, tiles=tiles, width=width, height=height)
    else:
        clusters_topics['style'] = clusters_topics.apply(lambda row: style_gen_dominant(row), axis=1)
        m = map_geometries(clusters_topics, tiles=tiles, width=width, height=height)

    return m


def map_cluster_diff(clusters_a, clusters_b, intersection_color='#00ff00', diff_ab_color='#0000ff',
                     diff_ba_color='#ff0000', tiles='OpenStreetMap', width='100%', height='100%'):
    """Returns a Folium Map displaying the differences between two sets of clusters. Map center and zoom level
    are set automatically.

    Args:
         clusters_a (GeoDataFrame): The first set of clusters.
         clusters_b (GeoDataFrame): The second set of clusters.
         intersection_color (color code): The color to use for A & B.
         diff_ab_color (color code): The color to use for A - B.
         diff_ba_color (color code): The color to use for B - A.
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).

    Returns:
        A Folium Map object displaying cluster intersections and differences.
    """

    if clusters_a.crs['init'] != '4326':
        clusters_a = clusters_a.to_crs({'init': 'epsg:4326'})

    if clusters_b.crs['init'] != '4326':
        clusters_b = clusters_b.to_crs({'init': 'epsg:4326'})

    spatial_index_b = clusters_b.sindex
    prev_size_list = []
    prev_cid_list = []

    after_cid_list = []
    after_size_list = []
    intersect_area_percentage_list = []

    intersection_polygons = []
    diff_ab_polygs = []
    diff_ba_polygs = []
    new_polygs = []

    intersection_polygons_attr = []
    diff_ab_polygs_attr = []
    diff_ba_polygs_attr = []
    new_polygs_attr = []

    for index_1, row_1 in clusters_a.iterrows():
        size = row_1['size']
        poly = row_1['geometry']
        cid = row_1['cluster_id']

        prev_area = poly.area
        prev_cid_list.append(cid)
        prev_size_list.append(size)

        possible_matches_index = list(spatial_index_b.intersection(poly.bounds))
        possible_matches = clusters_b.iloc[possible_matches_index]

        max_area = 0.0
        max_cid_intersect = -1
        max_size = 0

        max_polyg = None
        max_intersect_polyg = None

        for index_2, row_2 in possible_matches.iterrows():
            size_2 = row_2['size']
            poly_2 = row_2['geometry']
            cid_2 = row_2['cluster_id']

            intersect_polyg = poly.intersection(poly_2)
            area = intersect_polyg.area

            if area > max_area:
                max_area = area
                max_cid_intersect = cid_2
                max_size = size_2
                max_polyg = poly_2
                max_intersect_polyg = intersect_polyg

        if max_cid_intersect == -1:
            after_cid_list.append(np.nan)
            after_size_list.append(np.nan)
            intersect_area_percentage_list.append(0.0)
            new_polygs.append(poly)
            new_polygs_attr.append('A (' + str(cid) + ')')
        else:
            after_cid_list.append(max_cid_intersect)
            after_size_list.append(max_size)
            intersect_area_percentage_list.append(max_area / prev_area)

            ab_diff_poly = poly.difference(max_polyg)
            ba_diff_poly = max_polyg.difference(poly)

            intersection_polygons.append(max_intersect_polyg)
            diff_ab_polygs.append(ab_diff_poly)
            diff_ba_polygs.append(ba_diff_poly)

            intersection_polygons_attr.append('A(' + str(cid) + ') & B(' + str(max_cid_intersect) + ')')
            diff_ab_polygs_attr.append('A(' + str(cid) + ') - B(' + str(max_cid_intersect) + ')')
            diff_ba_polygs_attr.append('B(' + str(max_cid_intersect) + ') - A(' + str(cid) + ')')

    spatial_index_a = clusters_a.sindex
    old_polys = []
    old_poly_attr = []

    for index, row in clusters_b.iterrows():
        poly = row['geometry']
        cid = row['cluster_id']

        possible_matches_index = list(spatial_index_a.intersection(poly.bounds))
        possible_matches = clusters_a.iloc[possible_matches_index]

        max_area = 0.0

        for index_2, row_2 in possible_matches.iterrows():
            poly_2 = row_2['geometry']

            intersect_polyg = poly.intersection(poly_2)
            area = intersect_polyg.area

            if area > max_area:
                max_area = area

        if max_area == 0.0:
            old_polys.append(poly)
            old_poly_attr.append('B (' + str(cid) + ')')

    intersection_gdf = GeoDataFrame(list(zip(intersection_polygons, intersection_polygons_attr)),
                                    columns=['geometry', 'diff'], crs=clusters_a.crs)

    diff_ab_gdf = GeoDataFrame(list(zip(diff_ab_polygs + new_polygs, diff_ab_polygs_attr + new_polygs_attr)),
                               columns=['geometry', 'diff'], crs=clusters_a.crs)

    diff_ba_gdf = GeoDataFrame(list(zip(diff_ba_polygs + old_polys, diff_ba_polygs_attr + old_poly_attr)),
                               columns=['geometry', 'diff'], crs=clusters_a.crs)

    # Filter out erroneous rows
    intersection_gdf = intersection_gdf[(intersection_gdf.geometry.area > 0.0)]
    diff_ab_gdf = diff_ab_gdf[(diff_ab_gdf.geometry.area > 0.0)]
    diff_ba_gdf = diff_ba_gdf[(diff_ba_gdf.geometry.area > 0.0)]

    # Add colors
    intersection_style = {'fillColor': intersection_color, 'weight': 2, 'color': 'black', 'fillOpacity': 0.8}
    diff_ab_style = {'fillColor': diff_ab_color, 'weight': 2, 'color': 'black', 'fillOpacity': 0.8}
    diff_ba_style = {'fillColor': diff_ba_color, 'weight': 2, 'color': 'black', 'fillOpacity': 0.8}
    intersection_gdf['style'] = intersection_gdf.apply(lambda x: intersection_style, axis=1)
    diff_ab_gdf['style'] = diff_ab_gdf.apply(lambda x: diff_ab_style, axis=1)
    diff_ba_gdf['style'] = diff_ba_gdf.apply(lambda x: diff_ba_style, axis=1)

    # Concatenate results
    all_gdf = concat([diff_ab_gdf, diff_ba_gdf, intersection_gdf], ignore_index=True, sort=False)

    # Generate map
    m = map_geometries(all_gdf, tiles=tiles, width=width, height=height)

    return m


def map_cluster_contents_osm(cluster_borders, tiles='OpenStreetMap', width='100%', height='100%'):
    """Constructs a Folium Map displaying the streets and buildings, retreived from OpenStreetMap via OSMNX, within
    a given AOI.

    Args:
        cluster_borders (GeoDataFrame): The cluster polygons.
        tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
        width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
        height (integer or percentage): Height of the map in pixels or percentage (default: 100%).

    Returns:
        A Folium Map object displaying the retreived entities.
    """

    def is_nan(num):
        return num != num

    # set the crs to WGS84
    if cluster_borders.crs['init'] != '4326':
        cluster_borders = cluster_borders.to_crs({'init': 'epsg:4326'})

    empty_df = DataFrame(columns=['geometry', 'cluster_id', 'type', 'info'])
    final_gdf = GeoDataFrame(empty_df, crs=cluster_borders.crs, geometry='geometry')

    for index, row in cluster_borders.iterrows():
        poly = row['geometry']
        cluster_id = row['cluster_id']
        osmnx_gdf = osmnx.footprints.create_footprints_gdf(polygon=poly, footprint_type='building',
                                                           retain_invalid=False)
        remaining_cols = []
        columns = list(osmnx_gdf)

        if 'amenity' in columns:
            remaining_cols.append('amenity')

        if 'building' in columns:
            remaining_cols.append('building')

        remaining_cols.append('geometry')

        osmnx_gdf = osmnx_gdf[remaining_cols]
        osmnx_gdf['cluster_id'] = cluster_id

        col_names_2 = list(osmnx_gdf)

        info_list = []
        for index2, row2 in osmnx_gdf.iterrows():
            info = ''

            if 'building' in col_names_2:
                building = row2['building']
                if not is_nan(building):
                    if building != 'yes':
                        info += building + ', '

            if 'amenity' in col_names_2:
                amenity = row2['amenity']
                if not is_nan(amenity):
                    info += amenity

            info_list.append(info)

        del remaining_cols[-1]

        osmnx_gdf['type'] = 'building'
        osmnx_gdf['info'] = info_list
        osmnx_gdf.drop(columns=remaining_cols, inplace=True)

        oxg = osmnx.core.graph_from_polygon(poly, network_type='all_private', infrastructure='way["highway"]')

        gdf_edges = osmnx.save_load.graph_to_gdfs(oxg, nodes=False, edges=True, node_geometry=True,
                                                  fill_edge_geometry=True)

        columns_3 = list(gdf_edges)
        remaining_cols_3 = []

        if 'highway' in columns_3:
            remaining_cols_3.append('highway')

        if 'name' in columns_3:
            remaining_cols_3.append('name')

        if 'oneway' in columns_3:
            remaining_cols_3.append('oneway')

        remaining_cols_3.append('geometry')

        gdf_edges = gdf_edges[remaining_cols_3]
        gdf_edges['cluster_id'] = cluster_id

        info_edge_list = []
        for index2, row3 in gdf_edges.iterrows():
            info = ''

            if 'name' in columns_3:
                name = row3['name']
                if not is_nan(name):
                    if isinstance(name, list):
                        info += ','.join(name)
                    else:
                        info += name + ', '

            if 'highway' in columns_3:
                highway = row3['highway']
                if not is_nan(highway):
                    if isinstance(highway, list):
                        info += ','.join(highway)
                    else:
                        info += highway + ', '

            if 'oneway' in columns_3:
                oneway = row3['oneway']
                if not is_nan(oneway):
                    info += 'oneway'

            info_edge_list.append(info)

        del remaining_cols_3[-1]
        gdf_edges['type'] = 'Road'
        gdf_edges['info'] = info_edge_list
        gdf_edges.drop(columns=remaining_cols_3, inplace=True)

        res_gdf = concat([osmnx_gdf, gdf_edges], axis=0, join='outer', ignore_index=False,
                         keys=None, levels=None, names=None, verify_integrity=False, copy=True)
        final_gdf = concat([final_gdf, res_gdf], axis=0, join='outer', ignore_index=False,
                           keys=None, levels=None, names=None, verify_integrity=False, copy=True)

        final_gdf.reset_index(inplace=True, drop=True)

    m = map_geometries(final_gdf, tiles=tiles, width=width, height=height)

    return m
