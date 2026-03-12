package com.microservices.iam.controller;

import com.microservices.iam.dto.request.ChangePasswordRequest;
import com.microservices.iam.dto.request.UpdateAccountRequest;
import com.microservices.iam.dto.response.ApiResponse;
import com.microservices.iam.dto.response.UserResponse;
import com.microservices.iam.service.AccountService;
import com.microservices.iam.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/me")
@RequiredArgsConstructor
@Tag(name = "Account", description = "Operations for the currently authenticated user")
public class AccountController {

    private final AuthService authService;
    private final AccountService accountService;

    @GetMapping
    @Operation(summary = "Get current user account information")
    public ResponseEntity<ApiResponse<UserResponse>> getAccount(
            @Parameter(hidden = true)
            @RequestHeader("X-User-Email") String email) {

        UserResponse response = accountService.getAccount(email);
        return ResponseEntity.ok(ApiResponse.success("Account retrieved", response));
    }

    @PatchMapping
    @Operation(summary = "Update current user account information")
    public ResponseEntity<ApiResponse<UserResponse>> updateAccount(
            @Parameter(hidden = true)
            @RequestHeader("X-User-Email") String email,
            @Valid @RequestBody UpdateAccountRequest request) {

        UserResponse response = accountService.updateAccount(email, request);
        return ResponseEntity.ok(ApiResponse.success("Account updated", response));
    }

    @PatchMapping("/password")
    @Operation(
            summary = "Change password",
            description = "Allows the currently authenticated user to change their password"
    )
    public ResponseEntity<ApiResponse<Void>> changePassword(
            @Parameter(hidden = true)
            @RequestHeader("X-User-Email") String email,
            @Valid @RequestBody ChangePasswordRequest request) {

        authService.changePassword(email, request);

        return ResponseEntity.ok(
                ApiResponse.success("Password changed successfully")
        );
    }

    @PatchMapping(value = "/avatar", consumes = "multipart/form-data")
    @Operation(summary = "Upload & update avatar for current user")
    public ResponseEntity<ApiResponse<UserResponse>> updateAvatar(
            @Parameter(hidden = true)
            @RequestHeader("X-User-Email") String email,
            @RequestPart("file") MultipartFile file) {

        UserResponse response = accountService.updateAvatar(email, file);
        return ResponseEntity.ok(ApiResponse.success("Avatar updated", response));
    }

}