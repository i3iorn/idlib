import json
from typing import Dict

from httpx import URL


def _dict_to_http_format(
    start: str,
    headers: str,
    body: str
) -> str:
    """
    Convert a dictionary into the full raw HTTP request text, including:
      1. Start-Line
      2. All request headers
      3. A blank line, then the request body (if any)
    """
    start_line = start
    header_lines = "\n".join(f"{k}: {v}" for k, v in json.loads(headers).items())
    parts = [start_line, header_lines, "", body]

    return "\n".join(parts)


def response_dict_to_http_format(
    http_version: str,
    status_code: int,
    reason_phrase: str,
    headers: str,
    body: str,
    **kwargs
) -> str:
    """
    Convert a dictionary into the full raw HTTP response text, including:
      1. Status-Line (version, status code, reason)
      2. All response headers
      3. A blank line, then the response body (if any)

    :param http_version: The HTTP version (e.g. "1.1" or "2").
    :param status_code: The HTTP status code.
    :param reason_phrase: The reason phrase for the status code.
    :param headers: The HTTP headers as a string.
    :param body: The response body as a string.
    :return: A single string containing the raw HTTP response.
    """
    return _dict_to_http_format(
        start=f"{http_version} {status_code} {reason_phrase}",
        headers=headers,
        body=body
    )

def request_dict_to_http_format(
    method: str,
    url: str,
    headers: str,
    body: str,
    http_version: str = "HTTP/1.1",
    **kwargs
) -> str:
    """
    Convert a dictionary into the full raw HTTP request text, including:
      1. Request-Line (method, path+query, version)
      2. All request headers
      3. A blank line, then the request body (if any)
    """
    url = URL(url)
    return _dict_to_http_format(
        start=f"{method} {url.path}{url.query.decode('utf-8')} {http_version}",
        headers=headers,
        body=body
    )
