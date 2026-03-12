package com.microservices.iam.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "institutional_user")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InstitutionalUser {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "id", updatable = false, nullable = false)
    private UUID id;

    @Column(name = "avatar_url")
    private String avatarUrl;

    @Column(name = "avatar_public_id")
    private String avatarPublicId;

    @Column(name = "org_name", nullable = false)
    private String orgName;

    @Column(name = "contact_email", nullable = false, unique = true)
    private String contactEmail;

    @Column(name = "password", nullable = false)
    private String password;

    @Column(name = "activation_token")
    private String activationToken;

    @Column(name = "activation_token_expiry")
    private LocalDateTime activationTokenExpiry;

    @Column(name = "is_active")
    @Builder.Default
    private Boolean isActive = false;

    @Enumerated(EnumType.STRING)
    @Column(name = "role")
    private Role role;

    @CreationTimestamp
    @Column(name = "create_date", updatable = false)
    private LocalDateTime createDate;

    @Column(name = "is_delete")
    @Builder.Default
    private Boolean isDelete = false;

    @UpdateTimestamp
    @Column(name = "update_date")
    private LocalDateTime updateDate;
}
