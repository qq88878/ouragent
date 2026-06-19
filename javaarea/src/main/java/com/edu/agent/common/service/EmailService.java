package com.edu.agent.common.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class EmailService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(EmailService.class);

    private final JavaMailSender mailSender;
    private final String from;

    /** In-memory verification code store: email -> {code, expireTime} */
    private final Map<String, CodeEntry> codeStore = new ConcurrentHashMap<>();

    public EmailService(
            JavaMailSender mailSender,
            @Value("${spring.mail.username:}") String from) {
        this.mailSender = mailSender;
        this.from = from;
    }

    public boolean isConfigured() {
        return from != null && !from.isBlank();
    }

    public void storeCode(String email, String code) {
        codeStore.put(email, new CodeEntry(code, Instant.now().plusSeconds(300)));
        log.debug("Code stored for {}: {}", email, code);
    }

    public String getCode(String email) {
        CodeEntry entry = codeStore.get(email);
        if (entry == null) return null;
        if (Instant.now().isAfter(entry.expireTime)) {
            codeStore.remove(email);
            return null;
        }
        return entry.code;
    }

    public void removeCode(String email) {
        codeStore.remove(email);
    }

    public void sendVerificationCode(String to, String code) {
        if (!isConfigured()) {
            log.warn("Mail not configured, skipping verification email to {}. Code: {}", to, code);
            return;
        }
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(from);
            helper.setTo(to);
            helper.setSubject("OurAgent - 邮箱验证码");
            helper.setText(buildEmailContent(code), true);
            mailSender.send(message);
            log.info("Verification email sent to {}", to);
        } catch (MessagingException e) {
            log.error("Failed to send email to {}: {}", to, e.getMessage());
            throw new RuntimeException("邮件发送失败，请稍后重试", e);
        }
    }

    private String buildEmailContent(String code) {
        return """
            <div style="max-width:480px;margin:0 auto;font-family:Arial,sans-serif;">
                <h2 style="color:#409eff;">OurAgent 邮箱验证</h2>
                <p>您的验证码是：</p>
                <div style="font-size:28px;font-weight:bold;color:#333;padding:16px;background:#f0f2f5;text-align:center;letter-spacing:8px;border-radius:8px;">
                    %s
                </div>
                <p style="color:#909399;margin-top:16px;">验证码 5 分钟内有效，请勿泄露给他人。</p>
            </div>
            """.formatted(code);
    }

    private record CodeEntry(String code, Instant expireTime) {}
}