import type { components } from './schema'

type Schemas = components['schemas']

export type RunDetail = Schemas['RunDetailModel']
export type RunSummary = Schemas['RunSummaryModel']
export type RunEvent = Schemas['RunEventModel']
export type RunStatus = Schemas['RunStatus']
export type PendingApproval = Schemas['PendingApprovalModel']
export type ToolResult = Schemas['ToolResultModel']
export type ToolTrace = Schemas['ToolTraceModel']
export type SystemInfo = Schemas['SystemResponse']
export type SourceListing = Schemas['SourceListResponse']
export type Source = Schemas['SourceModel']
export type SourceDiagnostic = Schemas['DiagnosticModel']
export type IngestionReport = Schemas['IngestionReportResponse']
export type IngestionOutcome = Schemas['IngestionOutcomeModel']
export type RecoveryReport = Schemas['RecoverSourcesResponse']
export type DeleteSourceReport = Schemas['DeleteSourceResponse']
export type ClearUploadsReport = Schemas['ClearUploadsResponse']
export type ApprovalDecision = Schemas['ApprovalDecisionRequest']['decision']

/** A run is still executing, or paused for a person's decision. */
export function isActive(status: RunStatus): boolean {
  return status === 'running' || status === 'awaiting_approval'
}
