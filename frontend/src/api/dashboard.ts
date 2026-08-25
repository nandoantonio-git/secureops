import { apiGet, apiPost } from './client';

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type SeverityBucket = Severity | 'resolved_accepted';

export type FindingStatus =
  | 'open'
  | 'in_investigation'
  | 'resolved'
  | 'false_positive'
  | 'accepted_risk';

export interface SeverityDistributionSegment {
  bucket: SeverityBucket;
  count: number;
}

export interface SeverityDistribution {
  repository: string;
  segments: SeverityDistributionSegment[];
  total: number;
}

export interface WeeklyTrendPoint {
  week_start: string;
  count: number;
}

export interface WeeklyTrend {
  repository: string;
  points: WeeklyTrendPoint[];
}

export interface TopCriticalFile {
  file_path: string;
  count: number;
  finding_id: string;
  line_start: number;
}

export interface TopCriticalFiles {
  repository: string;
  files: TopCriticalFile[];
}

export interface FindingListItem {
  id: string;
  file_path: string;
  line_start: number;
  line_end: number | null;
  rule_id: string;
  category: string | null;
  severity: Severity;
  status: FindingStatus;
  short_description: string;
  fingerprint: string;
}

export interface FindingListPage {
  items: FindingListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface FindingListParams {
  repository: string;
  status?: FindingStatus;
  severity?: Severity;
  limit?: number;
  offset?: number;
}

export type OverrideChangeType =
  | 'status_change'
  | 'severity_override'
  | 'risk_acceptance'
  | 'reopen';

export interface OverrideFindingRequest {
  changed_by: string;
  change_type: OverrideChangeType;
  to_value: string;
  reason: string;
}

export function getSeverityDistribution(
  repository: string,
): Promise<SeverityDistribution> {
  return apiGet<SeverityDistribution>('/dashboard/severity-distribution', {
    repository,
  });
}

export function getWeeklyTrend(repository: string): Promise<WeeklyTrend> {
  return apiGet<WeeklyTrend>('/dashboard/weekly-trend', { repository });
}

export function getTopCriticalFiles(
  repository: string,
  limit = 5,
): Promise<TopCriticalFiles> {
  return apiGet<TopCriticalFiles>('/dashboard/top-critical-files', {
    repository,
    limit,
  });
}

export function getFindings(
  params: FindingListParams,
): Promise<FindingListPage> {
  const { repository, status, severity, limit = 20, offset = 0 } = params;
  return apiGet<FindingListPage>('/dashboard/findings', {
    repository,
    status,
    severity,
    limit,
    offset,
  });
}

export function overrideFinding(
  findingId: string,
  request: OverrideFindingRequest,
): Promise<unknown> {
  return apiPost(`/findings/${findingId}/override`, request);
}
