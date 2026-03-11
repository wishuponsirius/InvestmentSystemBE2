package com.microservices.market.repository;

import com.microservices.market.entity.ExchangeRate;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDateTime;
import java.util.List;

public interface ExchangeRateRepository extends JpaRepository<ExchangeRate, Integer> {

    @Query("""
        SELECT e
        FROM ExchangeRate e
        WHERE e.currency.currencyCode = :currency
        AND e.timestamp >= :from
        ORDER BY e.timestamp ASC
    """)
    List<ExchangeRate> findRates(String currency, LocalDateTime from);

    @Query("""
        SELECT e
        FROM ExchangeRate e
        WHERE e.currency.currencyCode = :currency
        ORDER BY e.timestamp ASC
    """)
    List<ExchangeRate> findAllRates(String currency);
}