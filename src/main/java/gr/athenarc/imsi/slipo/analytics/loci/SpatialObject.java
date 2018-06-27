package gr.athenarc.imsi.slipo.analytics.loci;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.locationtech.jts.geom.Envelope;
import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.PrecisionModel;

public class SpatialObject implements Comparable<SpatialObject> {
	private String id;
	private String name;
	private List<String> keywords;
	private double score;
	private Geometry geometry;
	private Map<Object, Object> attributes;

	public SpatialObject(String id, String name, List<String> keywords, double score, Geometry geometry) {
		super();
		this.id = (id != null && id.length() != 0) ? id : UUID.randomUUID().toString();
		this.name = name;
		this.keywords = keywords;
		this.score = score;
		this.geometry = geometry;
		this.attributes = new HashMap<Object, Object>();
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public List<String> getKeywords() {
		return keywords;
	}

	public void setKeywords(List<String> keywords) {
		this.keywords = keywords;
	}

	public double getScore() {
		return score;
	}

	public void setScore(double score) {
		this.score = score;
	}

	public Geometry getGeometry() {
		return geometry;
	}

	public void setGeometry(Geometry geometry) {
		this.geometry = geometry;
	}

	public Map<Object, Object> getAttributes() {
		return attributes;
	}

	public void setAttributes(Map<Object, Object> attributes) {
		this.attributes = attributes;
	}

	public static <T extends SpatialObject> Envelope getEnvelope(List<T> objects) {
		GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(),
				objects.get(0).getGeometry().getSRID());
		Geometry[] geometries = new Geometry[objects.size()];
		for (int i = 0; i < geometries.length; i++) {
			geometries[i] = objects.get(i).getGeometry();
		}
		return geometryFactory.createGeometryCollection(geometries).getEnvelopeInternal();
	}

	@Override
	public int compareTo(SpatialObject o) {
		if (this.getScore() > o.getScore()) {
			return -1;
		} else if (this.getScore() == o.getScore()) {
			return 0;
		} else {
			return 1;
		}
	}
}