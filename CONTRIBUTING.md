# Contributing to FinGuard AI

First off, thank you for considering contributing to FinGuard AI! It's people like you that make FinGuard AI such a robust open-source security tool.

## Code of Conduct
By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive.
- Keep criticisms constructive.
- Prioritize technical excellence and security.

## Development Workflow
1. **Fork the repository** to your GitHub account.
2. **Clone the repository** locally.
3. **Set up the environment** using Docker `make dev` or manually.
4. **Create a new branch** specifically for your feature or bug fix (`git checkout -b feature/your-feature-name`).
5. **Make your changes**.
6. **Run tests and linting** using `make test` and `make lint`. Ensure everything passes.
7. **Commit your changes**.

## Commit Message Conventions
We follow conventional commits:
- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Changes that do not affect the meaning of the code
- `refactor:` A code change that neither fixes a bug nor adds a feature
- `perf:` A code change that improves performance
- `test:` Adding missing tests
- `chore:` Changes to the build process or auxiliary tools

Example: `feat: add robust rate-limiting to auth routes`

## Pull Request Process
1. Ensure your PR description clearly describes the problem and solution.
2. Link any related issues.
3. Ensure ALL tests are passing on your branch locally.
4. Update testing and documentation directories if applicable.
5. Submit the PR for review from core maintainers.
