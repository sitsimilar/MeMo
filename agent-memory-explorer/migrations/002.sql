CREATE TABLE IF NOT EXISTS content_history(node_id TEXT NOT NULL REFERENCES nodes(id), version INTEGER NOT NULL, content TEXT NOT NULL, epistemic TEXT NOT NULL, review TEXT NOT NULL, PRIMARY KEY(node_id,version));
INSERT OR IGNORE INTO content_history SELECT id,content_version,content,epistemic,review FROM nodes;
CREATE TABLE IF NOT EXISTS source_requests(key TEXT PRIMARY KEY,payload TEXT NOT NULL,result TEXT NOT NULL);
INSERT OR IGNORE INTO schema_version VALUES(2);
