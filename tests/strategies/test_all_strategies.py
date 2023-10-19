"""Generic tests for all strategies."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from requests_mock import Mocker

    from ..conftest import OTEResponse, ResourceType, Testdata, TestResourceIds
    from .conftest import StrategyCls


def test_create(
    strategy_implementation: "tuple[type[StrategyCls], ResourceType, str]",
    mock_ote_response: "OTEResponse",
    ids: "TestResourceIds",
    server_url: str,
) -> None:
    """Test the `create()` method."""
    from utils import strategy_create_kwargs

    strategy_cls, strategy_type, backend = strategy_implementation
    server_url = server_url if backend != "python" else backend

    if backend == "services":
        # Mock URL responses
        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}",
            response_json={strategy_type.get_return_id_key(): ids(strategy_type.value)},
        )

    strategy = strategy_cls(server_url)

    assert not strategy.strategy_id

    strategy.create(**dict(strategy_create_kwargs())[strategy_type.value])

    assert strategy.strategy_id


def test_create_fails(
    strategy_implementation: "tuple[type[StrategyCls], ResourceType, str]",
    mock_ote_response: "OTEResponse",
    server_url: str,
) -> None:
    """Check `create()` raises `ApiError` upon request failure."""
    from utils import strategy_create_kwargs

    from otelib.exceptions import ApiError

    strategy_cls, strategy_type, backend = strategy_implementation

    if backend == "python":
        pytest.skip(
            "Currently no tests for expected create() failures for "
            f"backend={backend!r}."
        )

    if backend == "services":
        # Mock URL responses
        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}",
            status_code=500,
            response_content=b"Internal Server Error",
        )

    strategy = strategy_cls(server_url)

    assert not strategy.strategy_id

    valid_config = dict(strategy_create_kwargs())[strategy_type.value]
    with pytest.raises(ApiError, match=f"^{ApiError.__name__}.*"):
        # `session_id` has a wrong type, the request should fail.
        strategy.create(session_id=123, **valid_config)

    assert not strategy.strategy_id


def test_fetch(
    strategy_implementation: "tuple[type[StrategyCls], ResourceType, str]",
    mock_ote_response: "OTEResponse",
    ids: "TestResourceIds",
    server_url: str,
    testdata: "Testdata",
    requests_mock: "Mocker",
) -> None:
    """Test the `fetch()` method."""
    from utils import strategy_create_kwargs

    strategy_cls, strategy_type, backend = strategy_implementation
    server_url = server_url if backend != "python" else backend

    if strategy_type == strategy_type.FUNCTION and not (
        backend == "services" and "example" in server_url
    ):
        pytest.skip("No function strategy exists in oteapi-core yet.")

    if backend == "services":
        # Mock URL responses
        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}",
            response_json={strategy_type.get_return_id_key(): ids(strategy_type.value)},
        )

        mock_ote_response(
            method="get",
            endpoint=f"/{strategy_type.value}/{ids(strategy_type.value)}",
            response_json=testdata(strategy_type, "get"),
        )

    strategy = strategy_cls(server_url)

    session_id = ""
    if backend == "python":
        # Create session
        session_id = strategy._create_session()

    # We must first create the resource - getting a resource ID
    strategy.create(**dict(strategy_create_kwargs())[strategy_type.value])

    if backend == "python" and strategy_type == strategy_type.DATARESOURCE:
        # Mock URL responses
        requests_mock.request(
            method="get",
            url=dict(strategy_create_kwargs())[strategy_type.value]["downloadUrl"],
            status_code=200,
            json=testdata(strategy_type, "get")["content"],
        )

    content = strategy.fetch(session_id)

    if (
        strategy_type == strategy_type.TRANSFORMATION
        and backend == "services"
        and "example" not in server_url
    ):
        # Real backend for transformation strategy
        # Dynamic response content - just check keys are the same and values are
        # non-empty
        assert list(content) == list(testdata(strategy_type, "get"))
        assert all(content.values())
    else:
        assert content == testdata(strategy_type, "get")


def test_fetch_fails(
    strategy_implementation: "tuple[type[StrategyCls], ResourceType, str]",
    mock_ote_response: "OTEResponse",
    ids: "TestResourceIds",
    server_url: str,
) -> None:
    """Check `fetch()` raises `ApiError` upon request failure."""
    from utils import strategy_create_kwargs

    from otelib.exceptions import ApiError

    strategy_cls, strategy_type, backend = strategy_implementation

    if backend == "python":
        pytest.skip(
            f"Currently no tests for expected fetch() failures for backend={backend!r}."
        )

    if backend == "services":
        # Mock URL responses
        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}",
            response_json={strategy_type.get_return_id_key(): ids(strategy_type.value)},
        )

        mock_ote_response(
            method="get",
            endpoint=f"/{strategy_type.value}/{ids(strategy_type.value)}",
            status_code=500,
            response_content=b"Internal Server Error",
        )

    strategy = strategy_cls(server_url)

    # We must first create the resource - getting a resource ID
    strategy.create(**dict(strategy_create_kwargs())[strategy_type.value])

    with pytest.raises(ApiError, match=f"^{ApiError.__name__}.*"):
        # `session_id` has a wrong type, the request should fail.
        strategy.fetch(session_id=123)


def test_initialize(
    strategy_implementation: "tuple[type[StrategyCls], ResourceType, str]",
    mock_ote_response: "OTEResponse",
    ids: "TestResourceIds",
    server_url: str,
    testdata: "Testdata",
) -> None:
    """Test `DataResource.initialize()`."""
    from utils import strategy_create_kwargs

    strategy_cls, strategy_type, backend = strategy_implementation
    server_url = server_url if backend != "python" else backend

    if strategy_type == strategy_type.FUNCTION and not (
        backend == "services" and "example" in server_url
    ):
        pytest.skip("No function strategy exists in oteapi-core yet.")

    if backend == "services":
        # Mock URL responses
        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}",
            response_json={strategy_type.get_return_id_key(): ids(strategy_type.value)},
        )

        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}/{ids(strategy_type.value)}/initialize",
            response_json=testdata(strategy_type, "initialize"),
        )

    strategy = strategy_cls(server_url)

    session_id = ""
    if backend == "python":
        # Create session
        session_id = strategy._create_session()

    # We must first create the resource - getting a resource ID
    strategy.create(**dict(strategy_create_kwargs())[strategy_type.value])

    content = strategy.initialize(session_id)

    testdata_strategy = testdata(strategy_type, "initialize")
    if strategy_type == strategy_type.MAPPING and (
        backend == "python" or "example" not in strategy.url
    ):
        # "triples" is a Set and must be "sorted"
        content["triples"] = sorted(content["triples"])
        testdata_strategy["triples"] = sorted(testdata_strategy["triples"])
    else:
        assert content == testdata_strategy


def test_initialize_fails(
    strategy_implementation: "tuple[type[StrategyCls], ResourceType, str]",
    mock_ote_response: "OTEResponse",
    ids: "TestResourceIds",
    server_url: str,
) -> None:
    """Check `DataResource.initialize()` raises `ApiError` upon request failure."""
    from utils import strategy_create_kwargs

    from otelib.exceptions import ApiError

    strategy_cls, strategy_type, backend = strategy_implementation

    if backend == "python":
        pytest.skip(
            "Currently no tests for expected initialize() failures for "
            f"backend={backend!r}."
        )

    if backend == "services":
        # Mock URL responses
        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}",
            response_json={strategy_type.get_return_id_key(): ids(strategy_type.value)},
        )

        mock_ote_response(
            method="post",
            endpoint=f"/{strategy_type.value}/{ids(strategy_type.value)}/initialize",
            status_code=500,
            response_content=b"Internal Server Error",
        )

    strategy = strategy_cls(server_url)

    # We must first create the resource - getting a resource ID
    strategy.create(**dict(strategy_create_kwargs())[strategy_type.value])

    with pytest.raises(ApiError, match=f"^{ApiError.__name__}.*"):
        # `session_id` has a wrong type, the request should fail.
        strategy.initialize(session_id=123)
