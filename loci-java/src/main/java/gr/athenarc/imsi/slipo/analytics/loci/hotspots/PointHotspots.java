package gr.athenarc.imsi.slipo.analytics.loci.hotspots;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Predicate;

import gr.athenarc.imsi.slipo.analytics.loci.Grid;
import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public class PointHotspots extends HotspotFinder<POI> {

	@Override
	public List<SpatialObject> findHotspots(List<POI> pois, double eps, double neighborWeight, int topk,
			Double scoreThreshold) {
		List<SpatialObject> hotspots = new ArrayList<SpatialObject>();

		/* assign points to grid cells */
		Grid grid = new Grid(pois, eps);

		/* compute gi scores */
		double hotnessDegree, xMean = 0, xSquare = 0, sigma;
		for (POI poi : pois) {
			xMean += poi.getScore();
			xSquare += Math.pow(poi.getScore(), 2);
		}
		xMean /= pois.size();
		sigma = Math.sqrt((xSquare - pois.size() * Math.pow(xMean, 2)) / pois.size());

		List<POI> neighbors;
		double numerator, denominator;
		for (POI poi : pois) {
			neighbors = grid.getNeighbors(poi);
			numerator = poi.getScore() - xMean;
			for (POI neighbor : neighbors) {
				numerator += (neighborWeight * (neighbor.getScore() - xMean));
			}
			denominator = sigma * Math.sqrt((pois.size() * (1 + neighbors.size() * Math.pow(neighborWeight, 2))
					- Math.pow(1 + neighbors.size() * neighborWeight, 2)) / (pois.size() - 1));
			hotnessDegree = numerator / denominator;
			poi.setScore(hotnessDegree);
			hotspots.add(poi);
		}

		if (scoreThreshold != null) {
			Predicate<SpatialObject> scoreFilter = p -> p.getScore() < scoreThreshold;
			hotspots.removeIf(scoreFilter);
		}
		if (topk > 0) {
			Collections.sort(hotspots);
			hotspots = hotspots.subList(0, topk);
		}

		return hotspots;
	}
}