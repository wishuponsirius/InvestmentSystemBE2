package com.microservices.iam.controller;

import com.microservices.iam.dto.request.AdminCreateUserRequest;
import com.microservices.iam.dto.request.UpdateUserRequest;
import com.microservices.iam.dto.response.ApiResponse;
import com.microservices.iam.dto.response.PageResponse;
import com.microservices.iam.dto.response.UserResponse;
import com.microservices.iam.entity.Role;
import com.microservices.iam.service.AdminService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/admin/users")
@RequiredArgsConstructor
@Tag(name = "Admin — User Management", description = "ADMIN role required for all endpoints")
public class AdminController {

    private final AdminService adminService;

    @GetMapping
    @Operation(summary = "List all users",
               description = "Supports pagination, search by name/email, filter by role and status")
    public ResponseEntity<ApiResponse<PageResponse<UserResponse>>> getUsers(
            @RequestParam(required = false) String search,
            @RequestParam(required = false) Role role,
            @RequestParam(required = false) Boolean isActive,
            @RequestParam(required = false) Boolean isDelete,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "createDate") String sortBy,
            @RequestParam(defaultValue = "desc") String sortDir) {

        PageResponse<UserResponse> result = adminService.getUsers(
                search, role, isActive, isDelete, page, size, sortBy, sortDir);
        return ResponseEntity.ok(ApiResponse.success("Users retrieved", result));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID")
    public ResponseEntity<ApiResponse<UserResponse>> getUserById(@PathVariable UUID id) {
        UserResponse user = adminService.getUserById(id);
        return ResponseEntity.ok(ApiResponse.success("User retrieved", user));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update user",
               description = "Update org name, email, role, or active status. Only provided fields are updated.")
    public ResponseEntity<ApiResponse<UserResponse>> updateUser(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateUserRequest request) {
        UserResponse updated = adminService.updateUser(id, request);
        return ResponseEntity.ok(ApiResponse.success("User updated", updated));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Soft delete user",
               description = "Marks user as deleted and deactivates the account. Reversible via update.")
    public ResponseEntity<ApiResponse<Void>> deleteUser(@PathVariable UUID id) {
        adminService.deleteUser(id);
        return ResponseEntity.ok(ApiResponse.success("User deleted"));
    }

    @PostMapping
    @Operation(summary = "Create new user",
            description = "Admin creates a new user account and sends temporary login credentials via email.")
    public ResponseEntity<ApiResponse<UserResponse>> createUser(
            @Valid @RequestBody AdminCreateUserRequest request) {

        UserResponse createdUser = adminService.createUserByAdmin(request);

        return ResponseEntity.ok(ApiResponse.success("User created", createdUser));
    }
}
