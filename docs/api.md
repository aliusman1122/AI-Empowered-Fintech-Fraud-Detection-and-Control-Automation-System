# API Integration Documentation

FinGuard AI presents a rigorous RESTful backend exposed interactively via Swagger UI `/docs`.

## Authentication 
We enforce standard `OAuth2` with `PasswordFlow`.
- **Token Format:** JWT (RS256/HS256 specified) with 30-minute access expirations.
- **Header:** Include `Authorization: Bearer <TOKEN>` in all restricted requests.

## Rate Limiting
Globally handled by `SlowAPI`:
- **Auth Routes**: `5/min` avoiding brute force dict attacks.
- **Transaction Routes**: `60/min` strictly aligned to standard banking speeds.
- **Global Constraints**: Drops connections beyond `300/min` natively catching DOS requests.

*Exceeding rates invokes `HTTP 429 Too Many Requests` containing explicit retry-after headers.*

## Webhooks
We use **n8n** for orchestrating complex verification structures. 
- Payload drops upon `fraud_flag` catching a positive matrix.
- Verification hooks send immediate SMTP emails passing unique temporary hashes allowing 1-click customer validation.
