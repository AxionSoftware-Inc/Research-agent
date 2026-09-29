export interface ToolCall {
  id?: string;
  name: string;
  args: Record<string, any>;
  result?: string;
  status: "running" | "done" | "error";
}

export interface Attachment {
  file_name: string;
  path: string;
  is_image: boolean;
  size: number;
  preview_text?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  thinking?: string;
  progress?: string;
  toolCalls?: ToolCall[];
  attachments?: Attachment[];
  timestamp: number;
}

export interface PlanData {
  steps: string[];
  current_step: number;
  notes: string;
  summary: string;
}

export interface CheckpointItem {
  id: string;
  description: string;
  time: string;
  files: string[];
}

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  children?: FileNode[];
}

export interface Project {
  id: string;
  name: string;
  path: string;
  created_at: number;
  is_active?: boolean;
  chat_count?: number;
}

export interface ChatSession {
  id: string;
  name: string;
  model: string;
  project_id?: string;
  is_running: boolean;
  tokens: number;
  created_at: number;
}


export interface ModelPricing {
  input_cost_per_1m: number;
  output_cost_per_1m: number;
  is_local: boolean;
}

export interface ModelItem {
  id: string;
  name: string;
  provider: "ollama" | "openai_compatible";
  base_url: string;
  model_name: string;
  api_key?: string | null;
  input_cost_per_1m: number;
  output_cost_per_1m: number;
  is_local: boolean;
}

export interface ServerStatus {
  status: string;
  current_model: string;
  available_models: string[];
  models_detailed?: ModelItem[];
  workspace: string;
  checkpoints_count: number;
  active_plan: string;
  token_estimate: number;
  token_max: number;
  token_percent: number;
  is_running: boolean;
  active_session: string;
  sessions_count: number;
  total_cost_usd?: number;
  total_input_tokens?: number;
  total_output_tokens?: number;
  model_pricing?: ModelPricing;
  vram?: VramStatus;
}

export interface VramModel {
  name: string;
  model: string;
  size_gb: number;
  size_vram_gb: number;
  expires_at?: string;
}

export interface VramStatus {
  online: boolean;
  models: VramModel[];
  total_vram_gb: number;
  count: number;
}


export interface AppSettings {
  ollama_url: string;
  default_model: string;
  temperature: number;
  max_iterations: number;
  system_prompt: string;
  workspace_dir: string;
  plan_mode_auto?: boolean;
  critic_enabled?: boolean;
  auto_flush_context?: boolean;
  context_window_size?: number;
  top_p?: number;
}

