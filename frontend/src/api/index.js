import axios from 'axios';

const http = axios.create({
    baseURL: '/api',
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
});

http.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

http.interceptors.response.use(
    (response) => response.data,
    (error) => Promise.reject(error)
);

export const authApi = {
    login(username, password) { return http.post('/auth/login', { username, password }); },
    register(data) { return http.post('/auth/register', data); },
    logout() { return http.post('/auth/logout'); },
    me() { return http.get('/auth/me'); },
};

export default http;
