import logging

from dbslogin.browser.download import StatementDownloader, StatementRecord
from dbslogin.browser.login import DbsAuthHandler

logger = logging.getLogger(__name__)


def main():
    """
    Entrypoint for Cloud Run function that logs into the DBS
    web portal using Selenium, and downloads estatements
    """
    auth_handler = DbsAuthHandler()
    driver = auth_handler.login()
    cookies = driver.get_cookies()
    downloader = StatementDownloader(cookies, auth_handler.user_agent)

    statement_metadata = downloader.list_statements()

    for metadata in statement_metadata:
        record = StatementRecord(**metadata)
        pdf_statement = downloader.download_statement(record)
        pdf_filename = (
            f"dbs-{record.statement_type.lower()}-{record.statement_date}.pdf"
        )

        with open(pdf_filename, "wb") as pdf_file:
            pdf_file.write(pdf_statement)


if __name__ == "__main__":
    main()
