import io
import json
import os
from typing import Any
from unittest import TestCase, TestResult
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from pklookup import www

from .helpers import URLOpenMock


# pylint: disable=protected-access,too-many-public-methods
class SendOnlineTest(TestCase):
    """
    Tests that only run when `PKLOOKUP_ONLINE` is 1.

    Note that neither the builtin urllib nor requests throws on:

    - https://pinning-test.badssl.com
    - https://revoked.badssl.com
    - https://dh1024.badssl.com
    - https://dh-composite.badssl.com
    - https://dh-small-subgroup.badssl.com
    - https://dh-composite.badssl.com
    - https://sha1-intermediate.badssl.com
    """

    def run(self, result: TestResult=None) -> Any:
        try:
            online = int(os.getenv("PKLOOKUP_ONLINE"))
        except (TypeError, ValueError):
            return None

        if online == 1:
            return super().run(result)
        return None

    def test_expired(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://expired.badssl.com/")

    def test_wrong_host(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://wrong.host.badssl.com/")

    def test_self_signed(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://self-signed.badssl.com/")

    def test_untrusted_root(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://untrusted-root.badssl.com/")

    def test_rc4_md5(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://rc4-md5.badssl.com/")

    def test_rc4(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://rc4.badssl.com/")

    def test_3des(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://3des.badssl.com/")

    def test_null(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://null.badssl.com/")

    def test_dh480(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://dh480.badssl.com/")

    def test_dh512(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://dh512.badssl.com/")

    def test_invalid_expected_sct(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://invalid-expected-sct.badssl.com/")

    def test_subdomain_preloaded_hsts(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://subdomain.preloaded-hsts.badssl.com/")

    def test_superfish(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://superfish.badssl.com/")

    def test_e_dell_root(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://edellroot.badssl.com/")

    def test_dsd_test_provider(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://dsdtestprovider.badssl.com/")

    def test_preact_cli(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://preact-cli.badssl.com/")

    def test_webpack_dev_server(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://webpack-dev-server.badssl.com/")

    def test_mitm_software(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://mitm-software.badssl.com/")

    def test_sha1_2016(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://sha1-2016.badssl.com/")

    def test_sha1_2017(self) -> None:
        with self.assertRaises(www.WWWError):
            www._send("https://sha1-2017.badssl.com/")
# pylint: enable=protected-access,too-many-public-methods


@patch("urllib.request.urlopen")
class GetTest(TestCase):
    def test_method(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.get("https://example.com")

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.method, "GET")

    def test_auth_header(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.get("https://example.com", auth="abcd")

        args, _kwargs = mock.call_args
        req = args[0]

        self.assertEqual(req.headers, {"Authorization": "bearer abcd"})

    def test_data(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.get("https://example.com", auth="abc", a="b", x="y")

        args, _kwargs = mock.call_args
        req = args[0]

        headers = {
            "Authorization": "bearer abc",
            "Content-type": "application/json"
        }
        self.assertEqual(req.headers, headers)

        data = {
            "a": "b",
            "x": "y"
        }
        self.assertEqual(json.loads(req.data.decode("utf-8")), data)

    def test_http_error_messsage(self, mock: MagicMock) -> None:
        fp = io.BytesIO(json.dumps({"message": "xyz"}).encode("utf-8"))
        exc = HTTPError("url", 403, "forbidden", {}, fp)  # type: ignore
        mock.return_value = URLOpenMock(b"msg", exc)

        with self.assertRaises(www.WWWError):
            www.get("https://example.com")

    def test_http_error_no_messsage(self, mock: MagicMock) -> None:
        fp = io.BytesIO(b"abcd")
        exc = HTTPError("url", 403, "forbidden", {}, fp)  # type: ignore
        mock.return_value = URLOpenMock(b"msg", exc)

        with self.assertRaises(www.WWWError):
            www.get("https://example.com")


@patch("urllib.request.urlopen")
class PostTest(TestCase):
    def test_method(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.post("https://example.com")

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.method, "POST")

    def test_auth_header(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.post("https://example.com", auth="xyz")

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.headers, {"Authorization": "bearer xyz"})

    def test_data(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.post("https://example.com", auth="abc", a="b", x="y")

        args, _kwargs = mock.call_args
        req = args[0]

        headers = {
            "Authorization": "bearer abc",
            "Content-type": "application/json"
        }
        self.assertEqual(req.headers, headers)

        data = {
            "a": "b",
            "x": "y"
        }
        self.assertEqual(json.loads(req.data.decode("utf-8")), data)
