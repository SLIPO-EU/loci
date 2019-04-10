## LOCI

#### Overview

LOCI is a Java library for mining Locations of Interest. It currently supports the following functionalities:

- Computation of hotspots based on the [Getis-Ord local autocorrelation statistic](http://pro.arcgis.com/en/pro-app/tool-reference/spatial-statistics/h-how-hot-spot-analysis-getis-ord-gi-spatial-stati.htm).
- Identification of top-k fixed-size rectangular catchment areas that maximize a user-defined scoring function over the enclosed POIs; details presented at [D. Skoutas, D. Sacharidis, K. Patroumpas. Efficient Progressive and Diversified Top-k Best Region Search. SIGSPATIAL 2018](https://doi.org/10.1145/3274895.3274965).
- Density-based clustering of POIs using the [DBSCAN algorithm](https://en.wikipedia.org/wiki/DBSCAN).

#### Quick start

##### Installation

Get the source code: 
   `git clone https://github.com/SLIPO-EU/loci.git`

Build with Maven:
   `mvn install`

##### Configuration

The following parameters can be set in the configuration file `config.properties`:
* `input_file`: path to the input file
* `hs-output_file`, `ca-output_file`, `cl-output_file`: path to the output files for hotspots, catchment areas and clusters, respectively.
* `csv_delimiter`: delimeter used to separate the columns in the input CSV file
* `keyword_delimiter`: delimeter used to separate the keywords in the keyword column of the CSV file (optional)
* `keywords`: comma-separated list of keywords (optional); if set, only the POIs containing any of these keywords will be selected as input
* `column_id`: the position of the column containing the POI id in the CSV file (starting from 1)
* `column_name`: the position of the column containing the POI name in the CSV file (starting from 1; optional)
* `column_lon`: the position of the column containing the POI longitude in the CSV file (starting from 1)
* `column_lat`: the position of the column containing the POI latitude in the CSV file (starting from 1)
* `column_keywords`: the position of the column containing the POI keywords in the CSV file (starting from 1; optional)
* `hs-eps`: the grid resolution (cell width and height) for computing hotspots (in degrees)
* `ca-eps`, `ca-topk`: the rectangle width and height (in degrees) and the number of results to return for the best catchment areas computation
* `cl-eps`, `cl-minPts`: the eps and minPts parameter of the DBSCAN algorithm

##### Execution

1. Computation of hotspots:

   `java -cp target/loci.jar gr.athenarc.imsi.slipo.analytics.loci.showcase.ComputeCellHotspots`

2. Computation of best catchment areas:

   `java -cp target/loci.jar gr.athenarc.imsi.slipo.analytics.loci.showcase.ComputeBestCatchmentAreas`

3. Computation of clusters:

   `java -cp target/loci.jar gr.athenarc.imsi.slipo.analytics.loci.showcase.ComputeClusters`

#### Documentation

Please consult the [Javadoc](https://slipo-eu.github.io/loci/).

#### License

The contents of this project are licensed under the [Apache License 2.0](https://github.com/SLIPO-EU/loci/blob/master/LICENSE).