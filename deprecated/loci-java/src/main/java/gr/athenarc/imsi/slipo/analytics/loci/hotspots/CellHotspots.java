package gr.athenarc.imsi.slipo.analytics.loci.hotspots;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Predicate;

import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Polygon;

import gr.athenarc.imsi.slipo.analytics.loci.Grid;
import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public class CellHotspots extends HotspotFinder<POI> {

	@Override
	public List<SpatialObject> findHotspots(List<POI> pois, double eps, double neighborWeight, int topk,
			Double scoreThreshold) {
		List<SpatialObject> hotspots = new ArrayList<SpatialObject>();

		/* assign points to grid cells */
		Grid grid = new Grid(pois, eps);
		System.out.println("Number of grid cells: " + grid.getNumberOfCells());

		/* compute cell scores */
		double cellScore;
		int cellCount = 0;
		Map<Integer, Map<Integer, Double>> cellScores = new HashMap<Integer, Map<Integer, Double>>();
		List<POI> cellContents;
		for (Integer row : grid.getCells().keySet()) {
			for (Integer column : grid.getCells().get(row).keySet()) {
				cellCount++;
				cellScore = 0;
				cellContents = grid.getCells().get(row).get(column);
				for (POI poi : cellContents) {
					cellScore += poi.getScore();
				}
				if (cellScores.get(row) == null) {
					cellScores.put(row, new HashMap<Integer, Double>());
				}
				cellScores.get(row).put(column, cellScore);
			}
		}

		/* compute gi scores */
		double hotnessDegree, xMean = 0, xSquare = 0, sigma;
		for (Integer row : cellScores.keySet()) {
			for (Integer column : cellScores.get(row).keySet()) {
				cellScore = cellScores.get(row).get(column);
				xMean += cellScore;
				xSquare += Math.pow(cellScore, 2);
			}
		}
		xMean /= cellCount;
		sigma = Math.sqrt((xSquare - cellCount * Math.pow(xMean, 2)) / cellCount);

		double numerator, denominator;
		List<Double> neighborScores;
		Polygon cellBorder;
		GeometryFactory geometryFactory = new GeometryFactory(pois.get(0).getPoint().getPrecisionModel(),
				pois.get(0).getPoint().getSRID());
		for (Integer row : cellScores.keySet()) {
			for (Integer column : cellScores.get(row).keySet()) {
				cellScore = cellScores.get(row).get(column);
				neighborScores = new ArrayList<Double>();
				for (int i = row - 1; i <= row + 1; i++) {
					for (int j = column - 1; j <= column + 1; j++) {
						if (!(i == row && j == column) && cellScores.get(i) != null
								&& cellScores.get(i).get(j) != null) {
							neighborScores.add(cellScores.get(i).get(j));
						}
					}
				}
				numerator = cellScore - xMean;
				for (double d : neighborScores) {
					numerator += (neighborWeight * (d - xMean));
				}
				denominator = sigma * Math.sqrt((cellCount * (1 + neighborScores.size() * Math.pow(neighborWeight, 2))
						- Math.pow(1 + neighborScores.size() * neighborWeight, 2)) / (cellCount - 1));
				hotnessDegree = numerator / denominator;
				cellBorder = grid.cellIndexToGeometry(row, column, geometryFactory);
				hotspots.add(new SpatialObject(row + ":" + column, "", null, hotnessDegree, cellBorder));
			}
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