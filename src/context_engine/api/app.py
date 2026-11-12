"""FastAPI adapter over the core application facade.

Routes validate transport input and call ``ContextEngineApplication``; they contain no
business logic. The API is unauthenticated and intended for local use only.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, FastAPI, File, Header, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import JsonValue
from starlette.exceptions import HTTPException

from context_engine.api.schemas import (
    ApprovalDecisionRequest,
    ClearUploadsResponse,
    DeleteSourceResponse,
    ErrorBody,
    ErrorResponse,
    IngestionOutcomeModel,
    IngestionReportResponse,
    RecoverSourcesResponse,
    RunDetailModel,
    RunEventModel,
    RunListResponse,
    RunSummaryModel,
    SourceListResponse,
    StartRunRequest,
    SystemResponse,
)
from context_engine.core import (
    ContextEngineApplication,
    InvalidPromptError,
    NoPendingApprovalError,
    RunAlreadyActiveError,
    SourceCatalogError,
    UnknownRunError,
    UploadCandidate,
)
from context_engine.tools import ToolApprovalDecision

API_PREFIX = "/api/v1"
DEFAULT_KEEPALIVE_SECONDS = 15.0

_ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}


class ApiError(Exception):
    """A structured error with an explicit status code."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, JsonValue] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = ErrorBody(code=code, message=message, details=details)


def _error_response(status_code: int, body: ErrorBody) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=ErrorResponse(error=body).model_dump(mode="json")
    )


def _application(request: Request) -> ContextEngineApplication:
    application: ContextEngineApplication = request.app.state.application
    return application


def _format_sse(event: RunEventModel) -> str:
    return f"id: {event.sequence}\nevent: {event.kind}\ndata: {event.model_dump_json()}\n\n"


def _event_stream(
    application: ContextEngineApplication, run_id: str, after_sequence: int, keepalive: float
) -> Iterator[str]:
    """Replay recorded events after ``after_sequence``, then follow live until the run ends."""
    last_seen = after_sequence
    while True:
        events, finished = application.wait_for_run_events(
            run_id, after_sequence=last_seen, timeout=keepalive
        )
        for event in events:
            last_seen = event.sequence
            yield _format_sse(RunEventModel.from_core(event))
        if finished:
            return
        if not events:
            yield ": keep-alive\n\n"


def _runs_router() -> APIRouter:
    router = APIRouter(prefix="/runs", tags=["runs"], responses=_ERROR_RESPONSES)

    @router.post("", status_code=202, response_model=RunSummaryModel)
    def start_run(body: StartRunRequest, request: Request) -> RunSummaryModel:
        return RunSummaryModel.from_core(_application(request).start_run(body.prompt))

    @router.get("", response_model=RunListResponse)
    def list_runs(request: Request) -> RunListResponse:
        runs = _application(request).list_runs()
        return RunListResponse(runs=[RunSummaryModel.from_core(run) for run in runs])

    @router.get("/{run_id}", response_model=RunDetailModel)
    def get_run(run_id: str, request: Request) -> RunDetailModel:
        return RunDetailModel.from_core(_application(request).get_run(run_id))

    @router.post("/{run_id}/approval", response_model=RunSummaryModel)
    def decide_approval(
        run_id: str, body: ApprovalDecisionRequest, request: Request
    ) -> RunSummaryModel:
        record = _application(request).resolve_approval(
            run_id, ToolApprovalDecision(body.decision), body.reason
        )
        return RunSummaryModel.from_core(record)

    @router.get(
        "/{run_id}/events",
        response_class=StreamingResponse,
        responses={
            200: {
                "description": (
                    "Server-sent events. Each frame has `id` (the event sequence), `event` "
                    "(the event kind) and `data` (a RunEventModel JSON document). Recorded "
                    "events are replayed first; the stream closes after `run_finished`."
                ),
                "content": {"text/event-stream": {"schema": RunEventModel.model_json_schema()}},
            }
        },
    )
    def stream_events(
        run_id: str,
        request: Request,
        after: Annotated[int, Query(ge=0)] = 0,
        last_event_id: Annotated[str | None, Header()] = None,
    ) -> StreamingResponse:
        application = _application(request)
        application.get_run(run_id)  # unknown ids fail before the stream opens
        resume_from = after
        if last_event_id is not None and last_event_id.isdigit():
            resume_from = max(resume_from, int(last_event_id))
        return StreamingResponse(
            _event_stream(application, run_id, resume_from, request.app.state.keepalive_seconds),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return router


def _sources_router() -> APIRouter:
    router = APIRouter(prefix="/sources", tags=["sources"], responses=_ERROR_RESPONSES)

    @router.get("", response_model=SourceListResponse)
    def list_sources(request: Request) -> SourceListResponse:
        return SourceListResponse.from_core(_application(request).list_sources())

    @router.post("", response_model=IngestionReportResponse)
    async def upload_sources(
        request: Request, files: Annotated[list[UploadFile], File()]
    ) -> IngestionReportResponse:
        candidates = []
        for upload in files:
            if not upload.filename:
                raise ApiError(422, "invalid_upload", "Every uploaded file needs a file name.")
            candidates.append(UploadCandidate(name=upload.filename, content=await upload.read()))
        return _ingest(_application(request), candidates)

    @router.post("/recover", response_model=RecoverSourcesResponse)
    def recover_sources(request: Request) -> RecoverSourcesResponse:
        try:
            outcomes = _application(request).recover_source_index()
        except SourceCatalogError as exc:
            raise ApiError(500, "source_recovery_failed", str(exc)) from exc
        return RecoverSourcesResponse(
            outcomes=[IngestionOutcomeModel.from_core(item) for item in outcomes]
        )

    @router.delete("/{source_id}", response_model=DeleteSourceResponse)
    def delete_source(source_id: str, request: Request) -> DeleteSourceResponse:
        application = _application(request)
        listing = application.list_sources()
        if any(item.source_id == source_id for item in listing.preloaded):
            raise ApiError(409, "source_not_deletable", "Preloaded sources cannot be deleted.")
        if not any(item.source_id == source_id for item in listing.uploaded):
            raise ApiError(404, "unknown_source", f"Unknown uploaded source: {source_id}")
        try:
            outcome = application.delete_upload(source_id)
        except SourceCatalogError as exc:
            raise ApiError(500, "source_operation_failed", str(exc)) from exc
        return DeleteSourceResponse(outcome=IngestionOutcomeModel.from_core(outcome))

    @router.delete("", response_model=ClearUploadsResponse)
    def clear_uploads(request: Request) -> ClearUploadsResponse:
        try:
            deleted = _application(request).clear_uploads()
        except SourceCatalogError as exc:
            raise ApiError(500, "source_operation_failed", str(exc)) from exc
        return ClearUploadsResponse(deleted_source_ids=list(deleted))

    return router


def _ingest(
    application: ContextEngineApplication, candidates: list[UploadCandidate]
) -> IngestionReportResponse:
    try:
        report = application.ingest_uploads(candidates)
    except SourceCatalogError as exc:
        raise ApiError(422, "source_rejected", str(exc)) from exc
    return IngestionReportResponse.from_core(report)


def _system_router() -> APIRouter:
    router = APIRouter(prefix="/system", tags=["system"], responses=_ERROR_RESPONSES)

    @router.get("", response_model=SystemResponse)
    def get_system(request: Request) -> SystemResponse:
        return SystemResponse.from_core(_application(request).describe_system())

    return router


def create_app(
    application: ContextEngineApplication,
    *,
    static_dir: Path | None = None,
    keepalive_seconds: float = DEFAULT_KEEPALIVE_SECONDS,
) -> FastAPI:
    """Build the HTTP adapter around one composed application.

    When ``static_dir`` exists it is served at ``/`` after the API routes.
    """
    app = FastAPI(
        title="Context Engine API",
        version="1",
        description="Local-only API. It has no authentication; bind it to loopback.",
    )
    app.state.application = application
    app.state.keepalive_seconds = keepalive_seconds

    @app.exception_handler(ApiError)
    def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error_response(exc.status_code, exc.body)

    @app.exception_handler(RunAlreadyActiveError)
    def _run_active(_: Request, exc: RunAlreadyActiveError) -> JSONResponse:
        body = ErrorBody(
            code="run_already_active",
            message=str(exc),
            details={"active_run_id": exc.active_run_id},
        )
        return _error_response(409, body)

    @app.exception_handler(UnknownRunError)
    def _unknown_run(_: Request, exc: UnknownRunError) -> JSONResponse:
        return _error_response(404, ErrorBody(code="unknown_run", message=str(exc)))

    @app.exception_handler(NoPendingApprovalError)
    def _no_pending_approval(_: Request, exc: NoPendingApprovalError) -> JSONResponse:
        return _error_response(409, ErrorBody(code="no_pending_approval", message=str(exc)))

    @app.exception_handler(InvalidPromptError)
    def _invalid_prompt(_: Request, exc: InvalidPromptError) -> JSONResponse:
        return _error_response(422, ErrorBody(code="invalid_prompt", message=str(exc)))

    @app.exception_handler(RequestValidationError)
    def _invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = json.loads(json.dumps(exc.errors(), default=str))
        body = ErrorBody(
            code="invalid_request",
            message="The request did not match the expected schema.",
            details={"errors": errors},
        )
        return _error_response(422, body)

    @app.exception_handler(HTTPException)
    def _http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(
            exc.status_code, ErrorBody(code="http_error", message=str(exc.detail))
        )

    for router in (_runs_router(), _sources_router(), _system_router()):
        app.include_router(router, prefix=API_PREFIX)

    if static_dir is not None and static_dir.is_dir():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return app
