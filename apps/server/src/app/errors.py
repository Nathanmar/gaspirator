"""Errors returned in the `Error` format of the contract, with French messages."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import Error, ErrorDetail

_MESSAGES: dict[str, str] = {
    "missing": "champ obligatoire",
    "extra_forbidden": "champ non autorisé",
    "string_too_short": "doit contenir au moins {min_length} caractère(s)",
    "string_too_long": "doit contenir au plus {max_length} caractère(s)",
    "string_pattern_mismatch": "format invalide",
    "string_type": "doit être une chaîne de caractères",
    "enum": "doit valoir : {expected}",
    "model_type": "doit être un objet",
    "model_attributes_type": "doit être un objet",
    "dict_type": "doit être un objet",
    "int_type": "doit être un entier",
    "int_parsing": "doit être un entier",
    "greater_than_equal": "doit être supérieur ou égal à {ge}",
    "less_than_equal": "doit être inférieur ou égal à {le}",
    "list_type": "doit être une liste",
    "bool_type": "doit être un booléen",
    "bool_parsing": "doit être un booléen",
    "greater_than": "doit être supérieur à {gt}",
    "decimal_type": "doit être un nombre",
    "decimal_parsing": "doit être un nombre",
    "decimal_max_places": "doit avoir au plus {decimal_places} décimale(s)",
    "decimal_max_digits": "doit avoir au plus {max_digits} chiffre(s)",
    "decimal_whole_digits": "doit avoir au plus {whole_digits} chiffre(s) avant la virgule",
    "date_type": "doit être une date (AAAA-MM-JJ)",
    "date_parsing": "doit être une date (AAAA-MM-JJ)",
    "date_from_datetime_parsing": "doit être une date (AAAA-MM-JJ)",
    "date_from_datetime_inexact": "doit être une date (AAAA-MM-JJ)",
    "datetime_type": "doit être une date et heure ISO 8601",
    "datetime_parsing": "doit être une date et heure ISO 8601",
    "datetime_from_date_parsing": "doit être une date et heure ISO 8601",
    "timezone_aware": "doit préciser le fuseau horaire (ex. 2026-11-03T13:00:00Z)",
}

# Business-rule errors raised with `PydanticCustomError`: their message is already French.
_CUSTOM_ERROR_PREFIXES = ("registration_", "lot_")


def _field(loc: tuple[int | str, ...]) -> str:
    parts = loc[1:] if loc and loc[0] in ("body", "query", "path", "header") else loc
    return ".".join(str(part) for part in parts)


def _message(error: dict) -> str:
    error_type = error["type"]
    if error_type in _MESSAGES:
        return _MESSAGES[error_type].format(**error.get("ctx", {}))
    if error_type == "value_error" and error["loc"] and error["loc"][-1] == "email":
        return "adresse e-mail invalide"
    if error_type.startswith(_CUSTOM_ERROR_PREFIXES):
        return error["msg"]
    return "valeur invalide"


_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}

# Operations whose contract has no 422 response: invalid fields are a 400 (`BadRequest`
# covers "paramètre incorrect").
_BAD_REQUEST_ON_VALIDATION = {"refreshToken", "logout", "listMyLots", "searchSuppliers"}

# Operations whose contract has neither 400 nor 422: an id that cannot exist (not an
# integer, out of range) is simply not found.
_NOT_FOUND_ON_VALIDATION = {
    "getLot": "Lot introuvable.",
    "getSupplier": "Fournisseur introuvable.",
    "listSupplierLots": "Fournisseur introuvable.",
}


class ApiError(Exception):
    """An error answered in the contract `Error` format."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def unauthorized(message: str) -> ApiError:
    return ApiError(401, "unauthorized", message)


def forbidden(message: str) -> ApiError:
    return ApiError(403, "forbidden", message)


def not_found(message: str) -> ApiError:
    return ApiError(404, "not_found", message)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    body = Error(code=exc.code, message=exc.message)
    headers = _UNAUTHORIZED_HEADERS if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code, content=body.model_dump(exclude_none=True), headers=headers
    )


def _error_field(error: dict) -> str:
    """Path of the invalid field; errors on a whole object may name it in `ctx.field`."""
    field = _field(tuple(error["loc"]))
    context_field = error.get("ctx", {}).get("field")
    return ".".join(part for part in (field, context_field) if part) if context_field else field


def _details(exc: RequestValidationError) -> list[ErrorDetail]:
    return [ErrorDetail(field=_error_field(err), message=_message(err)) for err in exc.errors()]


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """400 if the JSON body is malformed, 422 for field-level validation errors."""
    if any(err["type"] == "json_invalid" for err in exc.errors()):
        body = Error(code="bad_request", message="Le corps de la requête n'est pas un JSON valide.")
        return JSONResponse(status_code=400, content=body.model_dump(exclude_none=True))

    operation_id = getattr(request.scope.get("route"), "operation_id", None)
    if operation_id in _NOT_FOUND_ON_VALIDATION:
        body = Error(code="not_found", message=_NOT_FOUND_ON_VALIDATION[operation_id])
        return JSONResponse(status_code=404, content=body.model_dump(exclude_none=True))

    if operation_id in _BAD_REQUEST_ON_VALIDATION:
        body = Error(code="bad_request", message="Paramètres incorrects.", details=_details(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    body = Error(
        code="validation_error", message="Certains champs sont invalides.", details=_details(exc)
    )
    return JSONResponse(status_code=422, content=body.model_dump())
