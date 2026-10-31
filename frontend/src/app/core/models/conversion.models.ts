export type OutputFormat = 'markdown' | 'html' | 'pdf' | 'docx';
export type ConversionStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'expired';

export interface ConversionDetail {
  success: boolean;
  conversion_id: string;
  original_name: string;
  input_format: 'docx' | 'pdf';
  output_format: OutputFormat;
  status: ConversionStatus;
  error: string;
  content: string | null;
  download_url: string | null;
  expires_at: string;
}

export interface ConversionQueuedResponse extends ConversionDetail {
  status: 'pending';
  status_url: string;
}

export interface ConversionErrorResponse {
  success: false;
  error: string;
}
