package gr.athenarc.imsi.slipo.analytics.loci.io;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Properties;
import java.util.StringTokenizer;

import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.PrecisionModel;

import gr.athenarc.imsi.slipo.analytics.loci.POI;

public class InputFileParser {

	private Properties prop;

	public InputFileParser(Properties prop) {
		this.prop = prop;
	}

	public ArrayList<POI> readPOIsFromFile() throws IOException {
		ArrayList<POI> pois = new ArrayList<POI>();

		POI poi;
		BufferedReader bufferedReader = new BufferedReader(new FileReader(prop.getProperty("input_file")));
		String name, line, kwds, id;
		StringTokenizer strTok;
		ArrayList<String> keywords;
		HashSet<String> filterKeywords = new HashSet<String>();
		String[] csvColumns;
		double x, y, score;

		int columnID = -1, columnName = -1, columnKeywords = -1, columnScore = -1, columnLon = -1, columnLat = -1;
		if (prop.getProperty("column_id") != null) {
			columnID = Integer.parseInt(prop.getProperty("column_id")) - 1;
		}
		if (prop.getProperty("column_name") != null) {
			columnName = Integer.parseInt(prop.getProperty("column_name")) - 1;
		}
		if (prop.getProperty("column_keywords") != null) {
			columnKeywords = Integer.parseInt(prop.getProperty("column_keywords")) - 1;
		}
		if (prop.getProperty("column_score") != null) {
			columnScore = Integer.parseInt(prop.getProperty("column_score")) - 1;
		}
		if (prop.getProperty("column_lon") != null) {
			columnLon = Integer.parseInt(prop.getProperty("column_lon")) - 1;
		}
		if (prop.getProperty("column_lat") != null) {
			columnLat = Integer.parseInt(prop.getProperty("column_lat")) - 1;
		}
		if (columnLon == -1 || columnLat == -1) {
			bufferedReader.close();
			return null;
		}

		String csvDelimiter = ",";
		if (prop.getProperty("csv_delimiter") != null) {
			csvDelimiter = prop.getProperty("csv_delimiter");
		}
		String kwdDelimiter = ";";
		if (prop.getProperty("keyword_delimiter") != null) {
			kwdDelimiter = prop.getProperty("keyword_delimiter");
		}

		boolean applyKeywordFilter = false;
		if (prop.getProperty("keywords") != null && prop.getProperty("keywords").length() > 0) {
			applyKeywordFilter = true;
			String k = prop.getProperty("keywords");
			strTok = new StringTokenizer(k, kwdDelimiter);
			while (strTok.hasMoreTokens()) {
				filterKeywords.add(strTok.nextToken().toLowerCase().trim());
			}
		}

		int poiCount = 0;
		GeometryFactory geometryFactory = new GeometryFactory(new PrecisionModel(), 4326);
		while ((line = bufferedReader.readLine()) != null) {
			try {
				strTok = new StringTokenizer(line, csvDelimiter);
				csvColumns = new String[strTok.countTokens()];
				for (int i = 0; i < csvColumns.length; i++) {
					csvColumns[i] = strTok.nextToken();
				}

				if (columnID == -1) {
					id = String.valueOf(poiCount);
				} else {
					id = csvColumns[columnID];
				}
				if (columnName == -1) {
					name = "";
				} else {
					name = csvColumns[columnName];
				}
				if (columnScore == -1) {
					score = 1;
				} else {
					score = Double.parseDouble(csvColumns[columnScore]);
				}
				if (columnKeywords == -1) {
					keywords = null;
				} else {
					kwds = csvColumns[columnKeywords];
					strTok = new StringTokenizer(kwds, kwdDelimiter);
					keywords = new ArrayList<String>();
					while (strTok.hasMoreTokens()) {
						keywords.add(strTok.nextToken().toLowerCase());
					}
				}

				x = Double.parseDouble(csvColumns[columnLon]);
				y = Double.parseDouble(csvColumns[columnLat]);

				if (applyKeywordFilter && Collections.disjoint(filterKeywords, keywords)) {
					continue;
				}

				poi = new POI(id, name, x, y, keywords, score, geometryFactory);

				pois.add(poi);
				poiCount++;
			} catch (Exception e) {
				continue;
			}
		}

		bufferedReader.close();
		return pois;
	}
}