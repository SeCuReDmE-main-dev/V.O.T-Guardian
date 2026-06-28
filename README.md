# V.O.T. Guardian

> **Development status.** This school tool is currently tagged **pre-alpha / in development**. External PRs are not evaluated for merge until the maintained tool reaches a stable, fully functional 100% classroom release after the pre-alpha phase. Issues and forks remain allowed, but official PR review is paused until that stability gate is met.


V.O.T. Guardian is a supervised cybersecurity education and fraud-awareness
project for teaching how voice-risk review systems should be designed with
privacy, consent, evidence boundaries, and human review.

> **Official school governance.** V.O.T. Guardian is for supervised cybersecurity
> training and public-interest fraud-awareness education. It is not an attack,
> impersonation, surveillance-abuse, or criminal automation tool. The maintained
> classroom route supports Codex/OpenAI or Antigravity/Gemini only. See
> [SCHOOL_TOOL_GOVERNANCE.md](SCHOOL_TOOL_GOVERNANCE.md) and
> [AGENTS.md](AGENTS.md).

> **License.** This project uses the Secured Educational Cybersecurity License
> 2.0 (`LicenseRef-SECL-2.0`). See [LICENSE](LICENSE), [NOTICE](NOTICE), and
> [DISCLAIMER](DISCLAIMER).

## What This Project Is

- A classroom and research scaffold for defensive voice-fraud awareness.
- A training surface for teenagers, young adults, teachers, and students.
- A human-review support model for discussing signal quality, consent,
  uncertainty, and evidence handling.
- A place to learn how cybersecurity tools should avoid overclaiming,
  autonomous accusations, and unsafe surveillance.

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


