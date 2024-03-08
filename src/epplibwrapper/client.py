"""Provide a wrapper around epplib to handle authentication and errors."""

import logging

try:
    from epplib.client import Client
    from epplib import commands
    from epplib.exceptions import TransportError, ParsingError

except ImportError:
    pass


from .cert import Cert, Key
from .errors import ErrorCode, LoginError, RegistryError

logger = logging.getLogger(__name__)

try:
    # Write cert and key to disk
    CERT = Cert()
    KEY = Key()
except Exception:
    CERT = None  # type: ignore
    KEY = None  # type: ignore
    logger.warning(
        "Problem with client certificate. Registrar cannot contact registry.",
        exc_info=True,
    )

from django.conf import settings

class EPPLibWrapper:
    """
    A wrapper over epplib's client.

    ATTN: This should not be used directly. Use `Domain` from domain.py.
    """

    def __init__(self) -> None:
        """Initialize settings which will be used for all connections."""
        # set _client to None initially. In the event that the __init__ fails
        # before _client initializes, app should still start and be in a state
        # that it can attempt _client initialization on send attempts
        self._client = None  # type: ignore
        # prepare (but do not send) a Login command
        self._login = commands.Login(
            cl_id=settings.SECRET_REGISTRY_CL_ID,
            password=settings.SECRET_REGISTRY_PASSWORD,
            obj_uris=[
                "urn:ietf:params:xml:ns:domain-1.0",
                "urn:ietf:params:xml:ns:contact-1.0",
            ],
        )
        try:
            self._initialize_client()
        except Exception:
            logger.warning("Unable to configure epplib. Registrar cannot contact registry.")

        self.pool_options = {
            # Pool size
            "size": settings.EPP_CONNECTION_POOL_SIZE,
            # Which errors the pool should look out for.
            # Avoid changing this unless necessary,
            # it can and will break things.
            "exc_classes": (TransportError,),
            # Occasionally pings the registry to keep the connection alive.
            # Value in seconds => (keepalive / size)
            "keepalive": settings.POOL_KEEP_ALIVE,
        }

        self._pool = None

        # Tracks the status of the pool
        self.pool_status = PoolStatus()

        if start_connection_pool:
            self.start_connection_pool()

    def _send(self, command):
        """Helper function used by `send`."""
        cmd_type = command.__class__.__name__

        try:
            # check for the condition that the _client was not initialized properly
            # at app initialization
            if self._client is None:
                self._initialize_client()
            response = self._client.send(command)
        except (ValueError, ParsingError) as err:
            message = f"{cmd_type} failed to execute due to some syntax error."
            logger.error(f"{message} Error: {err}")
            raise RegistryError(message) from err
        except TransportError as err:
            message = f"{cmd_type} failed to execute due to a connection error."
            logger.error(f"{message} Error: {err}")
            raise RegistryError(message, code=ErrorCode.TRANSPORT_ERROR) from err
        except LoginError as err:
            # For linter due to it not liking this line length
            text = "failed to execute due to a registry login error."
            message = f"{cmd_type} {text}"
            logger.error(f"{message} Error: {err}")
            raise RegistryError(message) from err
        except Exception as err:
            message = f"{cmd_type} failed to execute due to an unknown error."
            logger.error(f"{message} Error: {err}")
            raise RegistryError(message) from err
        else:
            if response.code >= 2000:
                raise RegistryError(response.msg, code=response.code)
            else:
                return response

    def _retry(self, command):
        """Retry sending a command through EPP by re-initializing the client
        and then sending the command."""
        # re-initialize by disconnecting and initial
        self._disconnect()
        self._initialize_client()
        return self._send(command)

    def send(self, command, *, cleaned=False):
        """Login, the send the command. Retry once if an error is found"""
        # try to prevent use of this method without appropriate safeguards
        cmd_type = command.__class__.__name__
        if not cleaned:
            raise ValueError("Please sanitize user input before sending it.")
        try:
            return self._send(command)
        except RegistryError as err:
            if (
                err.is_transport_error()
                or err.is_connection_error()
                or err.is_session_error()
                or err.is_server_error()
                or err.should_retry()
            ):
                message = f"{cmd_type} failed and will be retried"
                logger.info(f"{message} Error: {err}")
                return self._retry(command)
            else:
                raise err
            finally:
                # Code execution will halt after here.
                # The end user will need to recall .send.
                self.start_connection_pool()

        counter = 0  # we'll try 3 times
        while True:
            try:
                return self._send(command)
            except RegistryError as err:
                if counter < 3 and (err.should_retry() or err.is_transport_error()):
                    logger.info(f"Retrying transport error. Attempt #{counter+1} of 3.")
                    counter += 1
                    sleep((counter * 50) / 1000)  # sleep 50 ms to 150 ms
                else:  # don't try again
                    raise err

    def get_pool(self):
        """Get the current pool instance"""
        return self._pool

    def _create_pool(self, client, login, options):
        """Creates and returns new pool instance"""
        logger.info("New pool was created")
        return EPPConnectionPool(client, login, options)

    def start_connection_pool(self, restart_pool_if_exists=True):
        """Starts a connection pool for the registry.

        restart_pool_if_exists -> bool:
        If an instance of the pool already exists,
        then then that instance will be killed first.
        It is generally recommended to keep this enabled.
        """
        # Since we reuse the same creds for each pool, we can test on
        # one socket, and if successful, then we know we can connect.
        if not self._test_registry_connection_success():
            logger.warning("start_connection_pool() -> Cannot contact the Registry")
            self.pool_status.connection_success = False
        else:
            self.pool_status.connection_success = True

            # If this function is reinvoked, then ensure
            # that we don't have duplicate data sitting around.
            if self._pool is not None and restart_pool_if_exists:
                logger.info("Connection pool restarting...")
                self.kill_pool()
                logger.info("Old pool killed")

            self._pool = self._create_pool(CERT, KEY, self._login, self.pool_options)

            self.pool_status.pool_running = True
            self.pool_status.pool_hanging = False

            logger.info("Connection pool started")

    def kill_pool(self):
        """Kills the existing pool. Use this instead
        of self._pool = None, as that doesn't clear
        gevent instances."""
        if self._pool is not None:
            self._pool.kill_all_connections()
            self._pool = None
            self.pool_status.pool_running = False
            return None
        logger.info("kill_pool() was invoked but there was no pool to delete")

    def _test_registry_connection_success(self):
        """Check that determines if our login
        credentials are valid, and/or if the Registrar
        can be contacted
        """
        # This is closed in test_connection_success
        socket = Socket(CERT, KEY, self._login)
        can_login = False

        # Something went wrong if this doesn't exist
        if hasattr(socket, "test_connection_success"):
            can_login = socket.test_connection_success()

        return can_login


try:
    # Initialize epplib
    CLIENT = EPPLibWrapper()
    logger.info("registry client initialized")
except Exception:
    logger.warning("Unable to configure epplib. Registrar cannot contact registry.")
