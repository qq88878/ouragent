import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { learningApi, chatApi } from "@/api";
import axios from "axios";

export const useProfileStore = defineStore("profile", () => {
  // Core profile data
  const basicProfile = ref(null);
  const radarData = ref(null);
  const courseProfile = ref(null);
  const sessionSignals = ref(null);

  // UI state
  const loading = ref(false);
  const refreshing = ref(false);
  const error = ref("");
  const lastUpdated = ref(null);
  const profileVersion = ref(0);
  const panelCollapsed = ref(false);

  // Whether basic profile has been loaded at all
  const hasProfile = computed(() => basicProfile.value !== null);

  // Live radar dimensions: merge backend scores with real-time chat signals
  const liveDimensions = computed(() => {
    const base = radarData.value?.dimensions || {};
    if (typeof base !== "object" || Object.keys(base).length === 0) {
      return {}
    }
    const signals = sessionSignals.value || {};
    const topics = signals.active_topics || [];
    const gaps = signals.gap_keywords || [];
    const dist = signals.difficulty_distribution || {};
    const exchanges = signals.exchange_count || 0;

    const result = { ...base };

    if (topics.length > 0) {
      const theoryBoost = Math.min(topics.length * 3, 30);
      result["理论知识"] = Math.min(100, (base["理论知识"] || 50) + theoryBoost);
    }
    if (gaps.length > 0) {
      const solveBoost = Math.min(gaps.length * 5, 25);
      result["问题解决"] = Math.min(100, (base["问题解决"] || 50) + solveBoost);
    }
    const total = (dist.beginner || 0) + (dist.neutral || 0) + (dist.advanced || 0);
    if (total > 0) {
      const advRatio = (dist.advanced || 0) / total;
      result["实践能力"] = Math.min(100, (base["实践能力"] || 50) + Math.round(advRatio * 20));
    }
    if (exchanges > 0) {
      result["协作能力"] = Math.min(100, (base["协作能力"] || 50) + Math.min(exchanges, 20));
    }
    if (topics.length > 3) {
      result["创新思维"] = Math.min(100, (base["创新思维"] || 50) + 10);
    }

    return result;
  });

  const displayProfile = computed(() => {
    const base = basicProfile.value || {};
    const signals = sessionSignals.value || {};
    const course = courseProfile.value || {};
    return {
      learningStyle: base.learningStyle || "VISUAL",
      strengths: base.strengths || "",
      weaknesses: base.weaknesses || "",
      interests: base.interests || "",
      gradeLevel: base.gradeLevel || "BEGINNER",
      preferences: base.preferences ? safeJsonParse(base.preferences) : {},
      dimensions: liveDimensions.value,
      activeTopics: signals.active_topics || [],
      difficultyDistribution: signals.difficulty_distribution || {},
      gapKeywords: signals.gap_keywords || [],
      exchangeCount: signals.exchange_count || 0,
      courseInsights: course.insights || "",
    };
  });

  function safeJsonParse(str) {
    try { return JSON.parse(str); } catch { return {}; }
  }

  async function loadBasicProfile(force = false) {
    // Allow forced refresh even if loading
    if (loading.value && !force) {
      console.log("[ProfileStore] loadBasicProfile skipped - already loading");
      return;
    }
    loading.value = true;
    error.value = "";
    console.log("[ProfileStore] loadBasicProfile started");

    try {
      const [profileRes, radarRes] = await Promise.all([
        learningApi.getProfile().catch(e => {
          console.log("[ProfileStore] getProfile error:", e?.response?.status, e?.message);
          if (e?.response?.status === 403) return { code: 403, data: null };
          throw e;
        }),
        learningApi.getRadarData().catch(e => {
          console.log("[ProfileStore] getRadarData error:", e?.response?.status, e?.message);
          if (e?.response?.status === 403) return { code: 403, data: null };
          throw e;
        }),
      ]);

      console.log("[ProfileStore] profileRes:", profileRes?.code, "radarRes:", radarRes?.code);

      if (profileRes.code === 200) {
        basicProfile.value = profileRes.data;
        console.log("[ProfileStore] basicProfile loaded:", Object.keys(profileRes.data || {}));
      } else if (profileRes.code === 403) {
        basicProfile.value = {
          learningStyle: "VISUAL",
          gradeLevel: "BEGINNER",
          strengths: "",
          weaknesses: "",
          interests: ""
        };
        console.log("[ProfileStore] Using default basicProfile (403)");
      }

      if (radarRes.code === 200) {
        radarData.value = radarRes.data;
        console.log("[ProfileStore] radarData loaded, dimensions:", Object.keys(radarRes.data?.dimensions || {}));
      } else if (radarRes.code === 403 && !radarData.value) {
        radarData.value = {
          dimensions: {
            "理论知识": 50, "实践能力": 50, "问题解决": 50,
            "创新思维": 50, "协作能力": 50
          },
          source: "default"
        };
        console.log("[ProfileStore] Using default radarData (403)");
      }

      lastUpdated.value = new Date().toISOString();
      profileVersion.value++;
      console.log("[ProfileStore] loadBasicProfile complete, version:", profileVersion.value);
    } catch (e) {
      console.error("[ProfileStore] loadBasicProfile failed:", e?.message || e);
      if (!basicProfile.value) {
        basicProfile.value = {
          learningStyle: "VISUAL",
          gradeLevel: "BEGINNER",
          strengths: "",
          weaknesses: "",
          interests: ""
        };
      }
      if (!radarData.value) {
        radarData.value = {
          dimensions: {
            "理论知识": 50, "实践能力": 50, "问题解决": 50,
            "创新思维": 50, "协作能力": 50
          },
          source: "default"
        };
      }
      error.value = e?.response?.data?.message || "加载画像失败";
    } finally {
      loading.value = false;
    }
  }

  async function loadSessionSignals(sessionId) {
    if (!sessionId) {
      sessionSignals.value = null;
      return;
    }
    console.log("[ProfileStore] loadSessionSignals for session:", sessionId);
    try {
      const r = await chatApi.getSignals(sessionId);
      console.log("[ProfileStore] signals response:", r?.code, r?.data ? "has data" : "no data");
      if (r.code === 200 && r.data?.signals) {
        sessionSignals.value = r.data.signals;
        console.log("[ProfileStore] sessionSignals loaded, exchange_count:", r.data.signals.exchange_count);
      } else {
        sessionSignals.value = {
          active_topics: [],
          topic_history: [],
          difficulty_distribution: { beginner: 0, neutral: 0, advanced: 0 },
          question_count: 0,
          gap_keywords: [],
          question_type_dist: {},
          exchange_count: 0
        };
        console.log("[ProfileStore] Using default empty sessionSignals");
      }
    } catch (e) {
      console.error("[ProfileStore] loadSessionSignals failed:", e?.message);
      sessionSignals.value = {
        active_topics: [],
        topic_history: [],
        difficulty_distribution: { beginner: 0, neutral: 0, advanced: 0 },
        question_count: 0,
        gap_keywords: [],
        question_type_dist: {},
        exchange_count: 0
      };
    }
  }

  async function refreshProfile(userId, chatHistory = null, courseTitle = "", courseDescription = "") {
    if (refreshing.value) return;
    refreshing.value = true;
    error.value = "";
    try {
      const token = localStorage.getItem("accessToken");
      if (chatHistory && chatHistory.length > 0) {
        const courseRes = await axios.post(
          "/agent/agent/profile/course",
          {
            user_id: String(userId),
            basic_profile: basicProfile.value || {},
            chat_history: chatHistory.slice(-20),
            study_records: [],
            course_title: courseTitle || "",
            course_description: courseDescription || "",
          },
          {
            headers: token ? { Authorization: "Bearer " + token } : {},
            timeout: 60000,
          }
        );
        if (courseRes.data) {
          courseProfile.value = courseRes.data;
          console.log("[ProfileStore] courseProfile loaded:", Object.keys(courseRes.data));
        }
      }
      await loadBasicProfile(true);
    } catch (e) {
      error.value = e?.response?.data?.detail || e?.message || "刷新画像失败";
    } finally {
      refreshing.value = false;
    }
  }

  function clearProfile() {
    basicProfile.value = null;
    radarData.value = null;
    courseProfile.value = null;
    sessionSignals.value = null;
    error.value = "";
    lastUpdated.value = null;
    profileVersion.value = 0;
  }

  return {
    basicProfile,
    radarData,
    courseProfile,
    sessionSignals,
    loading,
    refreshing,
    error,
    lastUpdated,
    profileVersion,
    panelCollapsed,
    hasProfile,
    liveDimensions,
    displayProfile,
    loadBasicProfile,
    loadSessionSignals,
    refreshProfile,
    clearProfile,
  };
});