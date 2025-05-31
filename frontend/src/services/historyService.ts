import api from './api';

interface HistoryParams {
  skip?: number;
  limit?: number;
  status?: string;
  sync_type?: string;
  source_instance_id?: number;
  destination_instance_id?: number;
  start_date?: string;
  end_date?: string;
}

class HistoryService {
  async getHistory(params: HistoryParams = {}) {
    const response = await api.get('/history/', { params });
    return response.data;
  }

  async getStatistics(period: 'today' | 'week' | 'month' | 'all' = 'today') {
    const response = await api.get('/history/statistics', { params: { period } });
    return response.data;
  }

  async getSyncDetails(syncId: number) {
    const response = await api.get(`/history/${syncId}`);
    return response.data;
  }
}

export default new HistoryService();