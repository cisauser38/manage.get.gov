"""Provide a wrapper around epplib to handle authentication and errors."""

import logging

try:
    from epplib.client import Client
    from epplib import commands
    from epplib.exceptions import TransportError, ParsingError
    from epplib.transport import SocketTransport
except ImportError:
    pass

from django.conf import settings

from .cert import Cert, Key
from .errors import ErrorCode, LoginError, RegistryError
from registrar.models.utility.generic_helper import Timer

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

    def _initialize_client(self) -> Client:
        """Initialize a client, assuming _login defined. Sets _client to initialized
        client. Raises errors if initialization fails.
        This method will be called at app initialization, and also during retries."""
        # establish a client object with a TCP socket transport
        # note that type: ignore added in several places because linter complains
        # about _client initially being set to None, and None type doesn't match code
        client = Client(  # type: ignore
            SocketTransport(
                settings.SECRET_REGISTRY_HOSTNAME,
                cert_file=CERT.filename,
                key_file=KEY.filename,
                password=settings.SECRET_REGISTRY_KEY_PASSPHRASE,
            )
        )
        try:
            # use the _client object to connect
            client.connect()  # type: ignore
            response = client.send(self._login)  # type: ignore
            if response.code >= 2000:  # type: ignore
                client.close()  # type: ignore
                raise LoginError(response.msg)  # type: ignore
        except TransportError as err:
            message = "_initialize_client failed to execute due to a connection error."
            logger.error(f"{message} Error: {err}")
            raise RegistryError(message, code=ErrorCode.TRANSPORT_ERROR) from err
        except LoginError as err:
            raise err
        except Exception as err:
            message = "_initialize_client failed to execute due to an unknown error."
            logger.error(f"{message} Error: {err}")
            raise RegistryError(message) from err
        return client

    def _disconnect(self, client) -> None:
        """Close the connection."""
        try:
            client.send(commands.Logout())  # type: ignore
            client.close()  # type: ignore
        except Exception:
            logger.warning("Connection to registry was not cleanly closed.")

    def _send(self, client, command):
        """Helper function used by `send`."""
        cmd_type = command.__class__.__name__

        try:
            response = client.send(command)
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

    def send(self, command, *, cleaned=False):
        """Login, the send the command. Retry once if an error is found"""
        # try to prevent use of this method without appropriate safeguards
        cmd_type = command.__class__.__name__
        logger.info(f"about to execute EPP command {cmd_type}")
        with Timer():
            if not cleaned:
                raise ValueError("Please sanitize user input before sending it.")
            client = None
            try:
                logger.info("about to initialize EPP client")
                with Timer():
                    client = self._initialize_client()
                logger.info("about to send to EPP client")
                with Timer():
                    response = self._send(client,command)
                return response
            except RegistryError as err:
                raise err
            finally:
                if client:
                    logger.info("about to disconnect")
                    with Timer():
                        self._disconnect(client)


try:
    # Initialize epplib
    CLIENT = EPPLibWrapper()
    logger.info("registry client initialized")
except Exception:
    logger.warning("Unable to configure epplib. Registrar cannot contact registry.")
