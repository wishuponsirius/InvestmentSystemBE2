package com.microservices.market.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "currencies")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Currency {

    @Id
    @Column(name = "currency_code", length = 10)
    private String currencyCode;

    @Column(name = "is_active")
    private Boolean isActive;
}
