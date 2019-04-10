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
import gr.athenarc.imsi.slipo.analytics.loci.hotspots.HotspotFinder;
import gr.athenarc.imsi.slipo.analytics.loci.hotspots.PointHotspots;
import gr.athenarc.imsi.slipo.analytics.loci.io.InputFileParser;
import gr.athenarc.imsi.slipo.analytics.loci.io.ResultsWriter;

public class ComputePointHotspots {

	public static void main(String[] args)
			throws NumberFormatException, FileNotFoundException, IOException, ParseException {
		long startTime, endTime;

		/* load configuration file */
		Properties prop = new Properties();
		prop.load(new FileInputStream("config.properties"));

		double eps = Double.parseDouble(prop.getProperty("hs-eps"));
		double neighborWeight = Double.parseDouble(prop.getProperty("hs-neighbor_weight"));
		int topk = (prop.getProperty("hs-topk") != null) ? Integer.parseInt(prop.getProperty("hs-topk")) : 0;
		Double scoreThreshold = (prop.getProperty("hs-score_threshold") != null)
				? scoreThreshold = Double.parseDouble(prop.getProperty("hs-score_threshold")) : null;

		/* parse input file */
		System.out.print("Reading POIs from file...");
		startTime = System.nanoTime();
		InputFileParser inputFileParser = new InputFileParser(prop);
		ArrayList<POI> pois = inputFileParser.readPOIsFromFile();
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE: Number of POIs: " + pois.size() + " [" + endTime + " msec]");

		// compute point hotspots
		System.out.print("Computing hotspots...");
		startTime = System.nanoTime();
		HotspotFinder<POI> hotspotFinder = new PointHotspots();
		List<SpatialObject> hotspots = hotspotFinder.findHotspots(pois, eps, neighborWeight, topk, scoreThreshold);
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE [" + endTime + " msec]");

		// print results
		ResultsWriter resultsWriter = new ResultsWriter();
		resultsWriter.write(hotspots, prop.getProperty("hs-output_file"), prop.getProperty("csv_delimiter"));
		System.out.println("Finished writing results.");
	}
}