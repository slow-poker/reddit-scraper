import sys
import json
import lucene

from java.nio.file import Paths
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.document import Document, TextField, StringField, Field


def safe_str(value):
    """Convert None/null values into empty strings so Lucene does not crash."""
    if value is None:
        return ""
    return str(value)


def add_text(doc, field_name, value):
    """TextField is tokenized/searchable. Use this for title/content."""
    doc.add(TextField(field_name, safe_str(value), Field.Store.YES))


def add_string(doc, field_name, value):
    """StringField is exact-match searchable. Use this for ids, author, subreddit, dates, etc."""
    doc.add(StringField(field_name, safe_str(value), Field.Store.YES))


def build_index(input_file, index_dir):
    # Start the Java VM for PyLucene
    lucene.initVM(vmargs=["-Djava.awt.headless=true"])

    directory = FSDirectory.open(Paths.get(index_dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    writer = IndexWriter(directory, config)

    indexed_count = 0
    skipped_count = 0

    with open(input_file, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as error:
                skipped_count += 1
                print(f"Skipping invalid JSON on line {line_number}: {error}")
                continue

            doc = Document()

            # Decide whether this object is a post or comment
            if data.get("comment-id"):
                doc_type = "comment"
            else:
                doc_type = "post"

            add_string(doc, "doc_type", doc_type)

            # IDs
            add_string(doc, "post_id", data.get("post-id"))
            add_string(doc, "comment_id", data.get("comment-id"))
            add_string(doc, "author_id", data.get("author-id"))

            # Reddit metadata
            add_string(doc, "subreddit_name", data.get("subreddit_name"))
            add_string(doc, "author", data.get("author"))
            add_string(doc, "url", data.get("url"))
            add_string(doc, "attached_url", data.get("attached-url"))

            # Dates/timestamps
            add_string(doc, "date_posted", data.get("date-posted"))
            add_string(doc, "date_commented", data.get("data-commented"))
            add_string(doc, "live_timestamp", data.get("live-timestamp"))

            # Numeric-ish metadata stored as strings because your scraper outputs strings
            add_string(doc, "score", data.get("score"))
            add_string(doc, "comments", data.get("comments"))
            add_string(doc, "replies", data.get("replies"))
            add_string(doc, "golds", data.get("golds"))

            # Boolean-ish metadata stored as strings because your scraper outputs strings
            add_string(doc, "promoted", data.get("promoted"))
            add_string(doc, "nsfw", data.get("nsfw"))

            # Searchable text fields
            add_text(doc, "title", data.get("title"))
            add_text(doc, "content", data.get("content"))

            # Combined field makes B2 searching easier:
            # A query can search both title and content together.
            combined_text = safe_str(data.get("title")) + " " + safe_str(data.get("content"))
            add_text(doc, "all_text", combined_text)

            writer.addDocument(doc)
            indexed_count += 1

            if indexed_count % 1000 == 0:
                print(f"Indexed {indexed_count} documents...")

    writer.commit()
    writer.close()

    print()
    print(f"Finished indexing {indexed_count} documents.")
    print(f"Skipped {skipped_count} invalid JSON lines.")
    print(f"Index stored in: {index_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage:")
        print("python index_reddit.py <input_jsonl_file> <index_output_dir>")
        print()
        print("Example:")
        print('python index_reddit.py "example-scrapes/Scrape-2026-06-02_23-59-02/gaming00000.txt" reddit_index')
        sys.exit(1)

    input_file = sys.argv[1]
    index_dir = sys.argv[2]

    build_index(input_file, index_dir)
