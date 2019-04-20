import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.model_selection import GridSearchCV
import pyLDAvis.sklearn


def topic_modeling(clusters, label_col='cluster_id', kwds_col='kwds', num_of_topics=3, kwds_per_topic=10):
    """Models clusters as documents, extracts topics, and assigns topics to clusters.

    Args:
         clusters (GeoDataFrame): A POI GeoDataFrame with assigned cluster labels.
         label_col (string): The name of the column containing the cluster labels (default: label).
         kwds_col (string): The name of the column containing the keywords of each POI (default: kwds).
         num_of_topics (int): The number of topics to extract (default: 3).
         kwds_per_topic (int): The number of keywords to return per topic (default: 10).

    Returns:
          A DataFrame containing the clusters-to-topics assignments and a DataFrame containing the topics-to-keywords
          assignments.
    """

    # Create a "document" for each cluster
    cluster_kwds = dict()
    for index, row in clusters.iterrows():
        cluster_id, kwds = row[label_col], row[kwds_col]
        if cluster_id not in cluster_kwds:
            cluster_kwds[cluster_id] = ''
        for w in kwds:
            cluster_kwds[cluster_id] += w + ' '

    # Vectorize the corpus
    vectorizer = CountVectorizer()
    corpus_vectorized = vectorizer.fit_transform(cluster_kwds.values())

    # Extract the topics
    search_params = {'n_components': [num_of_topics]}
    lda = LatentDirichletAllocation(n_jobs=-1)
    model = GridSearchCV(lda, param_grid=search_params, n_jobs=-1, cv=3)
    model.fit(corpus_vectorized)
    lda_model = model.best_estimator_

    # Top keywords per topic
    keywords = np.array(vectorizer.get_feature_names())
    topic_keywords = []
    for topic_weights in lda_model.components_:
        top_keyword_locs = (-topic_weights).argsort()[:kwds_per_topic]
        k = keywords.take(top_keyword_locs)
        f = ["{0:.3f}".format(topic_weights[i] / len(clusters.index)) for i in top_keyword_locs]
        kf = [f[i] + '*' + k[i] for i in range(len(k))]
        topic_keywords.append(kf)

    topic_keywords = pd.DataFrame(topic_keywords)
    topic_keywords.columns = ['Kwd ' + str(i) for i in range(topic_keywords.shape[1])]
    topic_keywords.index = ['Topic ' + str(i) for i in range(topic_keywords.shape[0])]

    # Topics per cluster
    lda_output = lda_model.transform(corpus_vectorized)
    topic_names = ["Topic" + str(i) for i in range(lda_model.n_components)]
    cluster_names = cluster_kwds.keys()
    cluster_topics = pd.DataFrame(np.round(lda_output, 2), columns=topic_names, index=cluster_names).sort_index()
    dominant_topic = np.argmax(cluster_topics.values, axis=1)
    cluster_topics['Dominant Topic'] = dominant_topic

    # Prepare a visualization for the topics
    visualized_topics = pyLDAvis.sklearn.prepare(lda_model, corpus_vectorized, vectorizer)

    return cluster_topics, topic_keywords, visualized_topics
