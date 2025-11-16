export interface Club {
  club_id: number;
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

export interface User {
  id: number;
  email: string;
  name?: string;
  year?: string;
  major?: string;
  interests?: string;
  created_at: string;
}

export interface Event {
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
  is_online: boolean;
  join_link?: string | null;
  capacity?: number;
  visibility_mode: string;
  visible_email_domains?: string[];
}