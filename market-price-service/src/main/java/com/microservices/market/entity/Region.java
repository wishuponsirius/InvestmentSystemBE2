package com.microservices.market.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "regions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Region {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "region_id")
    private Integer regionId;

    @Column(name = "region_code", unique = true, nullable = false)
    private String regionCode;

    @Column(name = "region_name", nullable = false)
    private String regionName;

    @Column(name = "country_code", nullable = false)
    private String countryCode;
}
