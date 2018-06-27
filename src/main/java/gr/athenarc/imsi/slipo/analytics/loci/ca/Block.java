package gr.athenarc.imsi.slipo.analytics.loci.ca;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.locationtech.jts.geom.Envelope;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;

import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.score.ScoreFunction;

public class Block implements Comparable<Block> {

	public static final int BLOCK_ORIENTATION_HORIZONTAL = 0;
	public static final int BLOCK_ORIENTATION_VERTICAL = 1;
	public static final int BLOCK_ORIENTATION_NONE = -1;

	public static final int BLOCK_TYPE_CELL = 0;
	public static final int BLOCK_TYPE_SLAB = 1;
	public static final int BLOCK_TYPE_REGION = 2;

	public static final int EXPAND_BACKWARD = 0;
	public static final int EXPAND_FORWARD = 1;
	public static final int EXPAND_BOTH = 2;
	public static final int EXPAND_NONE = -1;

	public List<POI> pois;
	public double utilityScore, relevanceScore;
	public Envelope envelope;
	public List<Rectangle> orderedRectangles;
	public int type, orientation, expansion;
	public ScoreFunction<POI> scoreFunction;
	public double eps;
	public int precedingResults;
	public int expandLeft, expandRight;

	private GeometryFactory geometryFactory;

	public Block(List<POI> pois, ScoreFunction<POI> scoreFunction, int type, int orientation, int expansion, double eps,
			GeometryFactory geometryFactory) {
		this.geometryFactory = geometryFactory;
		this.pois = new ArrayList<POI>(pois);
		this.scoreFunction = scoreFunction;
		this.eps = eps;
		this.relevanceScore = scoreFunction.computeScore(pois);
		this.utilityScore = this.relevanceScore;
		this.envelope = computeEnvelope(pois);
		this.type = type;
		this.orientation = orientation;
		this.expansion = expansion;
		if (orientation != BLOCK_ORIENTATION_NONE) {
			this.orderedRectangles = computeOrderedRectangles(orientation, eps);
		}
		this.precedingResults = 0;
	}

	private Envelope computeEnvelope(List<POI> pois) {
		Point[] points = new Point[pois.size()];
		for (int i = 0; i < points.length; i++) {
			points[i] = pois.get(i).getPoint();
		}
		Envelope envelope = geometryFactory.createGeometryCollection(points).getEnvelopeInternal();
		return envelope;
	}

	private List<Rectangle> computeOrderedRectangles(int orientation, double eps) {

		double center;
		List<Rectangle> rectangles = new ArrayList<Rectangle>();

		// create rectangles
		for (POI p : pois) {
			center = (orientation == BLOCK_ORIENTATION_HORIZONTAL) ? p.getPoint().getX() : p.getPoint().getY();
			rectangles.add(new Rectangle(center - eps / 2, true, p));
			rectangles.add(new Rectangle(center + eps / 2, false, p));
		}

		// order rectangles
		Collections.sort(rectangles);

		return rectangles;
	}

	public Block[] getSubBlocks() {
		Block[] derivedBlocks = new Block[]{};

		if (expandLeft > 0 && expandRight > 0) {
			derivedBlocks = new Block[2];
			List<POI> leftSublist = new ArrayList<POI>(pois);
			leftSublist.remove(pois.size() - 1);
			List<POI> rightSublist = new ArrayList<POI>(pois);
			rightSublist.remove(0);
			derivedBlocks[0] = new Block(leftSublist, scoreFunction, type, orientation, EXPAND_BACKWARD, eps,
					geometryFactory);
			derivedBlocks[0].expandLeft = expandLeft - 1;
			derivedBlocks[0].expandRight = 0;

			derivedBlocks[1] = new Block(rightSublist, scoreFunction, type, orientation, EXPAND_FORWARD, eps,
					geometryFactory);
			derivedBlocks[1].expandRight = expandRight - 1;
			derivedBlocks[1].expandLeft = 0;
		} else if (expandLeft > 0) {
			derivedBlocks = new Block[1];
			List<POI> leftSublist = new ArrayList<POI>(pois);
			leftSublist.remove(pois.size() - 1);
			derivedBlocks[0] = new Block(leftSublist, scoreFunction, type, orientation, EXPAND_BACKWARD, eps,
					geometryFactory);
			derivedBlocks[0].expandLeft = expandLeft - 1;
		} else if (expandRight > 0) {
			derivedBlocks = new Block[1];
			List<POI> rightSublist = new ArrayList<POI>(pois);
			rightSublist.remove(0);
			derivedBlocks[0] = new Block(rightSublist, scoreFunction, type, orientation, EXPAND_FORWARD, eps,
					geometryFactory);
			derivedBlocks[0].expandRight = expandRight - 1;
		}

		return derivedBlocks;
	}

	public List<Block> sweep() {
		List<Block> blocks = new ArrayList<Block>();

		List<POI> pois = new ArrayList<POI>();
		boolean isMin = true;
		int expandLeft = 0, expandRight = 0;
		Block block = null;

		for (Rectangle r : orderedRectangles) {
			if (r.isMin) {
				if (!isMin) {
					block.expandRight = expandRight;
					expandRight = 0;
					blocks.add(block);
				}
				pois.add(r.p);
				expandLeft++;
				isMin = true;
			} else {
				if (isMin) {
					block = new Block(pois, scoreFunction, type + 1, Block.BLOCK_ORIENTATION_HORIZONTAL, EXPAND_BOTH,
							eps, geometryFactory);
					block.expandLeft = expandLeft;
					expandLeft = 0;
				}
				pois.remove(r.p);
				expandRight++;
				isMin = false;
			}
		}

		// at the end of the sweep, add the last pending block
		block.expandRight = expandRight;
		expandRight = 0;
		blocks.add(block);

		return blocks;
	}

	public List<Block> sweepExhaustive() {
		List<Block> blocks = new ArrayList<Block>();

		List<POI> pois = new ArrayList<POI>();
		// boolean isMin = true;

		for (Rectangle r : orderedRectangles) {
			if (r.isMin) {
				pois.add(r.p);
				blocks.add(new Block(pois, scoreFunction, type + 1, Block.BLOCK_ORIENTATION_HORIZONTAL, EXPAND_NONE,
						eps, geometryFactory));
				// isMin = true;
			} else {
				// if (isMin) {
				// blocks.add(new Block(pois, scoreFunction, type + 1,
				// Block.BLOCK_ORIENTATION_HORIZONTAL, eps,
				// geometryFactory));
				// }
				pois.remove(r.p);
				blocks.add(new Block(pois, scoreFunction, type + 1, Block.BLOCK_ORIENTATION_HORIZONTAL, EXPAND_NONE,
						eps, geometryFactory));
				// isMin = false;
			}
		}

		return blocks;
	}

	@Override
	public int compareTo(Block r) {
		if (this.utilityScore > r.utilityScore) {
			return -1;
		} else if (this.utilityScore < r.utilityScore) {
			return 1;
		} else {
			if (this.type >= r.type) {
				return -1;
			} else {
				return 1;
			}
		}
	}
}