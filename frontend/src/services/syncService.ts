import api from './api';
import { SyncRequest, SyncPreview, SyncResult, DataType } from '../types';

class SyncService {
  async previewSync(request: SyncRequest): Promise<SyncPreview> {
    const response = await api.post('/sync/preview', request);
    return response.data;
  }

  async syncBlocks(request: SyncRequest): Promise<SyncResult> {
    const response = await api.post('/sync/blocks', request);
    return response.data;
  }

  async syncPages(request: SyncRequest): Promise<SyncResult> {
    const response = await api.post('/sync/pages', request);
    return response.data;
  }

  async getSyncStatus(syncId: number): Promise<SyncResult> {
    const response = await api.get(`/sync/status/${syncId}`);
    return response.data;
  }
}

export default new SyncService();