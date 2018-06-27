package gr.athenarc.imsi.slipo.analytics.loci;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Polygon;

public class Grid {

	private Map<Integer, Map<Integer, List<POI>>> cells;
	private double offsetX, offsetY, eps, minX = Double.POSITIVE_INFINITY, minY = Double.POSITIVE_INFINITY,
			maxX = Double.NEGATIVE_INFINITY, maxY = Double.NEGATIVE_INFINITY;
	private int numberOfCells;

	public Grid(List<POI> pois, double eps) {
		int maxCellSize = 0;
		numberOfCells = 0;
		this.eps = eps;
		cells = new HashMap<Integer, Map<Integer, List<POI>>>();
		int i, j;
		offsetX = pois.get(0).getPoint().getX();
		offsetY = pois.get(0).getPoint().getY();
		for (POI poi : pois) {
			i = (int) Math.floor((poi.getPoint().getX() - offsetX) / eps);
			j = (int) Math.floor((poi.getPoint().getY() - offsetY) / eps);
			if (cells.get(i) == null) {
				cells.put(i, new HashMap<Integer, List<POI>>());
			}
			if (cells.get(i).get(j) == null) {
				cells.get(i).put(j, new ArrayList<POI>());
				numberOfCells++;
			}
			cells.get(i).get(j).add(poi);
			
			if (cells.get(i).get(j).size() > maxCellSize) {
				maxCellSize = cells.get(i).get(j).size();
			}

			minX = Math.min(minX, poi.getPoint().getX());
			maxX = Math.max(maxX, poi.getPoint().getX());
			minY = Math.min(minY, poi.getPoint().getY());
			maxY = Math.max(maxY, poi.getPoint().getY());
		}
		
		// print some grid statistics
		System.out.println("Number of cells: " + numberOfCells);
		System.out.println("Max points per cell: " + maxCellSize);
		System.out.println("minX: " + minX);
		System.out.println("maxX: " + maxX);
		System.out.println("minY: " + minY);
		System.out.println("maxY: " + maxY);
	}

	public List<POI> getNeighbors(POI poi) {
		List<POI> neighbors = new ArrayList<POI>();
		int i = (int) Math.floor((poi.getPoint().getX() - offsetX) / eps);
		int j = (int) Math.floor((poi.getPoint().getY() - offsetY) / eps);
		for (int i1 = i - 1; i1 <= i + 1; i1++) {
			for (int j1 = j - 1; j1 <= j + 1; j1++) {
				if (cells.get(i1) != null && cells.get(i1).get(j1) != null) {
					for (POI neighbor : cells.get(i1).get(j1)) {
						if (!poi.getId().equals(neighbor.getId())
								&& Math.abs(poi.getPoint().getX() - neighbor.getPoint().getX()) <= eps
								&& Math.abs(poi.getPoint().getY() - neighbor.getPoint().getY()) <= eps) {
							neighbors.add(neighbor);
						}
					}
				}
			}
		}
		return neighbors;
	}

	public Map<Integer, Map<Integer, List<POI>>> getCells() {
		return cells;
	}

	public double getOffsetX() {
		return offsetX;
	}

	public double getOffsetY() {
		return offsetY;
	}

	public double getEps() {
		return eps;
	}

	public double getMinX() {
		return minX;
	}

	public double getMinY() {
		return minY;
	}

	public double getMaxX() {
		return maxX;
	}

	public double getMaxY() {
		return maxY;
	}

	public int getNumberOfCells() {
		return numberOfCells;
	}

	public Polygon cellIndexToGeometry(Integer row, Integer column, GeometryFactory geometryFactory) {
		double lon = row * eps + offsetX;
		double lat = column * eps + offsetY;
		Coordinate ll = new Coordinate(lon, lat);
		Coordinate lr = new Coordinate(lon + eps, lat);
		Coordinate ur = new Coordinate(lon + eps, lat + eps);
		Coordinate ul = new Coordinate(lon, lat + eps);
		Coordinate[] coords = new Coordinate[] { ll, lr, ur, ul, ll };
		Polygon border = geometryFactory.createPolygon(coords);
		return border;
	}
}