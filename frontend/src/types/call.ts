import type { ToneVerdict } from './verdict';

export interface CallListItemData {
  id: string;
  name: string;
  status: string;
  status_group: string;
  tone: ToneVerdict | null;
  duration_ms: number | null;
  size_bytes: number;
  is_synthetic: boolean;
  created_at: string;
}
