package com.microservices.iam.config;

import com.microservices.iam.entity.InstitutionalUser;
import com.microservices.iam.entity.Role;
import com.microservices.iam.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {

        if (userRepository.count() > 0) {
            return; // DB already has users → skip seeding
        }

        seedUsers();
    }

    private void seedUsers() {

        InstitutionalUser admin = new InstitutionalUser();
        admin.setOrgName("Investment System Admin");
        admin.setContactEmail("admin@investmentsystem.com");
        admin.setPassword(passwordEncoder.encode("Admin@123"));
        admin.setIsActive(true);
        admin.setRole(Role.ADMIN);

        InstitutionalUser demo = new InstitutionalUser();
        demo.setOrgName("Demo Institution");
        demo.setContactEmail("demo@institution.com");
        demo.setPassword(passwordEncoder.encode("Demo@123"));
        demo.setIsActive(true);
        demo.setRole(Role.INSTITUTION);

        userRepository.save(admin);
        userRepository.save(demo);
    }
}
