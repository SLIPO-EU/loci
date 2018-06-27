package gr.athenarc.imsi.slipo.analytics.loci.score;

import java.util.List;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public abstract class ScoreFunction<T extends SpatialObject> {
	public abstract double computeScore(List<T> objects);
}