package gr.athenarc.imsi.slipo.analytics.loci.ca;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.PriorityQueue;

import org.locationtech.jts.geom.Envelope;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.PrecisionModel;

import gr.athenarc.imsi.slipo.analytics.loci.Grid;
import gr.athenarc.imsi.slipo.analytics.loci.POI;
import gr.athenarc.imsi.slipo.analytics.loci.SpatialObject;
import gr.athenarc.imsi.slipo.analytics.loci.score.ScoreFunction;

public class BCAIndexProgressive extends BCAFinder<POI> {

	private boolean distinctMode;
	private GeometryFactory geometryFactory;
	private long overallStartTime, resultEndTime;

	public BCAIndexProgressive(boolean distinctMode) {
		super();
		this.distinctMode = distinctMode;
	}

	@Override
	public List<SpatialObject> findBestCatchmentAreas(List<POI> pois, double eps, int k,
			ScoreFunction<POI> scoreFunction) {

		geometryFactory = new GeometryFactory(new PrecisionModel(), pois.get(0).getPoint().getSRID());
		long startTime, endTime;

		overallStartTime = System.nanoTime();

		// list to hold the top-k results
		List<SpatialObject> topk = new ArrayList<SpatialObject>();

		/* Assign points to grid cells. */
		System.out.println("Creating the grid...");
		startTime = System.nanoTime();
		Grid grid = new Grid(pois, eps);
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE [" + endTime + " msec]");

		/* Insert grid cells in a priority queue. */
		System.out.println("Initializing the queue...");
		startTime = System.nanoTime();
		PriorityQueue<Block> queue = initQueue(grid, scoreFunction, eps);
		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE [" + endTime + " msec]");
		// int maxQueueSize = queue.size();

		/* Process the queue. */
		Block block;
		System.out.println("Processing the queue...");
		startTime = System.nanoTime();

		while (topk.size() < k && !queue.isEmpty()) {

			// get the top block from the queue
			block = queue.poll();
			processBlock(block, eps, scoreFunction, queue, topk);

			// maxQueueSize = Math.max(maxQueueSize, queue.size());
		}

		endTime = (System.nanoTime() - startTime) / 1000000;
		System.out.println(" DONE [" + endTime + " msec]");
		// System.out.println("Max queue size: " + maxQueueSize);

		return topk;
	}

	private PriorityQueue<Block> initQueue(Grid grid, ScoreFunction<POI> scoreFunction, double eps) {

		PriorityQueue<Block> queue = new PriorityQueue<Block>();

		List<POI> cellPois;
		Block block;
		Envelope cellBoundary;

		/* Iterate over the cells and compute an upper bound for each cell. */
		for (Integer row : grid.getCells().keySet()) {
			for (Integer column : grid.getCells().get(row).keySet()) {

				cellBoundary = grid.cellIndexToGeometry(row, column, geometryFactory).getEnvelopeInternal();
				cellBoundary.expandBy(0.5 * eps);

				cellPois = new ArrayList<POI>();
				for (int i = row - 1; i <= row + 1; i++) {
					for (int j = column - 1; j <= column + 1; j++) {
						if (grid.getCells().get(i) != null && grid.getCells().get(i).get(j) != null) {
							for (POI p : grid.getCells().get(i).get(j)) {
								if (cellBoundary.intersects(p.getPoint().getCoordinate())) {
									cellPois.add(p);
								}
							}
						}
					}
				}

				block = new Block(cellPois, scoreFunction, Block.BLOCK_TYPE_CELL, Block.BLOCK_ORIENTATION_VERTICAL,
						Block.EXPAND_NONE, eps, geometryFactory);

				queue.add(block);
			}
		}

		return queue;
	}

	private void processBlock(Block block, double eps, ScoreFunction<POI> scoreFunction, PriorityQueue<Block> queue,
			List<SpatialObject> topk) {

		// int pointsBefore = block.pois.size();

		// if (distinctMode) {
		// removeOverlappingPoints(block, topk);
		// }

		// if (block.pois.size() < pointsBefore) {
		// // recreate block and reinsert it in the queue
		// block = new Block(block.pois, scoreFunction, block.type,
		// block.orientation, eps, geometryFactory);
		// queue.add(block);
		// } else {
		if (block.type == Block.BLOCK_TYPE_REGION) {
			inspectResult(block, eps, topk);
		} else {
			List<Block> newBlocks = block.sweep();
			queue.addAll(newBlocks);
		}

		// insert the two derived sub-blocks in the queue
		if ((block.type == Block.BLOCK_TYPE_SLAB || block.type == Block.BLOCK_TYPE_REGION) && block.pois.size() > 1) {
			Block[] derivedBlocks = block.getSubBlocks();
			for (int i = 0; i < derivedBlocks.length; i++) {
				queue.add(derivedBlocks[i]);
			}
		}
		// }
	}

	private void inspectResult(Block block, double eps, List<SpatialObject> topk) {
		// generate candidate result
		Envelope e = geometryFactory.createPoint(block.envelope.centre()).getEnvelopeInternal();
		e.expandBy(eps / 2); // with fixed size eps

		// Envelope e = block.envelope; // with tight mbr

		// if this result is valid, add it to top-k
		boolean isDistinct = true;
		if (distinctMode) {
			for (SpatialObject so : topk) {
				if (e.intersects(so.getGeometry().getEnvelopeInternal())) {
					isDistinct = false;
					break;
				}
			}
		}
		if (isDistinct) {
			SpatialObject result = new SpatialObject(block.envelope.centre().x + ":" + block.envelope.centre().y, null,
					null, block.utilityScore, geometryFactory.toGeometry(e));
			result.setAttributes(new HashMap<Object, Object>());
			result.getAttributes().put("coveredPoints", block.pois);

			resultEndTime = (System.nanoTime() - overallStartTime) / 1000000;
			result.getAttributes().put("executionTime", resultEndTime);
			topk.add(result);

			System.out.println("Results so far: " + topk.size());
		}
	}

	@SuppressWarnings("unused")
	private void removeOverlappingPoints(Block block, List<SpatialObject> topk) {
		/*
		 * Check if any existing results overlap with this block. If so, remove
		 * common points.
		 */
		List<SpatialObject> overlappingResults = new ArrayList<SpatialObject>(topk);
		Envelope border = block.envelope;
		overlappingResults.removeIf(p -> !border.intersects(p.getGeometry().getEnvelopeInternal()));

		for (SpatialObject r : overlappingResults) {
			block.pois.removeIf(p -> r.getGeometry().covers(p.getPoint()));
		}
	}

	public boolean getDistinctMode() {
		return distinctMode;
	}

	public void setDistinctMode(boolean distinctMode) {
		this.distinctMode = distinctMode;
	}
}