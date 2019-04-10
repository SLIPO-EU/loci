package gr.athenarc.imsi.slipo.analytics.loci.ca;

import java.util.List;

import org.locationtech.jts.geom.Envelope;

import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;

public class UtilityScoreFunction {

	// public double[] computeScore(List<SpatialObject> spatialObjects, double
	// objectiveScoreWeight,
	// double[] maxRelScores) {
	//
	// double sumRel = 0, sumDist = 0, objectiveScore;
	//
	// for (int i = 0; i < spatialObjects.size(); i++) {
	// sumRel += spatialObjects.get(i).getScore() / maxRelScores[i];
	// }
	// sumRel /= spatialObjects.size();
	//
	// Geometry g1, g2;
	// double dist;
	// for (int i = 0; i < spatialObjects.size(); i++) {
	// for (int j = 0; j < i; j++) {
	// g1 = spatialObjects.get(i).getGeometry();
	// g2 = spatialObjects.get(j).getGeometry();
	// dist = 1 - g1.intersection(g2).getArea() / Math.min(g1.getArea(),
	// g2.getArea());
	// sumDist += dist;
	// }
	// }
	// sumDist /= spatialObjects.size() * (spatialObjects.size() - 1) / 2;
	//
	// objectiveScore = objectiveScoreWeight * sumRel + (1 -
	// objectiveScoreWeight) * sumDist;
	//
	// return new double[] { sumRel, sumDist, objectiveScore };
	// }

	// public double[] computeMarginalRelevance(List<SpatialObject>
	// spatialObjects, double relevanceWeight) {
	//
	// double[] marginalRelevance = new double[spatialObjects.size()];
	// double maxScore = spatialObjects.get(0).getScore();
	//
	// marginalRelevance[0] = 1;
	//
	// double mr, maxSim, sim;
	// for (int i = 1; i < marginalRelevance.length; i++) {
	// mr = relevanceWeight * (spatialObjects.get(i).getScore() / maxScore);
	//
	// maxSim = 0;
	// Geometry g1, g2;
	// for (int j = 0; j < i; j++) {
	// g1 = spatialObjects.get(i).getGeometry();
	// g2 = spatialObjects.get(j).getGeometry();
	// sim = g1.intersection(g2).getArea() / Math.min(g1.getArea(),
	// g2.getArea());
	// if (sim > maxSim) {
	// maxSim = sim;
	// }
	// }
	//
	// mr -= (1 - relevanceWeight) * maxSim;
	//
	// marginalRelevance[i] = mr;
	// }
	//
	// return marginalRelevance;
	// }

	public double[] computeDiscountedRelevance(List<SpatialObject> topk, double decayConstant) {

		double maxScore = topk.get(0).getScore();
		// double maxScore = 1;
		double[] discountedRelevance = new double[topk.size()];

		Envelope[] envelopes = new Envelope[topk.size()];
		for (int i = 0; i < envelopes.length; i++) {
			envelopes[i] = topk.get(i).getGeometry().getEnvelopeInternal();
		}

		double sim, maxSim;
		for (int i = 0; i < discountedRelevance.length; i++) {

			maxSim = 0;
			for (int j = 0; j < i; j++) {
				sim = envelopes[i].intersection(envelopes[j]).getArea() / envelopes[i].getArea();
				if (sim > maxSim) {
					maxSim = sim;
				}
			}

			discountedRelevance[i] = (topk.get(i).getScore() / maxScore) * Math.exp(-decayConstant * maxSim);
		}

		return discountedRelevance;
	}

	// public double computeBlockUtilityScore(List<SpatialObject> topk, Block
	// block, double relevanceWeight, double eps) {
	//
	// double maxRelevanceScore = (topk.size() > 0) ? topk.get(0).getScore() :
	// 1.0;
	// double marginalRelevance = relevanceWeight * (block.relevanceScore /
	// maxRelevanceScore);
	//
	// double maxMinSim = 0, minSim;
	// Envelope g1 = block.envelope;
	// g1.expandBy(eps / 2);
	// Envelope g2;
	//
	// for (int i = 0; i < topk.size(); i++) {
	// g2 = topk.get(i).getGeometry().getEnvelopeInternal();
	//
	// double remainingSurface = g1.getArea() - g1.intersection(g2).getArea();
	//
	// if (remainingSurface >= g2.getArea()) {
	// minSim = 0;
	// } else {
	// minSim = (g2.getArea() - remainingSurface) / g2.getArea();
	// }
	// if (minSim > maxMinSim) {
	// maxMinSim = minSim;
	// }
	// }
	//
	// marginalRelevance -= (1 - relevanceWeight) * maxMinSim;
	//
	// return marginalRelevance;
	// }

	// public double computeObjectUtilityScore(List<SpatialObject> topk,
	// SpatialObject object, double relevanceWeight,
	// double eps) {
	//
	// double maxRelevanceScore = (topk.size() > 0) ? topk.get(0).getScore() :
	// 1.0;
	// double rel =
	// Double.parseDouble(object.getAttributes().get("relevanceScore").toString());
	// double marginalRelevance = relevanceWeight * (rel / maxRelevanceScore);
	//
	// double maxSim = 0, sim;
	// Geometry g1 = object.getGeometry();
	// Geometry g2;
	//
	// for (int i = 0; i < topk.size(); i++) {
	// g2 = topk.get(i).getGeometry();
	// sim = g1.intersection(g2).getArea() / Math.min(g1.getArea(),
	// g2.getArea());
	// if (sim > maxSim) {
	// maxSim = sim;
	// }
	// }
	//
	// marginalRelevance -= (1 - relevanceWeight) * maxSim;
	//
	// return marginalRelevance;
	// }

	public double computeMaxDiscountedRelevance(List<SpatialObject> topk, Block block, double decayConstant,
			double eps) {

		Envelope[] envelopes = new Envelope[topk.size()];
		for (int i = 0; i < envelopes.length; i++) {
			envelopes[i] = topk.get(i).getGeometry().getEnvelopeInternal();
		}

		Envelope e = block.envelope;
		e.expandBy(eps / 2.0);

		double minSim, maxMinSim = 0, freeSpace, rectSize = envelopes[0].getArea();
		for (int i = 0; i < envelopes.length; i++) {

			freeSpace = e.getArea() - e.intersection(envelopes[i]).getArea();

			minSim = (freeSpace >= rectSize) ? 0 : (rectSize - freeSpace) / rectSize;

			if (minSim > maxMinSim) {
				maxMinSim = minSim;
			}
		}

		double discountedRelevance = block.relevanceScore * Math.exp(-decayConstant * maxMinSim);

		return discountedRelevance;
	}

	public double computeDiscountedRelevance(List<SpatialObject> topk, SpatialObject result, double decayConstant) {

		Envelope[] envelopes = new Envelope[topk.size()];
		for (int i = 0; i < envelopes.length; i++) {
			envelopes[i] = topk.get(i).getGeometry().getEnvelopeInternal();
		}

		Envelope e = result.getGeometry().getEnvelopeInternal();

		double sim, maxSim = 0;
		for (int i = 0; i < envelopes.length; i++) {
			sim = envelopes[i].intersection(e).getArea() / envelopes[i].getArea();
			if (sim > maxSim) {
				maxSim = sim;
			}
		}

		double rel = Double.parseDouble(result.getAttributes().get("relevanceScore").toString());
		double discountedRelevance = rel * Math.exp(-decayConstant * maxSim);

		return discountedRelevance;
	}
}