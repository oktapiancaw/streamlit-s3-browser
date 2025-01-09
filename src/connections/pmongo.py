from contextlib import contextmanager

from loguru import logger
from pymongo import MongoClient
from pymongo.errors import ExecutionTimeout, NetworkTimeout

from configs import config
from typica import DBConnectionMeta


class MongoConnector:
    def __init__(self, meta: DBConnectionMeta) -> None:
        """
        Initialize a new instance of MongoConnector.

        Args:
            meta (DBConnectionMeta): A DBConnectionMeta instance containing the database connection details.

        The `uri` attribute of the `meta` object will be set to the connection URI
        string using the `uri_string` method of the `DBConnectionMeta` instance.
        The `client` attribute is set to None.
        """

        self._meta: DBConnectionMeta = meta
        if not self._meta.uri:
            self._meta.uri = self._meta.uri_string(base="mongodb", with_db=False)

        self.client: MongoClient | None = None

    @contextmanager
    def stream_connect(self, **kwargs):
        """
        Context manager to connect to the mongo database as a stream.

        Connect to the mongo database, yield the connection, and then close the connection.
        Any keyword arguments will be passed to the MongoClient constructor.

        See the MongoClient documentation for available keyword arguments.
        """

        self.connect(**kwargs)
        yield self
        self.close()

    def connect(self, **kwargs):
        """
        Connect to the mongo database.

        Connect to the mongo database and set the default database using the
        database name specified in the meta object.

        Any keyword arguments will be passed to the MongoClient constructor.

        See the MongoClient documentation for available keyword arguments.
        """

        try:
            if not self._meta.uri:
                raise ValueError("Mongo URI is not set")
            if not self._meta.database:
                raise ValueError("Mongo database is not set")
            self.client = MongoClient(self._meta.uri, **kwargs)
            self.db = self.client[str(self._meta.database)]
            logger.success("Mongo is connected")
        except (NetworkTimeout, ExecutionTimeout):
            logger.exception("Connecting timeout")
            raise
        except Exception:
            logger.exception("Something went wrong while connecting to mongo")
            raise

    def close(self):
        """
        Close the mongo database connection.

        Close the mongo database connection and log a message indicating
        that the connection has been closed.
        """

        if self.client:
            self.client.close()
        logger.success("Mongo is closed")
