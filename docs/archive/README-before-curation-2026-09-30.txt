# V.O.T. Guardian

<!-- SECUREDME-REPOSITORY-IMAGE:START -->
![V.O.T. Guardian — SecuredMe Education pre-alpha](docs/assets/repository/readme-banner-2026.png)

[Repository social preview](docs/assets/repository/github-social-preview-2026.jpg) · [Presentation history](docs/repository-presentation-history-2026-09-30.md)
<!-- SECUREDME-REPOSITORY-IMAGE:END -->

<!-- SECUREDME-ZENODO:START -->
<p align="center">
  <a href="https://doi.org/10.5281/zenodo.21893197"><img alt="Zenodo DOI: 10.5281/zenodo.21893197" src="https://img.shields.io/badge/Zenodo%20DOI-10.5281%2Fzenodo.21893197-1682D4?style=for-the-badge" /></a>
</p>
<!-- SECUREDME-ZENODO:END -->

<!-- SECUREDME-CPAI-MESH:START -->
[![CodeProject.AI local connector](https://img.shields.io/badge/CodeProject.AI-local%20connector-1F6FEB)](infra/codeproject-ai/README.md)

Local runtime availability must be checked; historical inference reports do not establish current readiness.
<!-- SECUREDME-CPAI-MESH:END -->

[Embedded CodeProject.AI node operations](infra/codeproject-ai/README.md)

[![SecuredMe Education Suite public calendar](https://img.shields.io/badge/SecuredMe%20Education%20Suite-public%20calendar%20%7C%20pre--alpha%20%7C%20active%20public%20development-5484ED?style=for-the-badge&logo=googlecalendar&logoColor=white)](https://calendrier.securedme.ca)

**Attribution:** Jean-Sebastien Beaulieu · [ORCID 0009-0007-2904-0443](https://orcid.org/0009-0007-2904-0443) · [SecuredMe](https://securedme.ca) · [V.O.T Guardian](https://vot-guardian.securedme.ca)

<!-- SECUREDME-SUITE-BADGES:START -->
[![License SECL-2.0](https://img.shields.io/badge/license-SECL--2.0-6F42FF)](LICENSE)
[![Pre-alpha](https://img.shields.io/badge/status-pre--alpha-0E7490)](AGENTS.md)
[![Issues](https://img.shields.io/github/issues/SeCuReDmE-main-dev/V.O.T-Guardian)](https://github.com/SeCuReDmE-main-dev/V.O.T-Guardian/issues)
[![Main history](https://img.shields.io/github/last-commit/SeCuReDmE-main-dev/V.O.T-Guardian/main)](https://github.com/SeCuReDmE-main-dev/V.O.T-Guardian/commits/main/)
<!-- SECUREDME-SUITE-BADGES:END -->

<!-- SECUREDME-STARTUP-SUPPORT:START -->
[![SPONSORED BY E2B FOR STARTUPS](https://img.shields.io/badge/SPONSORED%20BY-E2B%20FOR%20STARTUPS-ff3001?style=for-the-badge&labelColor=black)](https://e2b.dev/startups)

E2B supports SecuredMe through E2B for Startups. Sponsorship recognition is separate from runtime availability and included quotas.
<!-- SECUREDME-STARTUP-SUPPORT:END -->

> **Maintainer review.** This pre-alpha repository accepts reproducible issues and reviewed maintenance changes. Protected-branch reviews and human authorization remain required; an issue does not promise a response or delivery date.




## School Authentication And Secret Boundary
This repository is a small SecuredMe school tool. Official classroom use must not require `.env` files, API keys, raw tokens, or local model secrets. Student and teacher workflows must use Codex/OpenAI or Antigravity/Gemini through browser WebAuth, fingerprinted session approval, and encrypted local session records when authentication is needed.

Both host adapters implement the shared `securedme.education.webauth-template.v1` policy and are auditable through the Gateway. That proves policy compatibility, not a deployed V.O.T. Guardian login. Provider callback, account binding, session expiry, logout, recovery, and accessible browser acceptance remain required before live-login claims.

The reason for excluding generic local AI routes from official school mode is student and teacher safety: education accounts, provider-side account controls, browser login, and governed AI refusal behavior are safer than unguided local model endpoints for classroom cybersecurity and algorithm-building tools.

> **Development status.** This school tool is currently **pre-alpha — active public development**. Public issues remain open for intake, but no response or delivery date is promised. Pull requests are paused during active development.


V.O.T. Guardian is a supervised cybersecurity education and fraud-awareness
project for teaching how voice-risk review systems should be designed with
privacy, consent, evidence boundaries, and human review.

> **Official school governance.** V.O.T. Guardian is for supervised cybersecurity
> training and public-interest fraud-awareness education. It is not an attack,
> impersonation, surveillance-abuse, or criminal automation tool. The maintained
> classroom route supports Codex/OpenAI or Antigravity/Gemini only. See
> [SCHOOL_TOOL_GOVERNANCE.md](SCHOOL_TOOL_GOVERNANCE.md) and
> [AGENTS.md](AGENTS.md).

> **License.** This project uses the Secured Educational Cybersecurity License 2.0 (SECL-2.0). It is provided for defensive education, fraud-awareness, simulation, and supervised cyber training. Offensive workflows, unsafe surveillance, credential theft, fraud, bypass, and criminal automation are not maintained or endorsed by the official school version. See [LICENSE](LICENSE), [NOTICE](NOTICE), [DISCLAIMER](DISCLAIMER), and [SAFETY.md](SAFETY.md).
> [DISCLAIMER](DISCLAIMER).

## What This Project Is

- A classroom and research scaffold for defensive voice-fraud awareness.
- A training surface for teenagers, young adults, teachers, and students.
- A human-review support model for discussing signal quality, consent,
  uncertainty, and evidence handling.
- A place to learn how cybersecurity tools should avoid overclaiming,
  autonomous accusations, and unsafe surveillance.
- A classroom planning surface for responsible public communication:
  [Educational Marketing Plan Template](docs/educational_marketing_plan_template.md).

## What This Project Is Not

- Not a production fraud detector.
- Not a biometric identification system.
- Not a diagnostic, law-enforcement, compliance, or safety authority.
- Not a system for impersonation, attack, surveillance abuse, or criminal
  automation.
- Not a guarantee of accuracy, latency, throughput, legal compliance, or
  protection.

## School-Safe Boundary

Any model output, audio analysis, confidence score, or risk label must be treated
as a review artifact. A human reviewer must inspect the evidence, context,
consent, privacy posture, and limitations before taking any action.

Preferred output language:

- `review required`
- `signal quality concern`
- `uncertain voice-risk indicator`
- `evidence gap`
- `human review needed`

Avoid accusation language such as “fraud confirmed”, “impersonator detected”, or
“attack proven”.

## Repository Notes

The `developpement/` folder contains earlier implementation and research notes.
Those notes may mention experimental architecture, performance targets, or
compliance ideas. They are not public claims, not validated benchmarks, and not
deployment promises.

## Development

Use this repository as a school-safe development exercise:

```powershell
git status --short --branch
```

Run any available project-specific tests only after reviewing the local
requirements. Do not add secrets, production credentials, real private audio, or
personal data to the repository.

## Attribution

Jean-Sebastien Beaulieu  
ORCID: https://orcid.org/0009-0007-2904-0443  
SecuredMe







