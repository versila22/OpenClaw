export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Substance {
  id: string;
  name: string;
  category: string;
  description?: string | null;
  risk_level: string;
}

export interface DailyLog {
  id: string;
  user_id: string;
  substance_id: string;
  log_date: string;
  craving_level: number;
  quantity_used?: number | null;
  mood_score?: number | null;
  cbt_notes?: string | null;
  trigger_notes?: string | null;
}

export interface AssessmentResult {
  route: string;
  payload: {
    node: string;
    severity: string;
    message?: string;
    exercise?: {
      name: string;
      steps: string[];
    };
    local_resource?: {
      type: string;
      search_hint: string;
      directory_url: string;
    };
    notes_context?: string | null;
  };
}
