import api from './api';

export interface HistoryParams {
  skip?: number;
  limit?: number;
  status?: string;
  sync_type?: string;
  source_instance_id?: number;
  destination_instance_id?: number;
  start_date?: string;
  end_date?: string;
}

export interface HistoryPage<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// The API caps `limit` at 100 per request
const HISTORY_PAGE_SIZE = 100;
// Safety cap so a bad `total` can never loop forever
const HISTORY_MAX_PAGES = 50;

class HistoryService {
  async getHistory<T = unknown>(params: HistoryParams = {}): Promise<HistoryPage<T>> {
    const response = await api.get<HistoryPage<T>>('/history/', { params });
    return response.data;
  }

  /**
   * Fetch every history entry by paging through GET /history/ with limit=100
   * and an increasing skip until all `total` items are loaded (max 50 pages).
   */
  async getAllHistory<T = unknown>(filters: Omit<HistoryParams, 'skip' | 'limit'> = {}): Promise<T[]> {
    const items: T[] = [];
    let skip = 0;

    for (let pageIndex = 0; pageIndex < HISTORY_MAX_PAGES; pageIndex++) {
      const page = await this.getHistory<T>({ ...filters, skip, limit: HISTORY_PAGE_SIZE });
      items.push(...page.items);

      if (page.items.length === 0 || items.length >= page.total) {
        break;
      }
      skip += page.items.length;
    }

    return items;
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
