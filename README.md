# V.O.T. Guardian

<!-- SECUREDME-ZENODO:START -->
<p align="center">
  <a href="https://zenodo.org/badge/latestdoi/1082281882"><img alt="DOI" src="https://zenodo.org/badge/1082281882.svg" /></a>
</p>
<!-- SECUREDME-ZENODO:END -->

<!-- SECUREDME-CPAI-MESH:START -->
<p align="center">
  <img alt="CodeProject.AI Server embedded mesh node" src="https://img.shields.io/badge/CodeProject.AI%20Server-Embedded%20Mesh%20Node-1F6FEB?style=for-the-badge" />
  <img alt="YOLO real local inference validated" src="https://img.shields.io/badge/YOLO-Real%20Local%20Inference-16A34A?style=for-the-badge" />
</p>
<!-- SECUREDME-CPAI-MESH:END -->

[Embedded CodeProject.AI node operations](infra/codeproject-ai/README.md)

[![SecuredMe Education Suite public calendar](https://img.shields.io/badge/SecuredMe%20Education%20Suite-public%20calendar%20%7C%20pre--alpha%20%7C%20active%20public%20development-5484ED?style=for-the-badge&logo=googlecalendar&logoColor=white)](https://calendrier.securedme.ca)

**Attribution:** Jean-Sebastien Beaulieu · [ORCID 0009-0007-2904-0443](https://orcid.org/0009-0007-2904-0443) · [SecuredMe](https://securedme.ca) · [V.O.T Guardian](https://vot-guardian.securedme.ca)

<!-- SECUREDME-SUITE-BADGES:START -->
[![Issues](https://img.shields.io/github/issues/SeCuReDmE-main-dev/V.O.T-Guardian?color=111722)](https://github.com/SeCuReDmE-main-dev/V.O.T-Guardian/issues)
[![Milestones](https://img.shields.io/badge/milestones-M0--M7-D7263D)](https://github.com/SeCuReDmE-main-dev/V.O.T-Guardian/milestones)
[![Project Board](https://img.shields.io/badge/project-kanban-5484ED)](https://github.com/users/SeCuReDmE-main-dev/projects/3)
[![Branch](https://img.shields.io/badge/branch-main-0E7490)](https://github.com/SeCuReDmE-main-dev/V.O.T-Guardian/tree/main)
<!-- SECUREDME-SUITE-BADGES:END -->

<!-- SECUREDME-STARTUP-SUPPORT:START -->
<p align="center">
  <a href="https://e2b.dev/startups">
    <img alt="Gateway-ready E2B audit lane" src="https://img.shields.io/badge/Gateway--ready-E2B%20audit%20lane-FF8800?style=for-the-badge" />
  </a>
  <a href="https://www.datadoghq.com/partner/datadog-for-startups/">
    <img alt="Gateway-ready Datadog observability" src="https://img.shields.io/badge/Gateway--ready-Datadog%20observability-632CA6?style=for-the-badge&amp;logo=datadog&amp;logoColor=white" />
  </a>
</p>

> **Gateway support acknowledgement.** This SecuredMe school tool is gateway-compatible. E2B audit support and Datadog observability are routed through the shared SecuredMe gateway when that lane is configured; this repository does not claim a direct E2B or Datadog runtime dependency by default, and no E2B or Datadog secret is stored in this README.
<!-- SECUREDME-STARTUP-SUPPORT:END -->

> **Maintainer intake during active finishing week.** This repository is maintained directly on `main` by the SecuredMe maintainer. Public issues are open for bug reports, documentation corrections, security-safe observations, and reproducible feedback, but opening an issue does not promise a response or a delivery date. Pull requests are not accepted during the active code-finishing week; use issues only until this notice is replaced.




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







