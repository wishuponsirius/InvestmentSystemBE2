package com.microservices.market.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "market_price_raw")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MarketPriceRaw {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "price_id")
    private Integer priceId;

    @ManyToOne
    @JoinColumn(name = "asset_id", nullable = false)
    private AssetClass asset;

    @ManyToOne
    @JoinColumn(name = "source_id", nullable = false)
    private DataSource source;

    @ManyToOne
    @JoinColumn(name = "region_id", nullable = false)
    private Region region;

    @ManyToOne
    @JoinColumn(name = "unit_id", nullable = false)
    private Unit unit;

    @ManyToOne
    @JoinColumn(name = "currency_code", nullable = false)
    private Currency currency;

    @Column(name = "buy_price", precision = 20, scale = 6)
    private BigDecimal buyPrice;

    @Column(name = "sell_price", precision = 20, scale = 6)
    private BigDecimal sellPrice;

    @Column(name = "transfer_price", precision = 20, scale = 6)
    private BigDecimal transferPrice;

    @Column(name = "timestamp")
    private LocalDateTime timestamp;

    @Column(name = "spread", insertable = false, updatable = false, precision = 20, scale = 6)
    private BigDecimal spread;
}
