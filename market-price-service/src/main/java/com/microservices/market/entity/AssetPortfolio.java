package com.microservices.market.entity;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "asset_portfolio")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AssetPortfolio {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "portfolio_id")
    private Integer portfolioId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @ManyToOne
    @JoinColumn(name = "asset_id", nullable = false)
    private AssetClass asset;

    @Column(nullable = false, precision = 20, scale = 10)
    private BigDecimal quantity;

    @ManyToOne
    @JoinColumn(name = "unit_id", nullable = false)
    private Unit unit;

    @Column(name = "entry_price", precision = 20, scale = 6)
    private BigDecimal entryPrice;

    @ManyToOne
    @JoinColumn(name = "currency_code")
    private Currency currency;
}
