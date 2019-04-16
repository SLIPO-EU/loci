import math
from shapely.geometry import box
from scipy.stats import zscore
import geopandas as gpd
from time import time


def grid(pois, cell_width=None, cell_height=None, cell_size_ratio=0.01, znorm=False, neighborhood=False):
    """Constructs a uniform grid from the given POIs.

    If `cell_width` and `cell_height` are provided, each grid cell has size `cell_width * cell_height`.
    Otherwise, `cell_width = cell_size_ratio * area_width` and `cell_height = cell_size_ratio * area_height`,
    where `area` refers to the bounding box of `pois`.

    Each cell is assigned a `score`, which is the number of points within that cell.

    If `neighborhood` is `True`, each cell is assigned an additional score (`score_nb`), which is the total number of
    points within that cell and its adjacent cells.

    If `znorm` is True, the above scores are also provided in their z-normalized variants, `score_znorm` and
    `score_nb_znorm`.

    The constructed grid is represented by a GeoDataFrame where each row corresponds to a grid cell
    and contains the following columns:
        - `cell_id`: The id of the cell (integer computed as: `cell_x * num_columns + cell_y`)
        - `cell_x`: The row of the cell in the grid (integer).
        - `cell_y`: The column of the cell in the grid (integer).
        - `score`: see above
        - `score_nb`: see above
        - `score_znorm`: see above
        - `score_nb_znorm`: see above
        - 'contents': list of points in the cell.
        - 'geometry': Geometry column of the GeoDataFrame that contains the polygon representing the cell boundaries.

    Args:
        pois (GeoDataFrame): a POIs GeoDataFrame.
        cell_width (float): cell width.
        cell_height (float): cell height.
        cell_size_ratio (float): ratio of cell width and height to area width and height (default: 0.01).
        znorm (bool): Whether to include z-normalized scores (default: False).
        neighborhood (bool): Whether to include a total score including adjacent cells (default: False).

    Returns:
        A GeoDataFrame as described above.
    """

    t0 = time()
    orig_crs = pois.crs
    minx, miny, maxx, maxy = pois.geometry.total_bounds

    if cell_width is None:
        cell_width = cell_size_ratio * (maxx - minx)

    if cell_height is None:
        cell_height = cell_size_ratio * (maxy - miny)

    num_columns = math.ceil((maxx - minx) / cell_width)
    num_rows = math.ceil((maxy - miny) / cell_height)

    def grid_cell(poi):
        cell_x = math.floor((poi.x - minx) / cell_width)
        cell_y = math.floor((poi.y - miny) / cell_height)

        return int(cell_x * num_columns + cell_y)

    pois['cell_id'] = pois['geometry'].apply(lambda row: grid_cell(row))

    pois = pois.groupby('cell_id', sort=False)['id'].agg([list])

    def score(row):
        (cell_x, cell_y) = divmod(row.name, num_columns)

        cell_id = int(cell_x * num_columns + cell_y)
        cell_score = len(row['list'])
        geometry = box(minx + cell_x * cell_width, miny + cell_y * cell_height, minx + (cell_x + 1) * cell_width, miny
                       + (cell_y + 1) * cell_height)

        return cell_id, cell_x, cell_y, cell_score, geometry

    pois['cell_id'], pois['cell_x'], pois['cell_y'], pois['score'], pois['geometry'] = zip(*pois.apply(score, axis=1))

    pois.rename(columns={'list': 'contents'}, inplace=True)

    if znorm:
        pois['score_znorm'] = zscore(pois['score'])

    if neighborhood is True:
        # Build dict. {(x, y): score}
        cell_id_score_dict = pois.set_index(['cell_x', 'cell_y']).to_dict()['score']

        cell_id_nbsum_dict = dict()
        for key, value in cell_id_score_dict.items():
            x = key[0]
            y = key[1]
            nb_sum = 0
            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    nb_sum += cell_id_score_dict.get((i, j)) or 0

            cell_id_nbsum_dict[int(x * num_columns + y)] = nb_sum

        pois['score_nb'] = pois.index.map(cell_id_nbsum_dict)
        del cell_id_score_dict

        if znorm:
            pois['score_nb_znorm'] = zscore(pois['score_nb'])
            cols = ['cell_id', 'cell_x', 'cell_y', 'score', 'score_nb', 'score_znorm', 'score_nb_znorm', 'contents',
                    'geometry']
        else:
            cols = ['cell_id', 'cell_x', 'cell_y', 'score', 'score_nb', 'contents', 'geometry']

    else:
        if znorm:
            cols = ['cell_id', 'cell_x', 'cell_y', 'score', 'score_znorm', 'contents', 'geometry']
        else:
            cols = ['cell_id', 'cell_x', 'cell_y', 'score', 'contents', 'geometry']

    pois = pois[cols]

    gpois = gpd.GeoDataFrame(pois, crs=orig_crs, geometry=pois.geometry)

    print("Done in %0.3fs." % (time() - t0))

    return gpois, num_columns, num_rows
