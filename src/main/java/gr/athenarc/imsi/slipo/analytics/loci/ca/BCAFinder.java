package gr.athenarc.imsi.slipo.analytics.loci.ca;

import java.util.List;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;
import gr.athenarc.imsi.slipo.analytics.loci.score.ScoreFunction;

public abstract class BCAFinder<T extends SpatialObject> {
	public abstract List<SpatialObject> findBestCatchmentAreas(List<T> pois, double eps, int topk,
			ScoreFunction<T> scoreFunction);
}