export type CoachingCategory =
  | 'objection_handling'
  | 'pacing'
  | 'active_listening'
  | 'professionalism'
  | 'product_knowledge';

export type CoachingSeverity = 'suggestion' | 'important' | 'critical';

export interface CoachingRecommendationData {
  id: string;
  ref: string; // e.g. "C1", "C2"
  category: CoachingCategory | string;
  recommendation: string;
  context_quote?: string | null;
  severity: CoachingSeverity;
  utterance_id?: string | null;
  start_ms?: number | null;
  created_at?: string;
}
