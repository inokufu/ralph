"""Module py.test fixtures."""

import debugpy

from .fixtures.api import client  # noqa: F401
from .fixtures.auth import (  # noqa: F401
    basic_auth_credentials,
    cozy_auth_data,
    cozy_auth_target,
    cozy_auth_token,
    encoded_token,
    mock_discovery_response,
    mock_oidc_jwks,
)
from .fixtures.backends import (  # noqa: F401
    anyio_backend,
    async_es_backend,
    async_es_lrs_backend,
    async_mongo_backend,
    async_mongo_lrs_backend,
    cozystack_custom,
    es,
    es_backend,
    es_custom,
    es_data_stream,
    es_forwarding,
    es_lrs_backend,
    events,
    flavor,
    fs_backend,
    fs_lrs_backend,
    lrs,
    mongo,
    mongo_backend,
    mongo_custom,
    mongo_forwarding,
    mongo_lrs_backend,
    settings_fs,
)
from .fixtures.logs import gelf_logger  # noqa: F401
from .fixtures.statements import (  # noqa: F401
    init_cozystack_db_and_monkeypatch_backend,
    insert_statements_and_monkeypatch_backend,
)

debugpy.listen(5678, in_process_debug_adapter=True)
