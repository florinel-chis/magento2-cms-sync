import api from './api';
import { Instance, InstanceCreate, InstanceUpdate, InstanceTestResult } from '../types';

class InstanceService {
  async getAll(): Promise<Instance[]> {
    const response = await api.get('/instances');
    return response.data;
  }

  async getById(id: number): Promise<Instance> {
    const response = await api.get(`/instances/${id}`);
    return response.data;
  }

  async create(data: InstanceCreate): Promise<Instance> {
    const response = await api.post('/instances', data);
    return response.data;
  }

  async update(id: number, data: InstanceUpdate): Promise<Instance> {
    const response = await api.put(`/instances/${id}`, data);
    return response.data;
  }

  async delete(id: number): Promise<void> {
    await api.delete(`/instances/${id}`);
  }

  async testConnection(id: number): Promise<InstanceTestResult> {
    const response = await api.post(`/instances/${id}/test`);
    return response.data;
  }

  async getAllDataSnapshots(): Promise<any> {
    const response = await api.get('/instances/data-snapshots/all');
    return response.data;
  }
}

export default new InstanceService();