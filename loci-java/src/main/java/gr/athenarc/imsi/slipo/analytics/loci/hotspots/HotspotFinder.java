package gr.athenarc.imsi.slipo.analytics.loci.hotspots;

import java.util.List;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public abstract class HotspotFinder<S extends SpatialObject> {
	public abstract List<SpatialObject> findHotspots(List<S> objects, double eps, double neighborWeight, int topk,
			Double scoreThreshold);
}