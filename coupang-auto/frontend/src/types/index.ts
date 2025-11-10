// User types
export interface User {
  id: number;
  email: string;
  full_name: string;
  phone: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

// Tenant types
export interface Tenant {
  id: number;
  name: string;
  slug: string;
  plan: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  tenant_name: string;
  tenant_slug: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  tenant: Tenant;
}

// Sales Data types
export interface SalesRecord {
  id: number;
  date: string;
  product_name: string;
  option_name: string;
  sales_amount: number;
  ad_cost: number;
  quantity: number;
  margin?: number;
  net_profit?: number;
  margin_rate?: number;
  created_at: string;
}

export interface SalesStats {
  total_sales: number;
  total_ad_cost: number;
  total_net_profit: number;
  total_quantity: number;
  avg_margin_rate: number;
  record_count: number;
}

// Upload types
export interface UploadHistory {
  id: number;
  file_name: string;
  file_type: string;
  status: 'success' | 'failed' | 'processing';
  record_count: number;
  uploaded_at: string;
  error_message?: string;
}

// Margin types
export interface MarginData {
  id: number;
  product_name: string;
  option_name: string;
  margin_amount: number;
  margin_rate: number;
  start_date: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

// Team types
export interface TeamMember {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'member' | 'viewer';
  is_active: boolean;
  joined_at: string;
}

// Chart types
export interface ChartData {
  date: string;
  sales: number;
  ad_cost: number;
  net_profit: number;
}

// Pagination types
export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Export types
export interface ExportOptions {
  start_date: string;
  end_date: string;
  group_by: 'option' | 'product';
  period_display: 'daily' | 'total';
  file_format: 'xlsx' | 'csv';
  include_fields: string[];
}

// Common types
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface MessageState {
  success: string;
  error: string;
}
