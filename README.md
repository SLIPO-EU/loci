### LOCI

LOCI is a Java library for mining Locations of Interest. It currently supports the following functionalities:

- Computation of hotspots based on the [Getis-Ord local autocorrelation statistic](http://pro.arcgis.com/en/pro-app/tool-reference/spatial-statistics/h-how-hot-spot-analysis-getis-ord-gi-spatial-stati.htm).
- Identification of the top-k fixed-size rectangular catchment areas that maximize a user-defined scoring function over the enclosed POIs.
- Density-based clustering of POIs using the [DBSCAN algorithm](https://en.wikipedia.org/wiki/DBSCAN).