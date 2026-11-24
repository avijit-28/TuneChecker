import type { ToneVerdict } from './verdict';
import type { CoachingRecommendationData } from './coaching';

export interface EvidenceItemData {
  id: string;
  ref: string;
  utterance_id: string;
  speaker_label: string;
  quote: string;
  char_start: number;
  char_end: number;
  criterion_id: string;
  severity: number;
  rationale: string;
  start_ms: number;
}

export type ActionItemType =
  | 'commitment'
  | 'follow_up'
  | 'information_promised'
  | 'customer_task'
  | string;

export interface ActionItemData {
  id: string;
  ref: string;
  type: ActionItemType;
  task: string;
  modality: 'definite' | 'tentative';
  owner: {
    text: string | null;
    basis: string;
  };
  deadline: string | null;
  quote: string;
  char_start?: number;
  char_end?: number;
  utterance_id: string;
  start_ms: number;
}

export interface AnalysisConfidence {
  level: 'low' | 'medium' | 'high' | string;
  factors: Record<string, any>;
}

export interface SettingsSnapshot {
  version: number;
  sensitivity: string;
}

export interface AnalysisDetail {
  id: string;
  call_id: string;
  run_number: number;
  status: 'complete' | 'partial' | 'failed' | string;
  verdict: ToneVerdict | null;
  confidence: AnalysisConfidence;
  calibrated_model?: {
    calibrated_verdict: string;
    confidence: number;
    training_samples_count: number;
  };
  limited_evidence_reason?: string | null;
  explanation: string;
  sales_rep?: {
    label: string;
    source: string;
    status: string;
  } | null;
  evidence: EvidenceItemData[];
  action_items: ActionItemData[];
  coaching_recommendations?: CoachingRecommendationData[];
  settings_snapshot?: SettingsSnapshot;
  created_at: string;
}
