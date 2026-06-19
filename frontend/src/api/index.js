import axios from 'axios';

const http = axios.create({
    baseURL: '/api',
    timeout: 30000,
});

http.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

http.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('accessToken');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const authApi = {
    login(username, password) { return http.post('/auth/login', { username, password }); },
    register(data) { return http.post('/auth/register', data); },
    logout() { return http.post('/auth/logout'); },
    me() { return http.get('/auth/me'); },
    sendVerifyCode(email) { return http.post('/auth/send-verify-code', { email }); },
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

export const courseApi = {
    list(params) { return http.get('/courses', { params }); },
    getById(id) { return http.get(`/courses/${id}`); },
    create(data) { return http.post('/courses', data); },
    update(id, data) { return http.put(`/courses/${id}`, data); },
    delete(id) { return http.delete(`/courses/${id}`); },
    enroll(id) { return http.post(`/courses/${id}/enroll`); },
    getEnrolled() { return http.get('/courses/enrolled'); },
};

export const chatApi = {
    createSession(courseId) { return http.post('/chat/sessions', null, { params: { courseId } }); },
    listSessions() { return http.get('/chat/sessions'); },
    getMessages(sessionId, page = 1, size = 20) {
        return http.get(`/chat/sessions/${sessionId}/messages`, { params: { page, size } });
    },
    sendMessage(sessionId, message) {
        return http.post(`/chat/sessions/${sessionId}/messages`, { message });
    },
    async *sendMessageStream(sessionId, message, signal) {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(`/api/chat/sessions/${sessionId}/messages/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ message }),
            signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();
            for (const line of lines) {
                if (line.startsWith('data:')) {
                    const data = line.slice(line.charAt(5) === ' ' ? 6 : 5).trim();
                    if (data) {
                        try {
                            yield JSON.parse(data);
                        } catch { /* skip malformed */ }
                    }
                }
            }
        }
    },
    deleteSession(sessionId) { return http.delete(`/chat/sessions/${sessionId}`); },
};

export const learningApi = {
    generatePath(data) { return http.post('/learning/paths/generate', data); },
    listPaths() { return http.get('/learning/paths/'); },
    getPathById(id) { return http.get(`/learning/paths/${id}`); },
    updateStepStatus(pathId, stepId, status) {
        return http.put(`/learning/paths/${pathId}/steps/${stepId}`, null, { params: { status } });
    },
    deletePath(id) { return http.delete(`/learning/paths/${id}`); },
    getProfile() { return http.get('/profile/'); },
    updateProfile(data) { return http.put('/profile/', data); },
    getRadarData() { return http.get('/profile/radar'); },
    recordStudy(data) { return http.post('/study/records/', data); },
    listRecords(page = 1, size = 10) { return http.get('/study/records/', { params: { page, size } }); },
    getStudyStats() { return http.get('/study/records/stats'); },

    // 瀛︿範鐢诲儚闂嵎
    getQuestionnaire() { return http.get('/profile/questionnaire/'); },
    saveQuestionnaire(data) { return http.put('/profile/questionnaire/', data); },
    getQuestionnaireStatus() { return http.get('/profile/questionnaire/status'); },
};

export const knowledgeApi = {
    upload(file, courseId, name, description) {
        const formData = new FormData();
        formData.append('file', file);
        if (courseId != null) formData.append('courseId', courseId);
        if (name) formData.append('name', name);
        if (description) formData.append('description', description);
        return http.post('/knowledge/upload', formData);
    },
    list(courseId) { return http.get('/knowledge', { params: { courseId } }); },
    listAll() { return http.get('/knowledge/all'); },
    listPending() { return http.get('/knowledge/pending'); },
    getById(id) { return http.get(`/knowledge/${id}`); },
    assignToCourse(id, courseId) { return http.put(`/knowledge/${id}/assign`, null, { params: { courseId } }); },
    delete(id) { return http.delete(`/knowledge/${id}`); },
    reprocess(id) { return http.post(`/knowledge/${id}/reprocess`); },
    search(keyword) { return http.get('/knowledge/search', { params: { keyword } }); },
    getContent(id) { return http.get(`/knowledge/${id}/content`); },
    approve(id, approved, remark) { return http.post(`/knowledge/${id}/approve`, null, { params: { approved, remark } }); },
    batchApprove(ids, approved, remark) { return http.post('/knowledge/batch-approve', { ids, approved, remark }); },
};

export const adminApi = {
    getDashboard() { return http.get('/admin/dashboard'); },
    getSystemHealth() { return http.get('/admin/system/health'); },
};


export const scheduleApi = {
    getConfig() { return http.get('/schedule/config'); },
    saveConfig(data) { return http.put('/schedule/config', data); },
    listCourses() { return http.get('/schedule/courses'); },
    createCourse(data) { return http.post('/schedule/courses', data); },
    updateCourse(id, data) { return http.put(`/schedule/courses/${id}`, data); },
    deleteCourse(id) { return http.delete(`/schedule/courses/${id}`); },
    getWeekView(weekOffset = 0) { return http.get('/schedule/week-view', { params: { weekOffset } }); },
};

// Agent service??????JWT?????????
const agentHttp = axios.create({
    baseURL: '/agent',
    timeout: 120000,
});
agentHttp.interceptors.request.use((config) => {
    const token = localStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});
agentHttp.interceptors.response.use(
    (response) => response.data,
    (error) => Promise.reject(error)
);


// 错题本API
export const mistakeBookApi = {
    add(data) { return agentHttp.post('/mistake-book/add', data); },
    list(userId, params = {}) { return agentHttp.get(`/mistake-book/list/${userId}`, { params }); },
    review(data) { return agentHttp.post('/mistake-book/review', data); },

    delete(mistakeId) { return agentHttp.delete(`/mistake-book/${mistakeId}`); },
    clearAll(userId) { return agentHttp.delete(`/mistake-book/user/${userId}`); },
    stats(userId) { return agentHttp.get(`/mistake-book/stats/${userId}`); },
    dueReviews(userId, limit = 20) { return agentHttp.get(`/mistake-book/due/${userId}`, { params: { limit } }); },
    diagnose(data) { return agentHttp.post('/mistake-book/diagnose', data); },
    practice(data) { return agentHttp.post('/mistake-book/practice', data); },
    dailyReview(userId) { return agentHttp.post('/mistake-book/daily-review', new URLSearchParams({ user_id: userId })); },
    notifications(userId, limit = 10) { return agentHttp.get(`/mistake-book/notifications/${userId}`, { params: { limit } }); },
};

export default http;