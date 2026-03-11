package com.microservices.market.service;
import com.microservices.market.entity.AssetClass;
import com.microservices.market.entity.Currency;
import com.microservices.market.exception.ResourceNotFoundException;
import com.microservices.market.repository.AssetClassRepository;
import com.microservices.market.repository.CurrencyRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CurrencyLookupService {

    private final CurrencyRepository currencyRepository;

    @Cacheable(value = "currencies", key = "#p0.toUpperCase()")
    public Currency getCurrency(String code) {

        String normalized = code.toUpperCase();

        return currencyRepository.findById(normalized)
                .orElseThrow(() ->
                        new ResourceNotFoundException("Currency " + normalized + " not found"));
    }
}