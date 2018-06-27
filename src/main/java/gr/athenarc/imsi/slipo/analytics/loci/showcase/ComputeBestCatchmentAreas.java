package gr.athenarc.imsi.slipo.analytics.loci.showcase;

import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.text.ParseException;
import java.util.List;
import java.util.Properties;

import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;
import gr.athenarc.imsi.slipo.analytics.loci.ca.BCAFinder;
import gr.athenarc.imsi.slipo.analytics.loci.ca.BCAIndexProgressive;
import gr.athenarc.imsi.slipo.analytics.loci.ca.BCAIndexProgressiveDiv;
import gr.athenarc.imsi.slipo.analytics.loci.ca.BCAIndexProgressiveDivExhaustive;
import gr.athenarc.imsi.slipo.analytics.loci.ca.UtilityScoreFunction;
import gr.athenarc.imsi.slipo.analytics.loci.io.InputFileParser;
import gr.athenarc.imsi.slipo.analytics.loci.io.ResultsWriter;
import gr.athenarc.imsi.slipo.analytics.loci.score.ScoreFunction;
import gr.athenarc.imsi.slipo.analytics.loci.score.ScoreFunctionCount;

public class ComputeBestCatchmentAreas {

	public static void main(String[] args)
			throws NumberFormatException, FileNotFoundException, IOException, ParseException {
		long startTime, endTime;

		/* load configuration file */
		Properties prop = new Properties();
		prop.load(new FileInputStream("config.properties"));

		double eps = Double.parseDouble(prop.getProperty("ca-eps"));
		int topk = Integer.parseInt(prop.getProperty("ca-topk"));
		boolean distinct = Boolean.parseBoolean(prop.getProperty("ca-distinct"));
		boolean div = Boolean.parseBoolean(prop.getProperty("ca-div"));
		boolean exhaustive = Boolean.parseBoolean(prop.getProperty("ca-exhaustive"));
		double decayConstant = Double.parseDouble(prop.getProperty("ca-decay-constant"));
		// boolean printResults =
		// Boolean.parseBoolean(prop.getProperty("ca-print-results"));
		boolean printResults = true;

		/* parse input file */
		System.out.print("Reading POIs from file...");
		startTime = System.nanoTime();
		InputFileParser inputFileParser = new InputFileParser(prop);
		List<POI> pois = inputFileParser.readPOIsFromFile();
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE: Number of POIs: " + pois.size() + " [" + endTime + " msec]");

		ScoreFunction<POI> scoreFunction = new ScoreFunctionCount<POI>();
		List<SpatialObject> bca;
		BCAFinder<POI> bcaFinder;
		UtilityScoreFunction utilityScoreFunction = new UtilityScoreFunction();

		// compute best catchment areas
		System.out.print("Computing best catchment areas...\n");
		startTime = System.nanoTime();
		if (exhaustive) {
			bcaFinder = new BCAIndexProgressiveDivExhaustive(decayConstant, utilityScoreFunction);
		} else if (div) {
			bcaFinder = new BCAIndexProgressiveDiv(decayConstant, utilityScoreFunction);
		} else {
			bcaFinder = new BCAIndexProgressive(distinct);
		}
		bca = bcaFinder.findBestCatchmentAreas(pois, eps, topk, scoreFunction);
		// endTime = (System.nanoTime() - startTime) / 1000000;
		// System.out.println(" DONE [ # " + endTime + " msec # ]");
		double endTimeSec = (System.nanoTime() - startTime) / 1000000000.0;
		System.out.println(" DONE [ # " + endTimeSec + " sec # ]");

		// compute utility score
		double[] marginalRelevance = utilityScoreFunction.computeDiscountedRelevance(bca, decayConstant);
		System.out.println("\nMarginal relevance for decay constant: " + decayConstant);
		for (int i = 0; i < marginalRelevance.length; i++) {
			System.out.println(marginalRelevance[i]);
		}

		if (printResults) {
			// print results
			ResultsWriter resultsWriter = new ResultsWriter();
			resultsWriter.write(bca, prop.getProperty("ca-output_file"), prop.getProperty("csv_delimiter"));
			System.out.println("Finished writing results.\n");
		}
	}
}