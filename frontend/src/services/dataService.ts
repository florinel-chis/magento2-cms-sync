import api from './api';
import { DataType } from '../types';

class DataService {
  async refreshInstanceData(instanceId: number, dataType: DataType): Promise<any> {
    const response = await api.post(`/compare/refresh/${instanceId}`, null, {
      params: { data_type: dataType }
    });
    return response.data;
  }

  async getDataSnapshot(instanceId: number, dataType: DataType): Promise<any> {
    // This could be extended to fetch snapshot info
    const response = await api.get(`/instances/${instanceId}/data/${dataType}`);
    return response.data;
  }
}

export default new DataService();