import json
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from dbs.browser.download import StatementDownloader
from dbs.browser.login import DbsAuthHandler


def test_download(mocker: MockerFixture):
    expected_response = {
        "totalRecords": 1,
        "estatementTypes": [{"statementType": "DBSSPA", "statementName": "DBSSPA"}],
        "estatements": [
            {
                "statementDate": "2023-11-30",
                "statementType": "DBSSPA",
                "statementHashKey": "hash-qwerty-12345",
                "description": "DBS Savings Plus Account",
                "entityName": [],
                "address": [],
                "productCode": "1234",
                "productReferenceNo": "1234567890",
                "currency": None,
                "formattedAccountNumber": "123-4-567890",
            }
        ],
    }

    cookies = [
        {"name": "X-dbs-cust-sysgen-id", "value": "12345"},
        {"name": "X-dbs-session-token", "value": "mock_token"},
    ]

    mock_get = mocker.patch(
        "dbs.browser.download.requests.get",
        return_value=MagicMock(text=json.dumps(expected_response)),
    )
    mocker.patch("dbs.browser.download.uuid4", return_value="abcd1234")

    downloader = StatementDownloader(cookies, DbsAuthHandler.user_agent)
    response = downloader.list_statements(
        from_date="2023-06",
        to_date="2023-12",
        statement_type="ALL",
        sort_order="DESC",
        page_size=10,
        page_number=1,
    )

    assert response == expected_response["estatements"]

    expected_params = {
        "statementType": "ALL",
        "from": "062023",
        "to": "122023",
        "sortOrder": "DESC",
        "pageSize": 10,
        "pageNumber": 1,
    }

    expected_headers = {**downloader.common_headers}

    expected_headers["actionid"] = "LIST"
    expected_headers["x-version"] = "2.0.0"
    expected_headers["x-dbs-uuid"] = "abcd1234"
    expected_headers["x-correlationid"] = "abcd1234"

    mock_get.assert_called_once_with(
        downloader.list_endpoint,
        params=expected_params,
        headers=expected_headers,
        timeout=10,
    )
