export interface Club {
  id: number;
  name: string;
  description?: string;
  tags?: string; // comma‑separated, e.g. "AI,Programming,Tech"
  meeting_time?: string; // e.g. "Tue 18:00"
  location?: string;
  created_at?: Date;
}


export interface SwipeRecord {
  id: number;
  user_id: number;
  club_id: number;
  liked: boolean;
  created_at: Date;
}