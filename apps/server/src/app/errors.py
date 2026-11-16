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
}


def _field(loc: tuple[int | str, ...]) -> str:
    parts = loc[1:] if loc and loc[0] in ("body", "query", "path", "header") else loc
    return ".".join(str(part) for part in parts)


def _message(error: dict) -> str:
    error_type = error["type"]
    if error_type in _MESSAGES:
        return _MESSAGES[error_type].format(**error.get("ctx", {}))
    if error_type == "value_error" and error["loc"] and error["loc"][-1] == "email":
        return "adresse e-mail invalide"
    if error_type.startswith(("supplier_type_",)):
        return error["msg"]
    return "valeur invalide"


_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}

# Operations whose contract has no 422 response: invalid fields are a 400 (`BadRequest`
# covers "paramètre incorrect").
_BAD_REQUEST_ON_VALIDATION = {"refreshToken", "logout"}


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


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    body = Error(code=exc.code, message=exc.message)
    headers = _UNAUTHORIZED_HEADERS if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code, content=body.model_dump(exclude_none=True), headers=headers
    )


def _details(exc: RequestValidationError) -> list[ErrorDetail]:
    return [
        ErrorDetail(field=_field(tuple(err["loc"])), message=_message(err)) for err in exc.errors()
    ]


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """400 if the JSON body is malformed, 422 for field-level validation errors."""
    if any(err["type"] == "json_invalid" for err in exc.errors()):
        body = Error(code="bad_request", message="Le corps de la requête n'est pas un JSON valide.")
        return JSONResponse(status_code=400, content=body.model_dump(exclude_none=True))

    route = request.scope.get("route")
    if getattr(route, "operation_id", None) in _BAD_REQUEST_ON_VALIDATION:
        body = Error(code="bad_request", message="Paramètres incorrects.", details=_details(exc))
        return JSONResponse(status_code=400, content=body.model_dump())

    body = Error(
        code="validation_error", message="Certains champs sont invalides.", details=_details(exc)
    )
    return JSONResponse(status_code=422, content=body.model_dump())
