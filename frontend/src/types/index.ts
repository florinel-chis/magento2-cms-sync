export interface Instance {
  id: number;
  name: string;
  url: string;
  api_token: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataSnapshot {
  instance_id: number;
  data_type: DataType;
  item_count: number;
  created_at: string;
  file_path: string;
}

export interface InstanceCreate {
  name: string;
  url: string;
  api_token: string;
  is_active?: boolean;
}

export interface InstanceUpdate {
  name?: string;
  url?: string;
  api_token?: string;
  is_active?: boolean;
}

export interface InstanceTestResult {
  success: boolean;
  message: string;
  version?: string;
  store_views?: StoreView[];
}

export interface StoreView {
  id: number;
  code: string;
  name: string;
  website_id: number;
  store_group_id: number;
  is_active: boolean;
}

// Magento CMS content types
export interface CMSBlock {
  id: number;
  identifier: string;
  title: string;
  content: string;
  is_active: boolean;
  store_id: number[];
  creation_time?: string;
  update_time?: string;
}

export interface CMSPage {
  id: number;
  identifier: string;
  title: string;
  url_key: string;
  content: string;
  content_heading?: string;
  is_active: boolean;
  store_id: number[];
  page_layout?: string;
  meta_title?: string;
  meta_keywords?: string;
  meta_description?: string;
  creation_time?: string;
  update_time?: string;
}

// Union type for CMS content
export type CMSContent = CMSBlock | CMSPage;

export enum DataType {
  BLOCKS = 'blocks',
  PAGES = 'pages',
}

export enum ComparisonStatus {
  EXISTS = 'exists',
  MISSING = 'missing',
  DIFFERENT = 'different',
}

export interface ComparisonRequest {
  source_instance_id: number;
  destination_instance_id: number;
  force_refresh?: boolean;
}

export interface ComparisonItem {
  identifier: string;
  title: string;
  source_status: ComparisonStatus;
  destination_status: ComparisonStatus;
  source_data?: CMSContent;  // Type-safe: CMSBlock | CMSPage
  destination_data?: CMSContent;  // Type-safe: CMSBlock | CMSPage
  differences?: string[];
}

export interface ComparisonResult {
  source_instance: Instance;
  destination_instance: Instance;
  data_type: DataType;
  total_source: number;
  total_destination: number;
  exists_in_both: number;
  missing_in_destination: number;
  missing_in_source: number;
  different: number;
  items: ComparisonItem[];
  compared_at: string;
}

export interface DiffField {
  field_name: string;
  source_value: string | number | boolean | null | string[] | number[];  // Explicit union type
  destination_value: string | number | boolean | null | string[] | number[];  // Explicit union type
  is_different: boolean;
}

export interface DiffResult {
  identifier: string;
  data_type: DataType;
  fields: DiffField[];
  source_stores: string[];
  destination_stores: string[];
  has_differences?: boolean; // Computed on frontend
  destination_exists?: boolean; // Computed on frontend
}

export interface SyncItem {
  identifier: string;
  action: 'create' | 'update';
  fields_to_sync?: string[];
}

export interface SyncRequest {
  source_instance_id: number;
  destination_instance_id: number;
  data_type: DataType;
  items: SyncItem[];
  store_view_mapping?: Record<string, string>;
}

export interface SyncPreviewItem {
  identifier: string;
  title: string;
  action: 'create' | 'update';
}

export interface SyncPreview {
  items: SyncPreviewItem[];  // Type-safe array
  total_changes: number;
  creates: number;
  updates: number;
}

export interface SyncDetailItem {
  identifier: string;
  status: 'success' | 'failed';
  message?: string;
}

export interface SyncResult {
  sync_id: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  items_synced: number;
  items_failed: number;
  started_at: string;
  completed_at?: string;
  details: SyncDetailItem[];  // Type-safe array
  error_message?: string;
}