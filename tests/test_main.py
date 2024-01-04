from pytest_mock import MockerFixture

from dbs.main import Arguments, parse_arguments


def test_parse_arguments(mocker: MockerFixture):
    mocker.patch(
        "argparse._sys.argv",
        ["script.py", "--from-date", "2022-01", "--to-date", "2022-12", "--upload"],
    )
    args: Arguments = parse_arguments()
    assert args.from_date == "2022-01"
    assert args.to_date == "2022-12"
    assert args.statement_type == "ALL"
    assert args.sort_order == "DESC"
    assert args.page_size == 10
    assert args.page_number == 1
    assert args.upload
