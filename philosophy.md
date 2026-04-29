# Philosophy

This document records the principles behind the design of this repository.
It is a personal CV, not a product or publication — the scope is intentionally narrow.

## Editorial

**Data minimization.** Only professional information necessary for networking is included.
No personal data beyond what a standard CV contains.

**Single source of truth.** Career data lives in YAML, versioned through Git.
Every format — PDF, HTML, Markdown — derives from the same source.
There is no "primary" document maintained separately.

**No proprietary lock-in.** The entire stack is open-source and self-hostable.
Content is portable by design: plain text files, standard formats, no platform dependency.

## Engineering

**Proportionality.** Tooling is chosen to match the actual problem, not anticipated complexity.
One page, one HTML file, one dataset — no build pipeline heavier than the output warrants.

**No SaaS where unnecessary.** Static generation, local rendering, GitHub Pages.
No external services that would require accounts, tokens, or ongoing maintenance for a document.

## Privacy

**Secrets outside the repository.** Sensitive contact fields (phone, email, address) are stored
in a local file excluded from version control via `.gitignore`.
They are injected at render time and never appear in Git history.

**No encrypted secrets in version control.** Keeping encrypted personal data in a repository
creates a permanent history record. A local plaintext file provides proportionate protection
for a minimal set of three contact identifiers, without the operational complexity of key management.
