"""Herdr provider- and consumer-neutral orchestration core."""

from .taskgraph import (
    GRAPH_VERSION,
    GraphValidationError,
    LifecycleState,
    NodeRuntimeState,
    PersistentTaskGraph,
    TaskGraph,
    TaskGraphEnvelope,
    TaskNode,
)
from .scheduler import (
    AllowDecision,
    AuditLog,
    ChildProposal,
    DenyDecision,
    DenyReason,
    DynamicChildScheduler,
    SchedulerBudget,
    SchedulerError,
    Lease,
)
from .routing import (
    FailureKind,
    FailureScope,
    RejectedCandidate,
    RoutingDecision,
    RoutingError,
    bounded_fallback,
    classify_failure_scope,
    classify_failure,
    select_route,
)

__all__ = [
    "GRAPH_VERSION",
    "GraphValidationError",
    "LifecycleState",
    "NodeRuntimeState",
    "PersistentTaskGraph",
    "TaskGraph",
    "TaskGraphEnvelope",
    "TaskNode",
    "AllowDecision",
    "AuditLog",
    "ChildProposal",
    "DenyDecision",
    "DenyReason",
    "DynamicChildScheduler",
    "SchedulerBudget",
    "SchedulerError",
    "Lease",
    "FailureKind",
    "FailureScope",
    "RejectedCandidate",
    "RoutingDecision",
    "RoutingError",
    "bounded_fallback",
    "classify_failure_scope",
    "classify_failure",
    "select_route",
]
__version__ = "0.2.0"
from .workspace import (
    ArtifactIntegrityError,
    ArtifactRef,
    ConflictError,
    StaleBaseError,
    UnsafePathError,
    WorkspaceError,
    WorkspaceManager,
)
