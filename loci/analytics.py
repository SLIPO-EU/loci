from shapely.geometry import box


def filter_by_kwd(gdf, kwd_filter, col_kwds='kwds'):
    """Returns a GeoDataFrame with only those rows that contain the specified keyword.

    Args:
        gdf (GeoDataFrame): The initial GeoDataFrame to be filtered.
        kwd_filter (string): The keyword to use for filtering.
        col_kwds (string): Name of the column containing the keywords (default: `kwds`).

    Returns:
        A GeoDataFrame with only those rows that contain `kwd_filter`.
    """

    mask = gdf[col_kwds].apply(lambda x: kwd_filter in x)
    filtered_gdf = gdf[mask]

    return filtered_gdf


def bbox(gdf):
    """Computes the bounding box of a GeoDataFrame.

    Args:
        gdf (GeoDataFrame): A GeoDataFrame.

    Returns:
        A Polygon representing the bounding box enclosing all geometries in the GeoDataFrame.
    """

    minx, miny, maxx, maxy = gdf.geometry.total_bounds
    return box(minx, miny, maxx, maxy)


def kwds_freq(gdf, col_kwds='kwds', normalized=False):
    """Computes the frequency of keywords in the provided GeoDataFrame.

    Args:
        gdf (GeoDataFrame): A GeoDataFrame with a keywords column.
        col_kwds (string) : The column containing the list of keywords (default: `kwds`).
        normalized (bool): If True, the returned frequencies are normalized in [0,1]
            by dividing with the number of rows in `gdf` (default: False).

    Returns:
        A dictionary containing for each keyword the number of rows it appears in.
    """

    kwds_ser = gdf[col_kwds]

    kwds_freq_dict = dict()
    for (index, kwds) in kwds_ser.iteritems():
        for kwd in kwds:
            if kwd in kwds_freq_dict:
                kwds_freq_dict[kwd] += 1
            else:
                kwds_freq_dict[kwd] = 1

    num_of_records = kwds_ser.size

    if normalized:
        for(kwd, freq) in kwds_freq_dict.items():
            kwds_freq_dict[kwd] = freq / num_of_records

    return kwds_freq_dict
