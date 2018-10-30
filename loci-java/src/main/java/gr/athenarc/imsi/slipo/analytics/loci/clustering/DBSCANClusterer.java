package gr.athenarc.imsi.slipo.analytics.loci.clustering;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import gr.athenarc.imsi.slipo.analytics.loci.Grid;
import gr.athenarc.imsi.slipo.analytics.loci.POI;

public class DBSCANClusterer extends Clusterer<POI> {

	protected double eps;
	protected int minPts;

	public DBSCANClusterer(final double eps, final int minPts) {
		this.eps = eps;
		this.minPts = minPts;
	}

	@Override
	public List<List<POI>> cluster(List<POI> pois) {

		Grid grid = new Grid(pois, eps);
		List<List<POI>> clusters = new ArrayList<List<POI>>();

		for (POI poi : pois) {
			if (poi.getAttributes().get("dbscan_status") != null) {
				continue;
			}
			Set<POI> neighbors = new HashSet<POI>(grid.getNeighbors(poi));
			if (neighbors.size() >= minPts) {
				List<POI> cluster = new ArrayList<POI>();
				clusters.add(expandCluster(cluster, poi, neighbors, pois, grid));
			} else {
				poi.getAttributes().put("dbscan_status", "NOISE");
			}
		}
		return clusters;
	}

	private List<POI> expandCluster(List<POI> cluster, POI poi, Set<POI> seeds, List<POI> pois, Grid grid) {
		cluster.add(poi);
		poi.getAttributes().put("dbscan_status", "PART_OF_CLUSTER");

		while (seeds.size() > 0) {
			POI current = seeds.iterator().next();
			seeds.remove(current);
			if (current.getAttributes().get("dbscan_status") == null) {
				List<POI> currentNeighbors = grid.getNeighbors(current);
				if (currentNeighbors.size() >= minPts) {
					seeds.addAll(currentNeighbors);
				}
			}

			if (current.getAttributes().get("dbscan_status") != "PART_OF_CLUSTER") {
				current.getAttributes().put("dbscan_status", "PART_OF_CLUSTER");
				cluster.add(current);
			}
		}
		return cluster;
	}
}