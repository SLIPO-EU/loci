import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from loci.analytics import bbox


def map_pois(pois, tiles='OpenStreetMap', width='100%', height='100%', show_bbox=False):
    """Returns a Folium Map showing the contents of the provided POIs GeoDataFrame.
    Map center and zoom level are set automatically.

    Args:
         pois (GeoDataFrame): A GeoDataFrame containing the POIs to be displayed.
         tiles (string): The tiles to use for the map (default: `OpenStreetMap`).
         width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
         height (integer or percentage): Height of the map in pixels or percentage (default: 100%).
         show_bbox (bool): Whether to show the bounding box of the GeoDataFrame (default: False).

    Returns:
        A Folium Map object displaying the given POIs.
    """

    if pois.crs['init'] != '4326':
        pois = pois.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the bounding box enclosing the POIs.
    bb = bbox(pois)
    map_center = [bb.centroid.y, bb.centroid.x]

    m = folium.Map(location=map_center, tiles=tiles, width=width, height=height)

    # Automatically set zoom level
    m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    folium.GeoJson(pois, tooltip=folium.features.GeoJsonTooltip(fields=['id', 'name', 'kwds'],
                                                                aliases=['ID:', 'Name:', 'Keywords:'])).add_to(m)
    if show_bbox:
        folium.GeoJson(bb).add_to(m)

    return m


def barchart(data,
             orientation='Vertical',
             x_axis_label='',
             y_axis_label='',
             plot_title='',
             bar_width=0.5,
             plot_width=15,
             plot_height=5,
             top_k=10
             ):
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
        plt.barh(y_pos, performance, width=bar_width, align='center', alpha=0.5)
        plt.yticks(y_pos, objects)

    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_label)
    plt.title(plot_title)

    return plt


def heatmap(pois, width='100%', height='100%', radius=10):
    """Generates a heatmap of the input POIs.

    Args:
        pois (GeoDataFrame): A POIs GeoDataFrame.
        width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
        height (integer or percentage): Height of the map in pixels or percentage (default: 100%).
        radius (float): Radius of each point of the heatmap (default: 10).

    Returns:
        A Folium Map object displaying the heatmap generated from the POIs.
    """

    if pois.crs['init'] != '4326':
        pois = pois.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the gdf's bounding box
    bb = bbox(pois)
    map_center = [bb.centroid.y, bb.centroid.x]

    heat_map = folium.Map(location=map_center, width=width, height=height)

    # Automatically set zoom level
    heat_map.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    # List comprehension to make list of lists
    heat_data = [[row['geometry'].y, row['geometry'].x] for index, row in pois.iterrows()]

    # Plot it on the map
    HeatMap(heat_data, radius=radius).add_to(heat_map)

    return heat_map


def map_grid(g, score_column='score', percentiles=(0.5, 0.8, 0.9, 0.95, 0.98, 0.99), width='100%', height='100%',
             colormap='YlOrRd', opacity=0.7):
    """Displays a grid as a choropleth map.

    Args:
        g (GeoDataFrame): A GeoDataFrame representing the grid index.
        score_column (string): Name of the column containing the score to use for the choropleth map (default: score).
        percentiles (array): The percentiles to use for the scale of the choropleth map.
        width (integer or percentage): Width of the map in pixels or percentage (default: 100%).
        height (integer or percentage): Height of the map in pixels or percentage (default: 100%).
        colormap (string): A string indicating a Matplotlib colormap (default: YlOrRd).
        opacity (float): Opacity (default: 0.7).

    Returns:
        A Folium Map object displaying the grid as a choropleth map.
    """

    if g.crs['init'] != '4326':
        g = g.to_crs({'init': 'epsg:4326'})

    # Automatically center the map at the center of the grid's bounding box
    bb = bbox(g)
    map_center = [bb.centroid.y, bb.centroid.x]
    m = folium.Map(location=map_center, width=width, height=height)

    scale_min, scale_max = g[score_column].values.min(), g[score_column].values.max()
    bins = g[score_column].quantile(percentiles).values
    bins = np.insert(bins, 0, scale_min, axis=0)
    bins = np.append(bins, scale_max)
    ch = folium.Choropleth(g, data=g, key_on='feature.properties.cell_id', columns=['cell_id', score_column],
                           threshold_scale=bins, fill_color=colormap, fill_opacity=opacity)

    ch.add_to(m)

    # Automatically set zoom level
    m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    return m
