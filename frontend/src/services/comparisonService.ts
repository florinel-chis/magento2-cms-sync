import api from './api';
import { ComparisonRequest, ComparisonResult, DataType, DiffResult } from '../types';

interface DiffRequest {
  source_instance_id: number;
  destination_instance_id: number;
  data_type: DataType;
  identifier: string;
}

class ComparisonService {
  async compareBlocks(request: ComparisonRequest): Promise<ComparisonResult> {
    const response = await api.post('/compare/blocks', request);
    return response.data;
  }

  async comparePages(request: ComparisonRequest): Promise<ComparisonResult> {
    const response = await api.post('/compare/pages', request);
    return response.data;
  }

  async getItemDiff(request: DiffRequest): Promise<DiffResult> {
    const response = await api.post('/compare/diff', request);
    return response.data;
  }
}

export default new ComparisonService();