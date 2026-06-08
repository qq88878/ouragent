package com.edu.agent.security;

import com.edu.agent.module.user.entity.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;

@Component
public class JwtProvider {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.access-token-expiration}")
    private long accessTokenExpiration;

    @Value("${jwt.refresh-token-expiration}")
    private long refreshTokenExpiration;

    private SecretKey getKey() {
        // Generates a secure key from the secret string
        return Keys.hmacShaKeyFor(secret.getBytes());
    }

    public String generateAccessToken(User user) {
        return generateToken(user.getUsername(), accessTokenExpiration);
    }

    public String generateRefreshToken(User user) {
        return generateToken(user.getUsername(), refreshTokenExpiration);
    }

    private String generateToken(String subject, long expirationSeconds) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expirationSeconds * 1000);

        return Jwts.builder()
                .subject(subject)
                .issuedAt(now)
                .expiration(expiryDate)
                .signWith(getKey())
                .compact();
    }

    public Claims getClaimsFromToken(String token) {
        // Use the modern, fluent API for parsing and verification
        return Jwts.parser()
                .verifyWith(getKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public String getUsernameFromToken(String token) {
        return getClaimsFromToken(token).getSubject();
    }

    public boolean isTokenExpired(String token) {
        try {
            return getClaimsFromToken(token).getExpiration().before(new Date());
        } catch (Exception e) {
            // An expired token will throw an exception upon parsing, so we treat any parsing error as an expired/invalid token.
            return true;
        }
    }

    public boolean validateToken(String token, User user) {
        final String username = getUsernameFromToken(token);
        return (username.equals(user.getUsername()) && !isTokenExpired(token));
    }
}