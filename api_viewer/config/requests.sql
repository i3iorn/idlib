-- Create the requests table
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_request_id INTEGER,
    method TEXT NOT NULL,
    http_version TEXT NOT NULL,
    url TEXT NOT NULL,
    headers TEXT,
    body TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token_request_id) REFERENCES requests(id) ON DELETE CASCADE
);

-- Create the responses table
CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    response_time INTEGER NOT NULL,
    status_code INTEGER,
    reason_phrase TEXT,
    http_version TEXT NOT NULL,
    headers TEXT,
    body TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);

-- Create a table to store individual values by jsonpath --
CREATE TABLE IF NOT EXISTS jsonpath_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    jsonpath TEXT NOT NULL,
    value TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE
);

-- Create a view to link them
CREATE VIEW IF NOT EXISTS request_response AS
SELECT
    r.id AS request_id,
    r.token_request_id,
    r.method,
    r.http_version as request_http_version,
    r.url,
    r.headers AS request_headers,
    r.body AS request_body,
    r.timestamp AS request_timestamp,
    s.id AS response_id,
    s.status_code,
    s.reason_phrase,
    s.http_version as response_http_version,
    s.response_time,
    s.headers AS response_headers,
    s.body AS response_body,
    s.timestamp AS response_timestamp
FROM requests r
LEFT JOIN responses s ON r.id = s.request_id;

-- Create a trigger to automatically delete jsonpath values when a request is deleted
CREATE TRIGGER IF NOT EXISTS delete_jsonpath_values_after_request
AFTER DELETE ON requests
BEGIN
    DELETE FROM jsonpath_values WHERE request_id = OLD.id;
END;

-- Create a trigger to automatically delete responses when a request is deleted
CREATE TRIGGER IF NOT EXISTS delete_response_after_request
AFTER DELETE ON requests
BEGIN
    DELETE FROM responses WHERE request_id = OLD.id;
END;

-- Create a trigger to automatically delete requests when a response is deleted
CREATE TRIGGER IF NOT EXISTS delete_request_after_response
AFTER DELETE ON responses
BEGIN
    DELETE FROM requests WHERE id = OLD.request_id;
END;

-- Create a trigger to automatically delete requests when a token request is deleted
CREATE TRIGGER IF NOT EXISTS delete_request_after_token_request
AFTER DELETE ON requests
BEGIN
    DELETE FROM requests WHERE token_request_id = OLD.id;
END;

-- Create a trigger to automatically delete token_requests when a request is deleted
CREATE TRIGGER IF NOT EXISTS delete_token_request_after_request
AFTER DELETE ON requests
BEGIN
    DELETE FROM requests WHERE token_request_id = OLD.id;
END;
