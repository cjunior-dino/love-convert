export type OutputFormat = 'markdown' | 'html' | 'pdf' | 'docx';

export interface ConversionSuccessResponse {
  success: true;
  original_name: string;
  output_format: OutputFormat;
  content: string | null;
  download_url: string;
}

export interface ConversionErrorResponse {
  success: false;
  error: string;
}

export type ConversionResponse =
  | ConversionSuccessResponse
  | ConversionErrorResponse;
