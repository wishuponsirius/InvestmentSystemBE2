package com.microservices.market.service;

import com.microservices.market.dto.response.ForexResponseDTO;
import com.microservices.market.entity.ExchangeRate;
import com.microservices.market.exception.ResourceNotFoundException;
import com.microservices.market.repository.ExchangeRateRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ForexService {

    private final ExchangeRateRepository repo;

    public List<ForexResponseDTO> getRates(String currency, String range) {

        String currencyCode = currency.toUpperCase();

        List<ExchangeRate> rates;

        if (range.equalsIgnoreCase("all")) {

            rates = repo.findAllRates(currencyCode);

        } else {

            LocalDateTime from = calculateFromTime(range);

            rates = repo.findRates(currencyCode, from);
        }

        if (rates.isEmpty()) {
            throw new ResourceNotFoundException(
                    "No exchange rates found for currency '" + currencyCode + "'"
            );
        }

        return rates.stream()
                .map(this::toDTO)
                .toList();
    }

    private ForexResponseDTO toDTO(ExchangeRate rate) {

        return ForexResponseDTO.builder()
                .currency(rate.getCurrency().getCurrencyCode())
                .buyPrice(rate.getBuyPrice())
                .transferPrice(rate.getTransferPrice())
                .sellPrice(rate.getSellPrice())
                .timestamp(rate.getTimestamp())
                .build();
    }

    private LocalDateTime calculateFromTime(String range) {

        LocalDateTime now = LocalDateTime.now();

        return switch (range.toLowerCase()) {
            case "1d" -> now.minusDays(1);
            case "1w" -> now.minusWeeks(1);
            case "1m" -> now.minusMonths(1);
            case "1y" -> now.minusYears(1);
            default -> throw new IllegalArgumentException("Invalid range. Allowed values: all, 1d, 1w, 1m, 1y");
        };
    }
}