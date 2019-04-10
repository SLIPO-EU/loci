package gr.athenarc.imsi.slipo.analytics.loci;

import java.util.List;

import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;

public class POI extends SpatialObject {

	public POI(String id, String name, double x, double y, List<String> keywords, double score,
			GeometryFactory geometryFactory) {
		super(id, name, keywords, score, geometryFactory.createPoint(new Coordinate(x, y)));
	}

	public Point getPoint() {
		return (Point) getGeometry();
	}

	public void setPoint(Point point) {
		super.setGeometry(point);
	}
}