package gr.athenarc.imsi.slipo.analytics.loci.showcase;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;
import gr.athenarc.imsi.slipo.analytics.loci.clustering.Clusterer;
import gr.athenarc.imsi.slipo.analytics.loci.clustering.DBSCANClusterer;
import gr.athenarc.imsi.slipo.analytics.loci.io.InputFileParser;
import gr.athenarc.imsi.slipo.analytics.loci.io.ResultsWriter;

public class ComputeClusters {

	public static void main(String[] args)
			throws NumberFormatException, FileNotFoundException, IOException, ParseException {
		long startTime, endTime;

		/* load configuration file */
		Properties prop = new Properties();
		prop.load(new FileInputStream("config.properties"));

		double eps = Double.parseDouble(prop.getProperty("cl-eps"));
		int minPts = Integer.parseInt(prop.getProperty("cl-minPts"));

		/* parse input file */
		System.out.print("Reading POIs from file...");
		startTime = System.nanoTime();
		InputFileParser inputFileParser = new InputFileParser(prop);
		ArrayList<POI> pois = inputFileParser.readPOIsFromFile();
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE: Number of POIs: " + pois.size() + " [" + endTime + " msec]");

		// compute clusters
		System.out.print("Clustering POIs...");
		startTime = System.nanoTime();
		Clusterer<POI> clusterer = new DBSCANClusterer(eps, minPts);
		List<List<POI>> clusters = clusterer.cluster(pois);
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE: Number of clusters: " + clusters.size() + " [" + endTime + " msec]");

		// print results
		boolean printConvexHull = prop.getProperty("cl-print_clusters_convex_hull") != null
				&& prop.getProperty("cl-print_clusters_convex_hull").trim().equalsIgnoreCase("true");
		List<SpatialObject> clusteringResults = clusterer.clustersToSpatialObjects(clusters, printConvexHull);
		ResultsWriter resultsWriter = new ResultsWriter();
		resultsWriter.write(clusteringResults, prop.getProperty("cl-output_file"), prop.getProperty("csv_delimiter"));
		System.out.println("Finished printing results.");
	}
}