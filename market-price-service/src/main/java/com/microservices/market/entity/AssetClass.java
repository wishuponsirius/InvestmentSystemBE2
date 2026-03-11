package com.microservices.market.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "asset_class")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AssetClass {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "asset_id")
    private Integer assetId;

    @Column(nullable = false)
    private String name;

    @Column(name = "is_active")
    private Boolean isActive;
}
