package gr.athenarc.imsi.slipo.analytics.loci.score;

import java.util.List;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public class ScoreFunctionCount<T extends SpatialObject> extends ScoreFunction<T> {

	@Override
	public double computeScore(List<T> objects) {
		return objects.size();
	}
}