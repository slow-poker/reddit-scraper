import os
from flask import Flask, request, render_template_string
import lucene

from java.nio.file import Paths
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.analysis.standard import StandardAnalyzer

app = Flask(__name__)

INDEX_DIR = "reddit_ind" 

lucene.initVM(vmargs=["-Djava.awt.headless=true"])

def search_lucene(query_str, limit=10):
    vm_env = lucene.getVMEnv()
    vm_env.attachCurrentThread()
    
    directory = FSDirectory.open(Paths.get(INDEX_DIR))
    reader = DirectoryReader.open(directory)
    searcher = IndexSearcher(reader)
    analyzer = StandardAnalyzer()
    
    parser = QueryParser("all_text", analyzer)
    query = parser.parse(query_str)
    
    hits = searcher.search(query, 50)
    
    results_pool = []
    
    for hit in hits.scoreDocs:
        doc = searcher.storedFields().document(hit.doc)
    
        try:
            timestamp = float(doc.get("live_timestamp")) if doc.get("live_timestamp") else 0.0
        except ValueError:
            timestamp = 0.0
            
        results_pool.append({
            "score": float(hit.score), # Pure BM25 Relevance Score
            "timestamp": timestamp,
            "title": doc.get("title") or "[No Title/Comment]",
            "author": doc.get("author") or "[Unknown]",
            "content": doc.get("content") or "",
            "doc_type": doc.get("doc_type"),
            "subreddit": doc.get("subreddit_name")
        })
        
    reader.close()
    
    if not results_pool:
        return []

    # --- RANKING FUNCTION LOGIC ---
    # Find max/min timestamps to normalize time scores between 0.0 and 1.0
    timestamps = [r["timestamp"] for r in results_pool if r["timestamp"] > 0]
    max_time = max(timestamps) if timestamps else 1
    min_time = min(timestamps) if timestamps else 0
    time_range = max_time - min_time if (max_time - min_time) > 0 else 1

    for res in results_pool:
        # Normalize time score (Newest items get closer to 1.0, oldest get 0.0)
        norm_time_score = (res["timestamp"] - min_time) / time_range if res["timestamp"] > 0 else 0.0
        
        # Weights: 70% textual relevance, 30% recency
        w1, w2 = 0.7, 0.3
        res["combined_score"] = (w1 * res["score"]) + (w2 * norm_time_score)

    # Re-sort entire pool by your newly calculated custom compound score in descending order
    sorted_results = sorted(results_pool, key=lambda x: x["combined_score"], reverse=True)
    
    # Return exactly the top 10 as requested by spec
    return sorted_results[:limit]


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Reddit PyLucene Search Engine</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f9f9f9; color: #333; }
        .search-container { max-width: 600px; margin: 0 auto 30px auto; text-align: center; }
        input[type="text"] { width: 75%; padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 10px 20px; font-size: 16px; background-color: #3F704D; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #3F704D; }
        .results { max-width: 800px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin-bottom: 15px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .title { font-size: 18px; font-weight: bold; color: #0079d3; margin-bottom: 5px; }
        .meta { font-size: 12px; color: #777; margin-bottom: 10px; }
        .score-badge { display: inline-block; background-color: #e2f0fe; color: #0079d3; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .snippet { font-size: 14px; line-height: 1.4; }
    </style>
</head>
<body>

    <div class="search-container">
        <h2>Reddit Search Engine Engine</h2>
        <form method="GET" action="/">
            <input type="text" name="q" value="{{ query }}" placeholder="Search Reddit posts & comments..." required>
            <button type="submit">Search</button>
        </form>
    </div>

    <div class="results">
        {% if query %}
            <h3>Top Results for: "<i>{{ query }}</i>"</h3>
            {% if results %}
                {% for item in results %}
                    <div class="card">
                        <div class="title">[{{ item.doc_type.upper() }}] {{ item.title }}</div>
                        <div class="meta">
                            By u/{{ item.author }} in r/{{ item.subreddit }} 
                            | Raw Time: {{ item.timestamp }} 
                            | <span class="score-badge">Combined Score: {{ "%.4f"|format(item.combined_score) }}</span>
                            | <small>BM25 Text Score: {{ "%.2f"|format(item.score) }}</small>
                        </div>
                        <div class="snippet">{{ item.content[:300] }}{% if item.content|length > 300 %}...{% endif %}</div>
                    </div>
                {% endfor %}
            {% else %}
                <p>No matches found.</p>
            {% endif %}
        {% endif %}
    </div>

</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    query = request.args.get("q", "")
    results = []
    if query:
        results = search_lucene(query)
    return render_template_string(HTML_TEMPLATE, query=query, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)