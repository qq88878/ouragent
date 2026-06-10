import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authApi } from '@/api';

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('accessToken') || '');
    const refreshToken = ref(localStorage.getItem('refreshToken') || '');
    const user = ref(null);

    const isLoggedIn = computed(() => !!token.value);

    function setTokens(access, refresh) {
        token.value = access;
        refreshToken.value = refresh;
        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);
    }

    function clearAuth() {
        token.value = '';
        refreshToken.value = '';
        user.value = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    }

    async function login(username, password) {
        const res = await authApi.login(username, password);
        if (res.code === 200) setTokens(res.data.accessToken, res.data.refreshToken);
        return res;
    }

    async function register(form) {
        return await authApi.register(form);
    }

    async function fetchUser() {
        try {
            const res = await authApi.me();
            if (res.code === 200) user.value = res.data;
            return res;
        } catch { return null; }
    }

    async function logout() {
        try { await authApi.logout(); } catch { /* ignore */ }
        clearAuth();
    }

    return { token, refreshToken, user, isLoggedIn, login, register, fetchUser, logout, clearAuth };
});
