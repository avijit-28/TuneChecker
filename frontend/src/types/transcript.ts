export interface UtteranceItem {
  id: string;
  idx: number;
  speaker_label: string;
  start_ms: number;
  end_ms: number;
  text: string;
  asr_confidence?: number | null;
}

export interface SpeakerInfo {
  label: string;
  role: string;
  source: 'auto' | 'user';
  status: string;
  level?: string | null;
  talk_time_ms: number;
  turn_count: number;
}

export interface TranscriptData {
  utterances: UtteranceItem[];
  speakers: SpeakerInfo[];
}
