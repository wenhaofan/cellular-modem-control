# Security Policy

## Supported Versions

Security fixes target the latest released minor version. The project is still
pre-1.0, so APIs may change while the modem abstraction stabilizes.

## Reporting Issues

Open a private security advisory in the project repository when possible. If
that is not available, contact the maintainers through the repository issue
tracker with a minimal non-sensitive description and ask for a private channel.

Do not include SIM identifiers, phone numbers, IMEI values, SMS contents, or
carrier account information in public reports.

## Safety Boundaries

This project can control hardware that may place calls or send billable SMS.
Security reports involving unintended SMS, calls, message deletion, or raw AT
command execution are in scope.
