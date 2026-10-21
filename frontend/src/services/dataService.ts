import api from './api';
import { DataType, DataSnapshot, InstanceDataSnapshots } from '../types';

class DataService {
  async refreshInstanceData(instanceId: number, dataType: DataType): Promise<DataSnapshot> {
    const response = await api.post<DataSnapshot>(`/compare/refresh/${instanceId}`, null, {
      params: { data_type: dataType }
    });
    return response.data;
  }

  async getDataSnapshot(instanceId: number): Promise<InstanceDataSnapshots> {
    // GET /instances/{id}/data-snapshots returns the latest blocks/pages snapshot summary
    const response = await api.get<InstanceDataSnapshots>(`/instances/${instanceId}/data-snapshots`);
    return response.data;
  }
}

export default new DataService();
