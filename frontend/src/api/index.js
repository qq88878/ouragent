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
    sendVerifyCode(email) { return http.post('/auth/send-verify-code', null, { params: { email } }); },
    verifyEmail(email, code) { return http.post('/auth/verify-email', { email, code }); },
};

export const userApi = {
    getProfile() { return http.get('/users/me'); },
    updateProfile(data) { return http.put('/users/me', data); },
    listUsers(page = 1, size = 10) { return http.get('/users/', { params: { page, size } }); },
    getUserById(id) { return http.get(`/users/${id}`); },
    updateStatus(id, status) { return http.put(`/users/${id}/status`, null, { params: { status } }); },
    deleteUser(id) { return http.delete(`/users/${id}`); },
};

export default http;