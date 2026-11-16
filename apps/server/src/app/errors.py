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
    "min_properties": "au moins un champ doit être renseigné",
}


class ApiError(Exception):
    """An error returned to the client in the `Error` format of the contract."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error = Error(code=code, message=message, details=details)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    """Any `ApiError` raised by a route: status code + `Error` body."""
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.error.model_dump(exclude_none=True),
        headers=headers,
    )


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


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """400 if the JSON body is malformed, 422 for field-level validation errors."""
    if any(err["type"] == "json_invalid" for err in exc.errors()):
        body = Error(code="bad_request", message="Le corps de la requête n'est pas un JSON valide.")
        return JSONResponse(status_code=400, content=body.model_dump(exclude_none=True))

    body = Error(
        code="validation_error",
        message="Certains champs sont invalides.",
        details=[
            ErrorDetail(field=_field(tuple(err["loc"])), message=_message(err))
            for err in exc.errors()
        ],
    )
    return JSONResponse(status_code=422, content=body.model_dump())
