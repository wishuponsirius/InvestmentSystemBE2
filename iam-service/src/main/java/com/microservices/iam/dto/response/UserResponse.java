package com.microservices.iam.dto.response;

import com.microservices.iam.entity.Role;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserResponse {

    private UUID id;
    private String orgName;
    private String contactEmail;
    private String avatarUrl;
    private Role role;
    private Boolean isActive;
    private Boolean isDelete;
    private LocalDateTime createDate;
}
