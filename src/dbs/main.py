import argparse
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from google.cloud import storage  # type: ignore

from dbs.browser.download import StatementDownloader, StatementRecord
from dbs.browser.login import DbsAuthHandler
from dbs.settings import settings

logger = logging.getLogger(__name__)


def main():
    """
    Entrypoint for Cloud Run function that logs into the DBS
    web portal using Selenium, and downloads estatements
    """
    args: Arguments = parse_arguments()
    auth_handler = DbsAuthHandler()
    driver = auth_handler.login()
    cookies = driver.get_cookies()
    downloader = StatementDownloader(cookies, auth_handler.user_agent)

    statement_metadata = downloader.list_statements(**vars(args))

    for metadata in statement_metadata:
        record = StatementRecord(**metadata)
        pdf_statement = downloader.download_statement(record)
        pdf_filename = (
            f"dbs-{record.statement_type.lower()}-{record.statement_date}.pdf"
        )

        with open(pdf_filename, "wb") as pdf_file:
            pdf_file.write(pdf_statement)

        if args.upload:
            upload_to_cloud(source_filename=pdf_filename)


def parse_arguments() -> argparse.Namespace:
    """
    Parse arguments for main entrypoint
    """
    parser = argparse.ArgumentParser(description="Download DBS eStatements.")
    parser.add_argument(
        "--from-date",
        type=str,
        default=(datetime.now() - relativedelta(months=6)).strftime("%Y-%m"),
        help="Start date for statement retrieval (format: YYYY-MM)",
    )
    parser.add_argument(
        "--to-date",
        type=str,
        default=datetime.now().strftime("%Y-%m"),
        help="End date for statement retrieval (format: YYYY-MM)",
    )
    parser.add_argument(
        "--statement-type",
        type=str,
        default="ALL",
        help="Type of statement to retrieve",
    )
    parser.add_argument(
        "--sort-order",
        type=str,
        default="DESC",
        help="Sort order for statements (ASC or DESC)",
    )
    parser.add_argument(
        "--page-size", type=int, default=10, help="Number of statements per page"
    )
    parser.add_argument(
        "--page-number", type=int, default=1, help="Page number for statement retrieval"
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Flag that determines whether to upload to a cloud bucket",
    )
    return parser.parse_args()


# pylint: disable=too-few-public-methods
class Arguments(argparse.Namespace):
    from_date: str
    to_date: str
    statement_type: str
    sort_order: str
    page_size: int
    page_number: int
    upload: bool


def upload_to_cloud(
    source_filename: str,
    bucket_name: str = settings.bucket_name,
    bucket_prefix: str = "dbs",
) -> None:
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob_name = f"{bucket_prefix}/{source_filename}"
    blob = bucket.blob(blob_name)
    logger.info("Attempting to upload to 'gs://%s/%s'", bucket_name, bucket_name)
    blob.upload_from_filename(source_filename)
    logger.info("Uploaded to %s", blob_name)


if __name__ == "__main__":
    main()
