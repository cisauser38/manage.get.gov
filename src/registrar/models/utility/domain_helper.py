from enum import Enum
import re

from django import forms
from django.http import JsonResponse

from api.views import DOMAIN_API_MESSAGES, check_domain_available
from registrar.utility import errors
from epplibwrapper.errors import RegistryError
from registrar.utility.enums import ValidationErrorReturnType


class DomainHelper:
    """Utility functions and constants for domain names."""

    # a domain name is alphanumeric or hyphen, up to 63 characters, doesn't
    # begin or end with a hyphen, followed by a TLD of 2-6 alphabetic characters
    DOMAIN_REGEX = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.[A-Za-z]{2,6}$")

    # a domain can be no longer than 253 characters in total
    MAX_LENGTH = 253

    @classmethod
    def string_could_be_domain(cls, domain: str | None) -> bool:
        """Return True if the string could be a domain name, otherwise False."""
        if not isinstance(domain, str):
            return False
        return bool(cls.DOMAIN_REGEX.match(domain))

    @classmethod
    def validate(cls, domain: str | None, blank_ok=False) -> str:
        """Attempt to determine if a domain name could be requested."""
        if domain is None:
            raise errors.BlankValueError()
        if not isinstance(domain, str):
            raise errors.InvalidDomainError("Domain name must be a string")

        domain = domain.lower().strip()

        if domain == "" and not blank_ok:
            raise errors.BlankValueError()

        if domain.endswith(".gov"):
            domain = domain[:-4]

        if "." in domain:
            raise errors.ExtraDotsError()

        if not DomainHelper.string_could_be_domain(domain + ".gov"):
            raise errors.InvalidDomainError()

        try:
            if not check_domain_available(domain):
                raise errors.DomainUnavailableError()
        except RegistryError as err:
            raise errors.RegistrySystemError() from err
        return domain

    @classmethod
    def validate_and_handle_errors(cls, domain, error_return_type, prevent_blank=True, display_success=False):
        """
        Validates the provided domain and handles any validation errors.

        This method attempts to validate the domain using the `validate` method. If validation fails,
        it catches the exception and returns an appropriate error response. The type of the error response
        (JSON response or form validation error) is determined by the `error_return_type` parameter.

        If validation is successful and `display_success` is True, it returns a success response.
        Otherwise, it returns the validated domain.

        Args:
            domain (str): The domain to validate.
            error_return_type (ValidationErrorReturnType): The type of error response to return if validation fails.
            prevent_blank (bool, optional): Whether to return an exception if the input is blank. Defaults to True.
            display_success (bool, optional): Whether to return a success response if validation is successful. Defaults to False.

        Returns:
            The error response if validation fails,
            the success response if validation is successful and `display_success` is True,
            or the validated domain otherwise.
        """  # noqa

        try:
            validated = cls.validate(domain)
        except errors.BlankValueError:
            if not prevent_blank:
                return DomainHelper._return_form_error_or_json_response(error_return_type, code="required")
            else:
                return validated
        except errors.ExtraDotsError:
            return DomainHelper._return_form_error_or_json_response(error_return_type, code="extra_dots")
        except errors.DomainUnavailableError:
            return DomainHelper._return_form_error_or_json_response(error_return_type, code="unavailable")
        except errors.RegistrySystemError:
            return DomainHelper._return_form_error_or_json_response(error_return_type, code="error")
        except errors.InvalidDomainError:
            return DomainHelper._return_form_error_or_json_response(error_return_type, code="invalid")
        else:
            if display_success:
                return DomainHelper._return_form_error_or_json_response(
                    error_return_type, code="success", available=True
                )
            else:
                return validated

    @staticmethod
    def _return_form_error_or_json_response(return_type: ValidationErrorReturnType, code, available=False):
        """
        Returns an error response based on the `return_type`.

        If `return_type` is `FORM_VALIDATION_ERROR`, raises a form validation error.
        If `return_type` is `JSON_RESPONSE`, returns a JSON response with 'available', 'code', and 'message' fields.
        If `return_type` is neither, raises a ValueError.

        Args:
            return_type (ValidationErrorReturnType): The type of error response.
            code (str): The error code for the error message.
            available (bool, optional): Availability, only used for JSON responses. Defaults to False.

        Returns:
            A JSON response or a form validation error.

        Raises:
            ValueError: If `return_type` is neither `FORM_VALIDATION_ERROR` nor `JSON_RESPONSE`.
        """  # noqa
        match return_type:
            case ValidationErrorReturnType.FORM_VALIDATION_ERROR:
                raise forms.ValidationError(DOMAIN_API_MESSAGES[code], code=code)
            case ValidationErrorReturnType.JSON_RESPONSE:
                return JsonResponse({"available": available, "code": code, "message": DOMAIN_API_MESSAGES[code]})
            case _:
                raise ValueError("Invalid return type specified")

    @classmethod
    def sld(cls, domain: str):
        """
        Get the second level domain. Example: `gsa.gov` -> `gsa`.

        If no TLD is present, returns the original string.
        """
        return domain.split(".")[0]

    @classmethod
    def tld(cls, domain: str):
        """Get the top level domain. Example: `gsa.gov` -> `gov`."""
        parts = domain.rsplit(".")
        return parts[-1] if len(parts) > 1 else ""
