package gr.athenarc.imsi.slipo.analytics.loci.score;

import java.util.List;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public class ScoreFunctionTotalScore extends ScoreFunction<SpatialObject> {

	@Override
	public double computeScore(List<SpatialObject> objects) {
		double totalScore = 0;
		for (SpatialObject object : objects) {
			totalScore += object.getScore();
		}
		return totalScore;
	}
}