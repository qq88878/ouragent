import { defineStore } from "pinia";
import { ref, reactive } from "vue";
import { ElNotification } from "element-plus";

export const useChatStore = defineStore("chat", () => {
  // Track which session is currently streaming
  const activeStreams = reactive({});

  // Whether the ChatView component is currently mounted/visible
  const isChatPageActive = ref(true);

  function setChatPageActive(active) {
    isChatPageActive.value = active;
  }

  /**
   * Start a streaming response for a session.
   * Returns immediately; the stream runs in background.
   */
  function startStream(sessionId, message) {
    // Abort any existing stream for this session
    if (activeStreams[sessionId]?.controller) {
      activeStreams[sessionId].controller.abort();
    }

    const token = localStorage.getItem("accessToken");
    const controller = new AbortController();

    const stream = {
      content: "",
      done: false,
      error: "",
      controller,
    };
    activeStreams[sessionId] = stream;

    // Run the fetch in background — do NOT await here
    (async () => {
      try {
        const response = await fetch(
          `/api/chat/sessions/${sessionId}/messages/stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ message }),
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          stream.error = `HTTP ${response.status}`;
          stream.done = true;
          notifyIfAway(sessionId, stream);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();

          for (const line of lines) {
            if (line.startsWith("data:")) {
              const data = line
                .slice(line.charAt(5) === " " ? 6 : 5)
                .trim();
              if (data) {
                try {
                  const parsed = JSON.parse(data);
                  if (parsed.type === 'end' || parsed.done) {
                    stream.done = true;
                  } else if (parsed.type === 'error' || parsed.error) {
                    stream.error = parsed.error || 'AI服务错误';
                  } else if (parsed.content !== undefined) {
                    stream.content += parsed.content || '';
                  }
                } catch {
                  /* skip malformed */
                }
              }
            }
          }
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          stream.error = stream.content
            ? ""
            : "网络错误，请稍后重试";
        }
      } finally {
        stream.done = true;
        stream.controller = null;
        notifyIfAway(sessionId, stream);
      }
    })();

    return stream;
  }

  function notifyIfAway(sessionId, stream) {
    if (!isChatPageActive.value && stream.content) {
      ElNotification({
        title: "智能助手回复完成",
        message:
          stream.content.slice(0, 80) +
          (stream.content.length > 80 ? "..." : ""),
        type: "success",
        duration: 5000,
        onClick: () => {
          window.location.hash = `#/chat/${sessionId}`;
        },
      });
    }
  }

  function getStream(sessionId) {
    return activeStreams[sessionId] || null;
  }

  function cleanup(sessionId) {
    if (activeStreams[sessionId]?.controller) {
      activeStreams[sessionId].controller.abort();
    }
    delete activeStreams[sessionId];
  }

  return {
    activeStreams,
    isChatPageActive,
    setChatPageActive,
    startStream,
    getStream,
    cleanup,
  };
});
