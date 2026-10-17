"""Spin up a real embedded Postgres for the test session (pgserver)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session", autouse=True)
def _pg():
    import pgserver

    os.environ["LD_LIBRARY_PATH"] = (
        os.path.expanduser(
            "~/workspace/klosado/.venv/lib/python3.12/site-packages/"
            "pgserver/pginstall/lib"
        )
        + ":" + os.environ.get("LD_LIBRARY_PATH", "")
    )
    srv = pgserver.get_server("/tmp/klosado-test-pg")
    uri = srv.get_uri()
    # uri looks like postgresql://postgres:@/postgres?host=/tmp/klosado-test-pg
    os.environ["DATABASE_URL"] = uri.replace("/postgres?", "/klosado_test?", 1)
    import psycopg

    admin = psycopg.connect(uri)
    admin.autocommit = True
    admin.execute("DROP DATABASE IF EXISTS klosado_test")
    admin.execute("CREATE DATABASE klosado_test")
    admin.close()
    yield
    srv.cleanup()
