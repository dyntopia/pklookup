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
            www.WWW("https://expired.badssl.com/")._send("", "GET")

    def test_wrong_host(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://wrong.host.badssl.com/")._send("", "GET")

    def test_self_signed(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://self-signed.badssl.com/")._send("", "GET")

    def test_untrusted_root(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://untrusted-root.badssl.com/")._send("", "GET")

    def test_rc4_md5(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://rc4-md5.badssl.com/")._send("", "GET")

    def test_rc4(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://rc4.badssl.com/")._send("", "GET")

    def test_3des(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://3des.badssl.com/")._send("", "GET")

    def test_null(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://null.badssl.com/")._send("", "GET")

    def test_dh480(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://dh480.badssl.com/")._send("", "GET")

    def test_dh512(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://dh512.badssl.com/")._send("", "GET")

    def test_invalid_expected_sct(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://invalid-expected-sct.badssl.com/") \
               ._send("", "GET")

    def test_subdomain_preloaded_hsts(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://subdomain.preloaded-hsts.badssl.com/") \
               ._send("", "GET")

    def test_superfish(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://superfish.badssl.com/")._send("", "GET")

    def test_e_dell_root(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://edellroot.badssl.com/")._send("", "GET")

    def test_dsd_test_provider(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://dsdtestprovider.badssl.com/")._send("", "GET")

    def test_preact_cli(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://preact-cli.badssl.com/")._send("", "GET")

    def test_webpack_dev_server(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://webpack-dev-server.badssl.com/")._send("", "GET")

    def test_mitm_software(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://mitm-software.badssl.com/")._send("", "GET")

    def test_sha1_2016(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://sha1-2016.badssl.com/")._send("", "GET")

    def test_sha1_2017(self) -> None:
        with self.assertRaises(www.WWWError):
            www.WWW("https://sha1-2017.badssl.com/")._send("", "GET")
# pylint: enable=protected-access,too-many-public-methods


@patch("urllib.request.urlopen")
class GetTest(TestCase):
    def test_method(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com").get()

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.method, "GET")

    def test_auth_header(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com", token="abcd").get()

        args, _kwargs = mock.call_args
        req = args[0]

        self.assertEqual(req.headers, {"Authorization": "bearer abcd"})

    def test_data(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com", token="abc").get(a="b", x="y")

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
            www.WWW("https://example.com").get()

    def test_http_error_no_messsage(self, mock: MagicMock) -> None:
        fp = io.BytesIO(b"abcd")
        exc = HTTPError("url", 403, "forbidden", {}, fp)  # type: ignore
        mock.return_value = URLOpenMock(b"msg", exc)

        with self.assertRaises(www.WWWError):
            www.WWW("https://example.com").get()


@patch("urllib.request.urlopen")
class PostTest(TestCase):
    def test_method(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com").post()

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.method, "POST")

    def test_auth_header(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com", token="xyz").post()

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.headers, {"Authorization": "bearer xyz"})

    def test_data(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com", token="abc").post(a="b", x="y")

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


@patch("urllib.request.urlopen")
class DeleteTest(TestCase):
    def test_method(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com").delete()

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.method, "DELETE")

    def test_auth_header(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com", token="xyz").delete()

        args, _kwargs = mock.call_args
        req = args[0]
        self.assertEqual(req.headers, {"Authorization": "bearer xyz"})

    def test_data(self, mock: MagicMock) -> None:
        mock.return_value = URLOpenMock()

        www.WWW("https://example.com", token="abc").delete(a="b", x="y")

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
