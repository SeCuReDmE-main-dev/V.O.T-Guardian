# Twilio Application Packet

This packet is the source text for a fast Twilio application or support
submission. Review it before sending any form because it contains founder and
project positioning.

## Applicant Path

- Applicant type: sole proprietor.
- Project name: V.O.T Guardian by SecuredMe.
- Stage: pre-alpha supervised education pilot.
- Requested Twilio surface: Programmable Voice with Media Streams.
- Messaging status: SMS/MMS deferred until Twilio Verify or A2P 10DLC review.

## Opportunity Snapshot

- Source message: Proton inbox email from Twilio Startups Team.
- Program: Twilio AI Startup Searchlight 2026.
- Application URL:
  `https://www.twilio.com/en-us/lp/twilio-ai-startup-searchlight`.
- Recommended track: Breakthrough Builders, because V.O.T Guardian is an
  early-stage supervised pilot and should not be positioned as a scaled,
  venture-backed production product unless that status is separately verified.
- Deadline: not visible in the captured email or application page; verify before
  final submission.
- Eligibility fit to present: emerging technology integrated with Twilio,
  working functional demo, less than 200M in venture funding.
- Required demo asset: Loom, YouTube, or Vimeo link showing one complete
  workflow.

## Application Constraints

- The application page says a Twilio account is required before applying.
- The visible form states that it has 32 questions.
- The applicant must be over 21.
- Submission grants Twilio permission to include company name and logo in sales,
  marketing, public relations, social, investor, analyst, promotional, and
  advertising activity.
- The form says it will not accept these special characters:
  `[ ' " < > { } ; ]`.
- Before pasting into the form, sanitize answers to remove those characters.
- Do not submit without final confirmation from the account owner because the
  form transmits personal and business data.

## One-Line Pitch

V.O.T Guardian is a privacy-first educational voice-risk review pilot that uses
Twilio Media Streams to teach supervised fraud-awareness workflows without
retaining raw call audio or making autonomous accusations.

## Short Pitch

V.O.T Guardian helps students, teachers, and reviewers understand how voice-risk
systems should be designed with consent, privacy, evidence gaps, and human
review. The Twilio pilot uses Programmable Voice and Media Streams to stream
short live audio windows into a supervised review pipeline. The system produces
bounded review artifacts such as `review required` and `human review needed`;
it does not claim production fraud detection, biometric identity, emergency use,
or law-enforcement authority.

## Technical Pitch

The V.O.T Guardian prototype already has a Flask API, a Vue review interface,
and a Tenebris-style audit boundary. The Twilio integration adds:

- a signature-validated inbound voice webhook;
- consent-first TwiML with a `press 1 to continue` branch;
- a `wss://` Media Streams endpoint;
- short in-memory frame handling with explicit buffer purge;
- redacted live session state for the frontend;
- audit metadata without raw audio retention.

The pilot asks Twilio to support the voice streaming layer and the compliance
review path needed to move from a local educational prototype to a safe public
demo.

## Form-Safe Answer Set

Use this copy as the starting point for form fields that reject special
characters. Recheck each field after editing.

One-line summary:

V.O.T Guardian is a privacy first educational voice risk review pilot using
Twilio Programmable Voice and Media Streams to show consent led supervised human
review workflows without storing raw call audio.

Short product answer:

V.O.T Guardian helps students teachers and reviewers learn responsible voice
risk review. A caller gives consent Twilio streams short audio windows to a
Flask review service and the Vue interface shows bounded review artifacts for a
human reviewer. The tool does not make identity claims law enforcement claims
emergency claims or autonomous fraud accusations.

Technical answer:

The integration uses a signed POST /twilio/voice webhook consent first TwiML a
secure Media Streams WebSocket in memory frame processing immediate buffer purge
redacted session state and audit metadata. Twilio is the live communications
layer and makes the end to end workflow possible.

Demo answer:

The demo shows an inbound call a consent prompt press 1 Media Stream start live
panel session tracking review artifact creation human review required state and
no raw audio retention.

## Safety And Privacy Answer

The pilot is defensive and supervised. It is not a surveillance tool, not an
impersonation tool, and not a system for autonomous claims about a caller. It
requires consent before streaming. Raw call audio is not written to disk by the
gateway. The retained data is limited to metadata, frame counts, stream state,
review labels, and audit events for human review.

## Consent Answer

The inbound call flow starts with a consent prompt. If the caller does not press
`1`, the call ends. If the caller confirms, Twilio starts a Media Stream and the
review state remains bounded to education and human review.

## Retention Answer

Raw audio frames are decoded into memory, converted into a review artifact, and
zeroed immediately after use. The application retains only metadata required to
show the session state and audit the review boundary.

## Low-Volume Pilot Answer

The initial pilot is low-volume and limited to approved test callers. The goal is
to validate consent, streaming, audit, and reviewer ergonomics before any wider
deployment. SMS and WhatsApp are explicitly out of scope for this first step.

## Public-Facing Summary

V.O.T Guardian is an educational cybersecurity tool for learning how
voice-fraud awareness workflows should be reviewed responsibly. It demonstrates
how to keep consent, privacy, evidence quality, and human judgment in the loop
when discussing AI voice risk.

## Final Submit Checklist

- Confirm the Proton message sender and form URL.
- Confirm the application is relevant to Twilio, startup, grant, or partner
  support.
- Confirm which track is being selected.
- Confirm the Twilio account used for the application.
- Confirm the applicant is over 21.
- Confirm all personal and sole-proprietor fields are accurate.
- Confirm the demo link is public or access-safe for reviewers.
- Confirm all pasted answers avoid unsupported special characters.
- Confirm no `.env`, token, private audio, or private archive is attached.
- Confirm wording does not claim production readiness.
- Confirm permission to use company name and logo is acceptable.
- Confirm final submit with the account owner before sending.

## Follow-Up Email Draft

Subject: V.O.T Guardian Twilio Media Streams pilot

Hello,

Thank you for reviewing V.O.T Guardian. The project is a supervised educational
voice-risk review pilot focused on consent, privacy, no raw-audio retention, and
human review. The first Twilio integration uses Programmable Voice and Media
Streams only; SMS and messaging are deferred until the correct compliance path
is ready.

I would be glad to provide a short technical demo, the webhook flow, or the data
retention notes if useful.

Jean-Sebastien Beaulieu
