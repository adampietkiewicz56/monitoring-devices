import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (username, password, email) => api.post('/auth/register', { username, password, email }),
  logout: () => api.post('/auth/logout')
};

export const hostsAPI = {
  getAll: () => api.get('/hosts/'),
  search: (params) => api.get('/hosts/search', { params }),
  create: (host) => api.post('/hosts/', host),
  update: (id, host) => api.put(`/hosts/${id}`, host),
  delete: (id) => api.delete(`/hosts/${id}`)
};

export const alertsAPI = {
  getAll: () => api.get('/alerts/')
};

export const hostgroupsAPI = {
  getAll: () => api.get('/hostgroups/'),
  create: (group) => api.post('/hostgroups/', group),
  delete: (id) => api.delete(`/hostgroups/${id}`)
};

export default api;
