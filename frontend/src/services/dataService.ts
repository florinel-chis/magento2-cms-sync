import api from './api';
import { DataType, DataSnapshot } from '../types';

class DataService {
  async refreshInstanceData(instanceId: number, dataType: DataType): Promise<DataSnapshot> {
    const response = await api.post<DataSnapshot>(`/compare/refresh/${instanceId}`, null, {
      params: { data_type: dataType }
    });
    return response.data;
  }

  async getDataSnapshot(instanceId: number, dataType: DataType): Promise<DataSnapshot> {
    // This could be extended to fetch snapshot info
    const response = await api.get<DataSnapshot>(`/instances/${instanceId}/data/${dataType}`);
    return response.data;
  }
}

export default new DataService();