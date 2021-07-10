
from domainpy.infrastructure.records import TraceRecord

class TraceRecordManager:

    def get_trace_contexts(self, trace_id: str) -> tuple[TraceRecord.ContextResolution]:
        pass

    def store_in_progress(self, command: dict, contexts_resolutions: tuple[TraceRecord.ContextResolution]):
        pass # pragma: no cover

    def store_resolve_success(self, trace_id: str):
        pass # pragma: no cover

    def store_resolve_failure(self, trace_id: str):
        pass # pragma: no cover

    def store_context_resolve_success(self, trace_id: str, context: str):
        pass # pragma: no cover

    def store_context_resolve_failure(self, trace_id: str, context: str, error: str):
        pass # pragma: no cover
    