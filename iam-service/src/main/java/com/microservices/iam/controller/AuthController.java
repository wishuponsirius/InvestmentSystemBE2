package com.microservices.iam.controller;

import com.microservices.iam.dto.request.ChangePasswordRequest;
import com.microservices.iam.dto.request.LoginRequest;
import com.microservices.iam.dto.request.RefreshTokenRequest;
import com.microservices.iam.dto.request.RegisterRequest;
import com.microservices.iam.dto.response.ApiResponse;
import com.microservices.iam.dto.response.AuthResponse;
import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirements;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.nio.file.attribute.UserPrincipal;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "Register, activate, login and refresh tokens")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    @Operation(summary = "Register a new institutional user",
               description = "Creates an inactive account and sends an activation email")
    @SecurityRequirements  // no JWT needed for this endpoint
    public ResponseEntity<ApiResponse<Void>> register(
            @Valid @RequestBody RegisterRequest request) {
        authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(
                        "Registration successful. Please check your email to activate your account."));
    }

    @GetMapping("/activate")
    @Operation(summary = "Activate account via email token",
               description = "Validates the activation token sent by email and activates the account")
    @SecurityRequirements
    public ResponseEntity<ApiResponse<Void>> activate(@RequestParam String token) {
        authService.activateAccount(token);
        return ResponseEntity.ok(ApiResponse.success("Account activated successfully. You can now log in."));
    }

    @PostMapping("/login")
    @Operation(summary = "Login and receive JWT tokens",
               description = "Returns an access token (1hr) and refresh token (30 days)")
    @SecurityRequirements
    public ResponseEntity<ApiResponse<AuthResponse>> login(
            @Valid @RequestBody LoginRequest request) {
        AuthResponse response = authService.login(request);
        return ResponseEntity.ok(ApiResponse.success("Login successful", response));
    }

    @PostMapping("/refresh")
    @Operation(summary = "Refresh access token",
               description = "Exchange a valid refresh token for a new access token")
    @SecurityRequirements
    public ResponseEntity<ApiResponse<AuthResponse>> refresh(
            @Valid @RequestBody RefreshTokenRequest request) {
        AuthResponse response = authService.refresh(request);
        return ResponseEntity.ok(ApiResponse.success("Token refreshed", response));
    }

}
