"""Tests for Ralph cli usage strings."""

import logging

from click.testing import CliRunner

from ralph.cli import cli

test_logger = logging.getLogger("ralph")


def test_cli_auth_command_usage():
    """Test ralph auth command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["auth", "--help"])

    assert result.exit_code == 0
    assert all(
        text in result.output
        for text in [
            "Options:",
            "-u, --username TEXT",
            "-p, --password TEXT",
            "-s, --scope TEXT",
            "-t, --target TEXT",
            "-M, --agent-ifi-mbox TEXT",
            "-S, --agent-ifi-mbox-sha1sum TEXT",
            "-O, --agent-ifi-openid TEXT",
            "-A, --agent-ifi-account TEXT",
            "-N, --agent-name TEXT",
            "-w, --write-to-disk",
        ]
    )

    result = runner.invoke(cli, ["auth"])
    assert result.exit_code > 0
    assert "Error: Missing option '-u' / '--username'." in result.output


def test_cli_extract_command_usage():
    """Test ralph extract command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["extract", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -p, --parser [gelf|es]  Container format parser used to extract events\n"
        "                          [required]\n"
    ) in result.output

    result = runner.invoke(cli, ["extract"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-p' / '--parser'. Choose from:\n\tgelf,\n\tes\n"
    ) in result.output


def test_cli_validate_command_usage():
    """Test ralph validate command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  -f, --format [edx|xapi]  Input events format to validate  [required]\n"
        "  -I, --ignore-errors      Continue validating regardless of raised errors\n"
        "  -F, --fail-on-unknown    Stop validating at first unknown event\n"
    ) in result.output

    result = runner.invoke(cli, ["validate"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-f' / '--format'. Choose from:\n\tedx,\n\txapi\n"
    ) in result.output


def test_cli_convert_command_usage():
    """Test ralph convert command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--help"])

    assert result.exit_code == 0
    assert (
        "Options:\n"
        "  From edX to xAPI converter options: \n"
        "    -u, --uuid-namespace TEXT     The UUID namespace to use for the `ID` "
        "field\n"
        "                                  generation\n"
        "    -p, --platform-url TEXT       The `actor.account.homePage` to use in"
        " the\n"
        "                                  xAPI statements  [required]\n"
        "  -f, --from [edx]                Input events format to convert  [required]\n"
        "  -t, --to [xapi]                 Output events format  [required]\n"
        "  -I, --ignore-errors             Continue writing regardless of raised "
        "errors\n"
        "  -F, --fail-on-unknown           Stop converting at first unknown event\n"
    ) in result.output

    result = runner.invoke(cli, ["convert"])
    assert result.exit_code > 0
    assert "Error: Missing option '-p' / '--platform-url'" in result.output


def test_cli_read_command_usage():
    """Test ralph read command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["read", "--help"])

    assert result.exit_code == 0

    assert (
        "Usage: ralph read [OPTIONS] [QUERY]\n\n"
        "  Read records matching the QUERY (json or string) from a configured backend."
        "\n\n"
        "Options:\n"
        "  -b, --backend "
        "[async_es|async_mongo|cozystack|es|fs|mongo]\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri URL\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  cozystack backend: \n"
        "    --cozystack-client-options KEY=VALUE,KEY=VALUE\n"
        "    --cozystack-default-doctype TEXT\n"
        "    --cozystack-locale-encoding TEXT\n"
        "    --cozystack-read-chunk-size INTEGER\n"
        "    --cozystack-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri URL\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  -s, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -t, --target TEXT               Endpoint from which to read events (e.g.\n"
        "                                  `/statements`)\n"
        "  -i, --ignore_errors BOOLEAN     Ignore errors during the encoding operation."
        "\n"
        "                                  [default: False]\n"
        "  --help                          Show this message and exit.\n"
    ) == result.output
    logging.warning(result.output)
    result = runner.invoke(cli, ["read"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. "
        "Choose from:\n\tasync_es,\n\tasync_mongo,"
        "\n\tcozystack,\n\tes,\n\tfs,\n\tmongo\n"
    ) in result.output


def test_cli_list_command_usage():
    """Test ralph list command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--help"])

    assert result.exit_code == 0
    assert (
        "Usage: ralph list [OPTIONS]\n\n"
        "  List available documents from a configured data backend.\n\n"
        "Options:\n"
        "  -b, --backend [async_es|async_mongo|cozystack|es|fs|mongo]\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri URL\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  cozystack backend: \n"
        "    --cozystack-client-options KEY=VALUE,KEY=VALUE\n"
        "    --cozystack-default-doctype TEXT\n"
        "    --cozystack-locale-encoding TEXT\n"
        "    --cozystack-read-chunk-size INTEGER\n"
        "    --cozystack-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri URL\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  -t, --target TEXT               Container to list events from\n"
        "  -n, --new / -a, --all           List not fetched (or all) documents\n"
        "  -D, --details / -I, --ids       Get documents detailed output (JSON)\n"
        "  --help                          Show this message and exit.\n"
    ) == result.output

    result = runner.invoke(cli, ["list"])
    assert result.exit_code > 0
    assert (
        "Error: Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\t"
        "async_mongo,\n\tcozystack,\n\tes,\n\tfs,\n\tmongo\n"
    ) in result.output


def test_cli_write_command_usage():
    """Test ralph write command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["write", "--help"])

    assert result.exit_code == 0

    expected_output = (
        "Usage: ralph write [OPTIONS]\n\n"
        "  Write an archive to a configured backend.\n\n"
        "Options:\n"
        "  -b, --backend "
        "[async_es|async_mongo|cozystack|es|fs|mongo]"
        "\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri URL\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  cozystack backend: \n"
        "    --cozystack-client-options KEY=VALUE,KEY=VALUE\n"
        "    --cozystack-default-doctype TEXT\n"
        "    --cozystack-locale-encoding TEXT\n"
        "    --cozystack-read-chunk-size INTEGER\n"
        "    --cozystack-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri URL\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  -t, --target TEXT               The target container to write into\n"
        "  -s, --chunk-size INTEGER        Get events by chunks of size #\n"
        "  -I, --ignore-errors             Continue writing regardless of raised errors"
        "\n"
        "  -o, --operation-type OP_TYPE    Either index, create, delete, update or "
        "append\n"
        "  -c, --concurrency INTEGER       Number of chunks to write concurrently. ("
        "async\n"
        "                                  backends only)\n"
        "  --help                          Show this message and exit.\n"
    )
    assert expected_output == result.output

    result = runner.invoke(cli, ["write"])
    assert result.exit_code > 0
    assert (
        "Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\t"
        "async_mongo,\n\tcozystack,\n\tes,\n\tfs,\n\tmongo\n"
    ) in result.output


def test_cli_runserver_command_usage():
    """Test ralph runserver command usage."""
    runner = CliRunner()
    result = runner.invoke(cli, ["runserver", "--help"])

    expected_output = (
        "Usage: ralph runserver [OPTIONS]\n\n"
        "  Run the API server for the development environment.\n\n"
        "  Starts uvicorn programmatically for convenience and documentation.\n\n"
        "Options:\n"
        "  -b, --backend [async_es|async_mongo|cozystack|es|fs|mongo]\n"
        "                                  Backend  [required]\n"
        "  async_es backend: \n"
        "    --async-es-allow-yellow-status / --no-async-es-allow-yellow-status\n"
        "    --async-es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-es-default-index TEXT\n"
        "    --async-es-hosts TEXT\n"
        "    --async-es-locale-encoding TEXT\n"
        "    --async-es-point-in-time-keep-alive TEXT\n"
        "    --async-es-read-chunk-size INTEGER\n"
        "    --async-es-refresh-after-write TEXT\n"
        "    --async-es-write-chunk-size INTEGER\n"
        "  async_mongo backend: \n"
        "    --async-mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --async-mongo-connection-uri URL\n"
        "    --async-mongo-default-collection TEXT\n"
        "    --async-mongo-default-database TEXT\n"
        "    --async-mongo-locale-encoding TEXT\n"
        "    --async-mongo-read-chunk-size INTEGER\n"
        "    --async-mongo-write-chunk-size INTEGER\n"
        "  cozystack backend: \n"
        "    --cozystack-client-options KEY=VALUE,KEY=VALUE\n"
        "    --cozystack-default-doctype TEXT\n"
        "    --cozystack-locale-encoding TEXT\n"
        "    --cozystack-read-chunk-size INTEGER\n"
        "    --cozystack-write-chunk-size INTEGER\n"
        "  es backend: \n"
        "    --es-allow-yellow-status / --no-es-allow-yellow-status\n"
        "    --es-client-options KEY=VALUE,KEY=VALUE\n"
        "    --es-default-index TEXT\n"
        "    --es-hosts TEXT\n"
        "    --es-locale-encoding TEXT\n"
        "    --es-point-in-time-keep-alive TEXT\n"
        "    --es-read-chunk-size INTEGER\n"
        "    --es-refresh-after-write TEXT\n"
        "    --es-write-chunk-size INTEGER\n"
        "  fs backend: \n"
        "    --fs-default-directory-path PATH\n"
        "    --fs-default-lrs-file TEXT\n"
        "    --fs-default-query-string TEXT\n"
        "    --fs-locale-encoding TEXT\n"
        "    --fs-read-chunk-size INTEGER\n"
        "    --fs-write-chunk-size INTEGER\n"
        "  mongo backend: \n"
        "    --mongo-client-options KEY=VALUE,KEY=VALUE\n"
        "    --mongo-connection-uri URL\n"
        "    --mongo-default-collection TEXT\n"
        "    --mongo-default-database TEXT\n"
        "    --mongo-locale-encoding TEXT\n"
        "    --mongo-read-chunk-size INTEGER\n"
        "    --mongo-write-chunk-size INTEGER\n"
        "  -h, --host TEXT                 LRS server host name\n"
        "  -p, --port INTEGER              LRS server port\n"
        "  --help                          Show this message and exit.\n"
    )
    assert result.exit_code == 0
    assert expected_output == result.output

    result = runner.invoke(cli, ["runserver"])
    assert result.exit_code > 0
    assert (
        "Missing option '-b' / '--backend'. Choose from:\n\tasync_es,\n\tasync_mongo,"
        "\n\tcozystack,\n\tes,\n\tfs,\n\tmongo\n"
    ) in result.output
