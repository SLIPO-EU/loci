package gr.athenarc.imsi.slipo.analytics.loci.clustering;

import java.util.ArrayList;
import java.util.List;

import org.locationtech.jts.algorithm.ConvexHull;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.MultiPoint;
import org.locationtech.jts.geom.Point;
import org.locationtech.jts.geom.PrecisionModel;

import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public abstract class Clusterer<S extends SpatialObject> {
	public abstract List<List<S>> cluster(List<S> objects);

	public List<SpatialObject> clustersToSpatialObjects(List<List<POI>> clusters, boolean printConvexHull) {
		List<SpatialObject> clusteringResults = new ArrayList<SpatialObject>();
		GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(),
				clusters.get(0).get(0).getGeometry().getSRID());
		MultiPoint multiPoint;
		ConvexHull convexHull;
		Coordinate[] coords;
		for (int i = 0; i < clusters.size(); i++) {
			if (printConvexHull) {
				coords = new Coordinate[clusters.get(i).size()];
				for (int j = 0; j < coords.length; j++) {
					coords[j] = new Coordinate(clusters.get(i).get(j).getPoint().getX(),
							clusters.get(i).get(j).getPoint().getY());
				}
				convexHull = new ConvexHull(coords, geometryFactory);
				clusteringResults.add(new SpatialObject(null, null, null, coords.length, convexHull.getConvexHull()));
			} else {
				Point[] clusterPoints = new Point[clusters.get(i).size()];
				for (int j = 0; j < clusterPoints.length; j++) {
					clusterPoints[j] = clusters.get(i).get(j).getPoint();
				}
				multiPoint = geometryFactory.createMultiPoint(clusterPoints);
				clusteringResults.add(new SpatialObject(null, null, null, clusterPoints.length, multiPoint));
			}
		}
		return clusteringResults;
	}
}