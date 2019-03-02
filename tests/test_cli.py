import tempfile
from unittest import TestCase
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pklookup import cli, www


class CliTest(TestCase):
    def test_no_url(self) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      admin_token = abcd\n
                      """)
            tmp.flush()

            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "add-token"
            ])
            self.assertNotEqual(result.exit_code, 0)

    @patch("getpass.getpass")  # type: ignore
    def test_no_token(self, mock: MagicMock) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      url = https://url\n
                      """)
            tmp.flush()

            runner = CliRunner()
            runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "add-token"
            ])
            self.assertEqual(mock.call_count, 1)


class AddTokenTest(TestCase):
    def test_no_role(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli.add_token)
        self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.post")  # type: ignore
    def test_invalid_role(self, mock: MagicMock) -> None:
        mock.return_value = {"token": "123"}

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      url = https://url:port\n
                      admin_token = abcd\n
                      """)
            tmp.flush()

            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "add-token",
                "--role=xyz",
                "--description=desc",
            ])
            self.assertNotEqual(result.exit_code, 0)

    @patch("pklookup.www.post")  # type: ignore
    def test_failure_exception(self, mock: MagicMock) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      url = https://url:port\n
                      admin_token = abcd\n
                      """)
            tmp.flush()

            mock.side_effect = www.WWWError
            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "add-token",
                "--role=server",
                "--description=desc",
            ])
            self.assertEqual(result.exit_code, 1)

    @patch("pklookup.www.post")  # type: ignore
    def test_success_admin(self, mock: MagicMock) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      url = https://url:port\n
                      admin_token = abcd\n
                      """)
            tmp.flush()

            mock.return_value = {"token": "xyz"}
            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "add-token",
                "--role=admin",
                "--description=desc",
            ])

            args, kwargs = mock.call_args
            self.assertEqual(args, ("https://url:port/api/v1/token", "abcd"))
            self.assertEqual(kwargs, {"role": "admin", "description": "desc"})
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(result.exit_code, 0)
            self.assertTrue("xyz" in result.output)

    @patch("pklookup.www.post")  # type: ignore
    def test_success_server(self, mock: MagicMock) -> None:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"""
                      [pklookup]\n
                      url = https://url:port\n
                      admin_token = abcd\n
                      """)
            tmp.flush()

            mock.return_value = {"token": "abcd"}
            runner = CliRunner()
            result = runner.invoke(cli.cli, [
                "--config-file",
                tmp.name,
                "add-token",
                "--role=server",
                "--description=desc",
            ])

            args, kwargs = mock.call_args
            self.assertEqual(args, ("https://url:port/api/v1/token", "abcd"))
            self.assertEqual(kwargs, {"role": "server", "description": "desc"})
            self.assertEqual(mock.call_count, 1)
            self.assertEqual(result.exit_code, 0)
            self.assertTrue("abcd" in result.output)
