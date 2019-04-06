import http.client
import json
import ssl
import urllib.error
import urllib.request
from typing import Any, BinaryIO, Dict, Optional, Union


class WWWError(Exception):
    pass


class WWW:
    def __init__(
            self,
            url: str,
            token: Optional[str] = None,
            cafile: Optional[str] = None,
    ) -> None:
        self._url = url
        self._token = token
        self._cafile = cafile

    def get(self, path: str = "/", **kwargs: Any) -> Dict:
        """
        Send a GET request.
        """
        return self._send(path, "GET", **kwargs)

    def delete(self, path: str = "/", **kwargs: Any) -> Dict:
        """
        Send a DELETE request.
        """
        return self._send(path, "DELETE", **kwargs)

    def post(self, path: str = "/", **kwargs: Any) -> Dict:
        """
        Send a POST request.
        """
        return self._send(path, "POST", **kwargs)

    def _send(self, path: str, method: str, **kwargs: Any) -> Dict:
        """
        Send a HTTP(S) request.
        """
        data = None
        headers = {}

        if self._token:
            headers["authorization"] = "bearer {}".format(self._token)

        if kwargs:
            data = json.dumps(kwargs).encode("utf-8")
            headers["content-type"] = "application/json"

        req = urllib.request.Request(
            "{}/{}".format(self._url, path),
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, cafile=self._cafile) as res:
                return self._json_decode(res)
        except urllib.error.HTTPError as e:
            raise WWWError(self._json_decode(e)["message"])
        except (ssl.CertificateError, urllib.error.URLError) as e:
            raise WWWError(e)

    @staticmethod
    def _json_decode(res: Union[http.client.HTTPResponse, BinaryIO]) -> Dict:
        """
        Decode a JSON response.
        """
        data = res.read().decode("utf-8")
        try:
            return json.loads(data)  # type: ignore
        except json.JSONDecodeError:
            # This is ugly, but Flask-HTTPAuth is not RESTful.  Assume
            # that all non-json payloads are error messages to be
            # wrapped in "message".
            return {"message": data}
