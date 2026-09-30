export interface User {
  id: number;
  email: string;
  full_name: string;
  phone_number: string;
  is_email_verified: boolean;
  date_joined: string;
}

export type Pace = "relaxed" | "balanced" | "intense";
export type BudgetScope = "per_person" | "group";
export type IntercityTransport = "flight" | "train" | "bus" | "personal_car" | "unknown";
export type LocalTransport = "public_transit" | "taxi" | "rental_car" | "walking" | "mixed" | "unknown";

export interface Assumption {
  field: string;
  assumption: string;
  reason: string;
}

export interface TripPreferences {
  adults_count: number | null;
  children_count: number | null;
  has_older_adults: boolean | null;
  arrival_time: string | null;
  departure_time: string | null;
  intercity_transport: IntercityTransport;
  local_transport: LocalTransport;
  interests: string[];
  pace: Pace | null;
  budget_amount: number | null;
  budget_scope: BudgetScope | null;
  accessibility_notes: string;
  has_existing_accommodation: boolean | null;
  accommodation_notes: string;
  room_count: number | null;
  nightly_accommodation_budget: number | null;
  assumptions: Assumption[];
  updated_at: string;
}

export type TripStatus =
  | "collecting_info"
  | "ready_for_generation"
  | "generating"
  | "planned"
  | "archived";

export interface Trip {
  id: string;
  title: string;
  origin: string;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  timezone: string;
  status: TripStatus;
  preferences: TripPreferences;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export type PlanningJobStatus = "pending" | "running" | "succeeded" | "failed";

export interface PlanningJob {
  id: number;
  status: PlanningJobStatus;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface PlaceRef {
  id: number;
  name: string;
  category: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
  neshan_poi_id: string;
  source: "tavily" | "neshan" | "model";
  source_url: string;
}

export interface ItineraryItem {
  id: number;
  order: number;
  start_time: string | null;
  end_time: string | null;
  title: string;
  description: string;
  category: "sight" | "food" | "transport" | "rest" | "accommodation" | "other";
  place: PlaceRef | null;
}

export interface ItineraryDay {
  id: number;
  day_index: number;
  date: string | null;
  city: string;
  notes: string;
  items: ItineraryItem[];
}

export interface Itinerary {
  id: number;
  version: number;
  summary: string;
  model_name: string;
  generated_at: string;
  days: ItineraryDay[];
}

export interface Accommodation {
  id: number;
  name: string;
  room_type: string;
  nightly_price: number | null;
  is_selected: boolean;
  source: string;
  place: PlaceRef | null;
}
