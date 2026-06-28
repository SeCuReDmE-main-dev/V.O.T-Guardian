# School Tool Governance Standard

This repository is part of the SecuredMe open-source school-tool suite.

Official classroom use is maintained for students, teachers, schools, and supervised young-adult learning. The supported AI-assisted routes are Codex/OpenAI and Antigravity/Gemini only. Ollama Cloud, generic uncensored local AI, and unknown agent routes are not supported as official classroom providers.

This repository uses the Secured Educational Cybersecurity License 2.0 (SECL-2.0) for supervised defensive cybersecurity and fraud-awareness education.

Cybersecurity and voice-fraud features are training tools for supervised learning and public-interest awareness. They must not be used for attack, impersonation, surveillance misuse, fraud, bypass, abuse, or criminal automation.

Users may fork the code under the repository license, but the maintainer only supports the reviewed official version.
## Development Stability Gate
This repository is tagged `pre-alpha` and `in-development`. External PRs are not evaluated for merge before the official school tool is stable and fully functional for classroom use. Until that gate is met, outside contributors should open issues or build local forks/plugins; maintainers may still push internal stabilization commits.
## School Authentication And Secret Boundary
This repository is a small SecuredMe school tool. Official classroom use must not require `.env` files, API keys, raw tokens, or local model secrets. Student and teacher workflows must use Codex/OpenAI or Antigravity/Gemini through browser WebAuth, fingerprinted session approval, and encrypted local session records when authentication is needed.

The reason for excluding generic local AI routes from official school mode is student and teacher safety: education accounts, provider-side account controls, browser login, and governed AI refusal behavior are safer than unguided local model endpoints for classroom cybersecurity and algorithm-building tools.


