# Security and private information

This is a personal, self-hosted application with one local login. It is not designed as a public internet service or as a multi-tenant client portal. Keep the Python backend on loopback and use the documented HTTPS gateway over trusted LAN/VPN routes.

Do not post vulnerabilities that expose private chart data or credentials in a public issue. If the GitHub repository has **Security → Report a vulnerability**, use that private channel. The repository owner must enable private vulnerability reporting after publishing. If it is unavailable, ask the maintainer for a private reporting channel without including exploit details or private data.

Include the version, platform, reproduction steps using fictional data, and impact. Never include live passwords, database exports, client records or CA private keys. No response-time guarantee or formal security audit is claimed. Updates are distributed as source releases; check the changelog before updating and keep a backup.

The release ZIP and Git history should contain source only. `.gitignore` reduces accidental staging but does not remove already tracked files. Review staged changes before every public push. If a secret is exposed, rotate it; deleting the latest file does not erase Git history.
