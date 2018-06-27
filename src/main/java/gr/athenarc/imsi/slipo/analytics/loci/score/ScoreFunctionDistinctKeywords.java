package gr.athenarc.imsi.slipo.analytics.loci.score;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public class ScoreFunctionDistinctKeywords extends ScoreFunction<SpatialObject> {

	@Override
	public double computeScore(List<SpatialObject> objects) {
		Set<String> distinctKeywords = new HashSet<String>();
		for (SpatialObject object : objects) {
			distinctKeywords.addAll(object.getKeywords());
		}
		return distinctKeywords.size();
	}
}