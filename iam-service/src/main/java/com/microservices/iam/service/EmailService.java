package com.microservices.iam.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailService {

    private final JavaMailSender mailSender;

    @Value("${spring.mail.username}")
    private String fromEmail;

    @Value("${app.base-url}")
    private String baseUrl;

    @Async
    public void sendActivationEmail(String toEmail, String orgName, String token) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setFrom(fromEmail);
            helper.setTo(toEmail);
            helper.setSubject("Activate your Investment System account");

            String activationUrl = baseUrl + "/auth/activate?token=" + token;
            String html = buildActivationEmail(orgName, activationUrl);

            helper.setText(html, true);
            mailSender.send(message);

            log.info("Activation email sent to {}", toEmail);
        } catch (MessagingException e) {
            log.error("Failed to send activation email to {}: {}", toEmail, e.getMessage());
        }
    }

    private String buildActivationEmail(String orgName, String activationUrl) {
        return """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Welcome to Investment System</h2>
                    <p>Hi <strong>%s</strong>,</p>
                    <p>Thank you for registering. Please activate your account by clicking the button below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="%s"
                           style="background-color: #4CAF50; color: white; padding: 14px 24px;
                                  text-decoration: none; border-radius: 4px; font-size: 16px;">
                            Activate Account
                        </a>
                    </div>
                    <p style="color: #888; font-size: 13px;">
                        This link expires in 24 hours. If you did not register, please ignore this email.
                    </p>
                    <p style="color: #888; font-size: 13px;">
                        Or copy this link: <a href="%s">%s</a>
                    </p>
                </div>
                """.formatted(orgName, activationUrl, activationUrl, activationUrl);
    }

    @Async
    public void sendAdminCreatedAccountEmail(String toEmail, String orgName, String tempPassword) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

            helper.setFrom(fromEmail);
            helper.setTo(toEmail);
            helper.setSubject("Your Investment System account has been created");

            String html = buildAdminCreatedEmail(orgName, toEmail, tempPassword);

            helper.setText(html, true);
            mailSender.send(message);

            log.info("Admin account email sent to {}", toEmail);

        } catch (MessagingException e) {
            log.error("Failed to send admin account email to {}: {}", toEmail, e.getMessage());
        }
    }

    private String buildAdminCreatedEmail(String orgName, String email, String tempPassword) {
        return """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Welcome to Investment System</h2>

            <p>Hello <strong>%s</strong>,</p>

            <p>An administrator has created an account for your organization.</p>

            <p>You can log in using the following credentials:</p>

            <p><strong>Email:</strong> %s</p>
            <p><strong>Temporary Password:</strong> %s</p>

            <p style="margin-top:20px;">
                For security reasons, please change your password after logging in.
            </p>

            <p style="color:#888;font-size:13px;">
                If you did not expect this account, please contact the system administrator.
            </p>
        </div>
        """.formatted(orgName, email, tempPassword, baseUrl);
    }
}
