import pandas as pd
import geopandas as gpd
from shapely.geometry import box, GeometryCollection
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori


def filter_by_kwd(df, kwd_filter, col_kwds='kwds'):
    """Returns a DataFrame with only those rows that contain the specified keyword.

    Args:
        df (DataFrame): The initial DataFrame to be filtered.
        kwd_filter (string): The keyword to use for filtering.
        col_kwds (string): Name of the column containing the keywords (default: `kwds`).

    Returns:
        A GeoDataFrame with only those rows that contain `kwd_filter`.
    """

    mask = df[col_kwds].apply(lambda x: kwd_filter in x)
    filtered_gdf = df[mask]

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


def freq_locationsets(location_visits, location_id_col, locations, locationset_id_col, min_sup, min_length):
    """Computes frequently visited sets of locations based on frequent itemset mining.

        Args:
             location_visits (DataFrame): A DataFrame with location ids and locationset ids.
             location_id_col (String): The name of the column containing the location ids.
             locationset_id_col (String): The name of the column containing the locationsets ids.
             locations (GeoDataFrame): A GeoDataFrame containing the geometries of the locations.
             min_sup (float): The minimum support threshold.
             min_length (int): Minimum length of itemsets to be returned.

        Returns:
            A GeoDataFrame with the support, length and geometry of the computed location sets.
    """

    itemsets = location_visits.groupby([locationset_id_col], sort=False)[location_id_col].agg(set)
    te = TransactionEncoder()
    oht_ary = te.fit(itemsets).transform(itemsets.values, sparse=True)
    sparse_df = pd.SparseDataFrame(oht_ary, columns=te.columns_, default_fill_value=False)

    apriori_df = apriori(sparse_df, min_support=min_sup, use_colnames=True)
    apriori_df['length'] = apriori_df['itemsets'].apply(lambda x: len(x))

    apriori_df = apriori_df[(apriori_df['length'] >= min_length)]

    def cluster_id_to_geom(row):
        polylist = [locations.loc[c].geometry for c in row]
        return GeometryCollection(polylist)

    apriori_df['geometry'] = apriori_df['itemsets'].apply(lambda x: cluster_id_to_geom(x))

    apriori_df = gpd.GeoDataFrame(apriori_df, crs=locations.crs, geometry=apriori_df.geometry)
    apriori_df.rename(columns={'itemsets': 'location_ids'}, inplace=True)

    return apriori_df
