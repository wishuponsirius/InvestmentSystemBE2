package com.microservices.iam.service;

import com.microservices.iam.dto.request.ChangePasswordRequest;
import com.microservices.iam.dto.request.LoginRequest;
import com.microservices.iam.dto.request.RefreshTokenRequest;
import com.microservices.iam.dto.request.RegisterRequest;
import com.microservices.iam.dto.response.AuthResponse;
import com.microservices.iam.dto.response.UserResponse;
import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.entity.Role;
import com.microservices.iam.exception.EmailAlreadyExistsException;
import com.microservices.iam.exception.InvalidTokenException;
import com.microservices.iam.exception.UserNotFoundException;
import com.microservices.iam.repository.UserRepository;
import com.microservices.iam.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final EmailService emailService;

    @Transactional
    public void register(RegisterRequest request) {
        if (userRepository.existsByContactEmailIgnoreCase(request.getContactEmail())) {
            throw new EmailAlreadyExistsException(request.getContactEmail());
        }

        String activationToken = UUID.randomUUID().toString();

        InstitutionalUser user = InstitutionalUser.builder()
                .orgName(request.getOrgName())
                .contactEmail(request.getContactEmail().toLowerCase())
                .password(passwordEncoder.encode(request.getPassword()))
                .avatarUrl(request.getAvatarUrl())
                .role(Role.INSTITUTION)  // default role on registration
                .isActive(false)
                .activationToken(activationToken)
                .activationTokenExpiry(LocalDateTime.now().plusHours(24))
                .build();

        userRepository.save(user);

        emailService.sendActivationEmail(
                user.getContactEmail(),
                user.getOrgName(),
                activationToken
        );

        log.info("User registered: {}", user.getContactEmail());
    }

    @Transactional
    public void activateAccount(String token) {
        InstitutionalUser user = userRepository.findByActivationToken(token)
                .orElseThrow(() -> new InvalidTokenException("Invalid activation token"));

        if (user.getIsActive()) {
            throw new InvalidTokenException("Account is already activated");
        }

        if (user.getActivationTokenExpiry().isBefore(LocalDateTime.now())) {
            throw new InvalidTokenException("Activation token has expired");
        }

        user.setIsActive(true);
        user.setActivationToken(null);
        user.setActivationTokenExpiry(null);
        userRepository.save(user);

        log.info("Account activated: {}", user.getContactEmail());
    }

    public AuthResponse login(LoginRequest request) {
        InstitutionalUser user = userRepository
                .findByContactEmailIgnoreCase(request.getContactEmail())
                .orElseThrow(() -> new BadCredentialsException("Invalid email or password"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BadCredentialsException("Invalid email or password");
        }

        if (Boolean.TRUE.equals(user.getIsDelete())) {
            throw new BadCredentialsException("Account has been deactivated");
        }

        if (!user.getIsActive()) {
            throw new BadCredentialsException("Account is not activated. Please check your email");
        }

        String accessToken = jwtUtil.generateAccessToken(
                user.getId(),
                user.getContactEmail(),
                user.getRole().name()
        );
        String refreshToken = jwtUtil.generateRefreshToken(user.getId());

        log.info("User logged in: {}", user.getContactEmail());

        return AuthResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .tokenType("Bearer")
                .expiresIn(jwtUtil.getAccessTokenExpiryMs() / 1000)
                .user(mapToUserResponse(user))
                .build();
    }

    public AuthResponse refresh(RefreshTokenRequest request) {
        String refreshToken = request.getRefreshToken();

        if (!jwtUtil.isTokenValid(refreshToken) || !jwtUtil.isRefreshToken(refreshToken)) {
            throw new InvalidTokenException("Invalid or expired refresh token");
        }

        UUID userId = UUID.fromString(jwtUtil.extractUserId(refreshToken));
        InstitutionalUser user = userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException("User not found"));

        if (!user.getIsActive() || user.getIsDelete()) {
            throw new InvalidTokenException("Account is no longer active");
        }

        String newAccessToken = jwtUtil.generateAccessToken(
                user.getId(),
                user.getContactEmail(),
                user.getRole().name()
        );

        return AuthResponse.builder()
                .accessToken(newAccessToken)
                .refreshToken(refreshToken)  // reuse existing refresh token
                .tokenType("Bearer")
                .expiresIn(jwtUtil.getAccessTokenExpiryMs() / 1000)
                .user(mapToUserResponse(user))
                .build();
    }

    private UserResponse mapToUserResponse(InstitutionalUser user) {
        return UserResponse.builder()
                .id(user.getId())
                .orgName(user.getOrgName())
                .contactEmail(user.getContactEmail())
                .avatarUrl(user.getAvatarUrl())
                .role(user.getRole())
                .isActive(user.getIsActive())
                .isDelete(user.getIsDelete())
                .createDate(user.getCreateDate())
                .build();
    }

    @Transactional
    public void changePassword(String email, ChangePasswordRequest request) {

        InstitutionalUser user = userRepository
                .findByContactEmailIgnoreCase(email)
                .orElseThrow(() -> new UserNotFoundException(email));

        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPassword())) {
            throw new BadCredentialsException("Current password is incorrect");
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));

        userRepository.save(user);
    }
}
