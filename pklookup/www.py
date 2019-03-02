import http.client
import json
import ssl
import urllib.error
import urllib.request
from typing import Any, BinaryIO, Dict, Union


class WWWError(Exception):
    pass


def get(url: str, auth: str=None) -> Dict:
    """
    Send a GET request.
    """
    return _send(url, auth)


def post(url: str, auth: str=None, **kwargs: Any) -> Dict:
    """
    Send a POST request.
    """
    return _send(url, auth, "POST", **kwargs)


def _send(url: str, auth: str=None, method: str="GET", **kwargs: Any) -> Dict:
    """
    Send a HTTP(S) request.
    """
    data = None
    headers = {}

    if auth:
        headers["authorization"] = "bearer {}".format(auth)

    if kwargs:
        data = json.dumps(kwargs).encode("utf-8")
        headers["content-type"] = "application/json"

    req = urllib.request.Request(url,
                                 data=data,
                                 headers=headers,
                                 method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return _json_decode(res)
    except urllib.error.HTTPError as e:
        raise WWWError(_json_decode(e)["message"])
    except (ssl.CertificateError, urllib.error.URLError) as e:
        raise WWWError(e)


def _json_decode(res: Union[http.client.HTTPResponse, BinaryIO]) -> Dict:
    """
    Decode a JSON response.
    """
    data = res.read().decode("utf-8")
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # This is ugly, but Flask-HTTPAuth is not RESTful.  Assume that
        # all non-json payloads are error messages to be wrapped in
        # "message".
        return {"message": data}
