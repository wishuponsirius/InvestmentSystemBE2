package com.microservices.gateway;

import org.springdoc.core.properties.AbstractSwaggerUiConfigProperties;
import org.springdoc.core.properties.SwaggerUiConfigProperties;
import org.springframework.cloud.gateway.route.RouteDefinitionLocator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;

import java.util.HashSet;
import java.util.Set;

@Configuration
public class SwaggerAggregatorConfig {

    /**
     * Dynamically builds Swagger UI URLs from all registered Gateway routes.
     * Each service exposes /v3/api-docs, and the gateway forwards them here.
     * Access the aggregated UI at: http://localhost:8080/swagger-ui.html
     */
    @Bean
    @Lazy(false)
    public Set<AbstractSwaggerUiConfigProperties.SwaggerUrl> swaggerUrls(
            RouteDefinitionLocator locator,
            SwaggerUiConfigProperties swaggerUiConfigProperties) {

        Set<AbstractSwaggerUiConfigProperties.SwaggerUrl> urls = new HashSet<>();

        locator.getRouteDefinitions()
                .filter(route -> route.getId() != null && !route.getId().startsWith("ReactiveCompositeDiscoveryClient"))
                .subscribe(route -> {
                    String serviceId = route.getId();
                    AbstractSwaggerUiConfigProperties.SwaggerUrl swaggerUrl =
                            new AbstractSwaggerUiConfigProperties.SwaggerUrl(
                                    serviceId,
                                    "/v3/api-docs/" + serviceId,
                                    serviceId
                            );
                    urls.add(swaggerUrl);
                });

        swaggerUiConfigProperties.setUrls(urls);
        return urls;
    }
}
