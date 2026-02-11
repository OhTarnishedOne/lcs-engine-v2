/**
 * Shared API types matching backend schemas.
 */

// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

// Profile
export interface UserProfile {
  id: string;
  user_id: string;
  persona: string | null;
  experience_level: string | null;
  biggest_barrier: string | null;
  primary_goal: string | null;
  risk_tolerance: string | null;
  learning_preference: string | null;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

// Onboarding
export interface OnboardingQuestion {
  key: string;
  text: string;
  type: string;
  required: boolean;
  order: number;
  options: OnboardingOption[];
  placeholder: string | null;
  conditional: Record<string, unknown> | null;
}

export interface OnboardingOption {
  value: string;
  label: string;
  emoji?: string;
}

export interface OnboardingSection {
  section: number;
  title: string;
  subtitle: string;
  questions: OnboardingQuestion[];
}

export interface OnboardingQuestionsResponse {
  sections: OnboardingSection[];
  total_questions: number;
}

export interface OnboardingSubmitResult {
  section: number;
  saved_count: number;
  is_complete: boolean;
  next_section: number | null;
}

export interface OnboardingProgress {
  sections_completed: number[];
  current_section: number | null;
  questions_answered: number;
  total_questions: number;
  percent_complete: number;
  is_complete: boolean;
}

export interface OnboardingWelcome {
  name: string;
  persona: string;
  welcome_message: string;
  suggested_first_steps: string[];
  learning_path_preview: string[];
}

// Chat
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message_preview?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
}

// Strategies
export interface Strategy {
  id: string;
  user_id: string;
  name: string;
  strategy_type: string;
  risk_level: number;
  description: string;
  asset_allocation: Record<string, number>;
  rationale: string;
  risk_assessment: string;
  learning_points: string[];
  created_at: string;
}

export interface GenerateStrategyRequest {
  strategy_type?: string;
}

export interface StrategiesResponse {
  strategies: Strategy[];
  total: number;
}

export interface CompareStrategiesRequest {
  strategy_ids: string[];
}

export interface StrategyComparison {
  strategies: Strategy[];
  comparison: string;
  recommendation: string;
}

export interface ExplainStrategyRequest {
  question: string;
}

export interface ExplainStrategyResponse {
  strategy_id: string;
  question: string;
  explanation: string;
}

// Trading
export interface PortfolioResponse {
  equity: number;
  cash: number;
  buying_power: number;
  portfolio_value: number;
  day_pl: number;
  day_pl_pct: number;
  total_pl: number;
  total_pl_pct: number;
}

export interface Position {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_pl_pct: number;
  side: string;
}

export interface PositionsResponse {
  positions: Position[];
  total: number;
}

export interface PlaceOrderRequest {
  symbol: string;
  qty: number;
  side: "buy" | "sell";
  order_type: "market" | "limit";
  limit_price?: number;
  time_in_force?: string;
  strategy_id?: string;
  notes?: string;
}

export interface Order {
  id: string;
  symbol: string;
  qty: number;
  side: string;
  order_type: string;
  status: string;
  filled_avg_price: number | null;
  filled_qty: number;
  limit_price: number | null;
  created_at: string;
}

export interface OrdersResponse {
  orders: Order[];
  total: number;
}

export interface TradeHistory {
  id: string;
  symbol: string;
  qty: number;
  side: string;
  order_type: string;
  filled_price: number | null;
  status: string;
  strategy_id: string | null;
  notes: string | null;
  created_at: string;
}

export interface TradeHistoryResponse {
  trades: TradeHistory[];
  total: number;
}

export interface SymbolSearchResult {
  symbol: string;
  name: string;
  type: string;
  exchange: string;
}

export interface Quote {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
}

export interface CompanyInfo {
  symbol: string;
  name: string;
  description: string;
  sector: string;
  industry: string;
  market_cap: number;
  employees: number;
}

// Probability Lab
export interface PredictionMarket {
  id: string;
  external_id: string | null;
  title: string;
  description: string | null;
  category: string;
  market_probability: number | null;
  close_date: string;
  is_resolved: boolean;
  resolution: string | null;
  explainer: string | null;
  investing_connection: string | null;
}

export interface MarketsResponse {
  markets: PredictionMarket[];
  total: number;
}

export interface SubmitPredictionRequest {
  market_id: string;
  probability: number;
  reasoning?: string;
}

export interface UserPrediction {
  id: string;
  market_id: string;
  market_title: string;
  predicted_probability: number;
  market_probability: number | null;
  reasoning: string | null;
  brier_score: number | null;
  created_at: string;
}

export interface PredictionsResponse {
  predictions: UserPrediction[];
  total: number;
}

export interface CalibrationBucket {
  bucket: string;
  predicted_avg: number;
  actual_pct: number;
  count: number;
}

export interface BiasInfo {
  bias_type: string;
  description: string;
  investing_impact: string;
}

export interface CalibrationResponse {
  total_predictions: number;
  resolved_predictions: number;
  average_brier_score: number | null;
  calibration_curve: CalibrationBucket[];
  detected_biases: BiasInfo[];
}

// API Error
export interface ApiError {
  detail: string;
}
