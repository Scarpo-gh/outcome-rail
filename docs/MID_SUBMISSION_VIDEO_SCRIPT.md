# OutcomeRail — Mid-Submission Progress Update Video

**Target duration:** 2–3 minutes  
**Format:** Screen recording of the five-slide deck, with no webcam required.  
**Deck:** https://scarpo-gh.github.io/outcome-rail/checkpoint-2-deck.html

## Narration

Hi, I’m Onur, building OutcomeRail for the Agentic Economy track.

OutcomeRail addresses a simple problem: an agent can read public prediction-market data, but another agent cannot easily check which snapshot it used, which safety rules ran, or whether the delivered analysis was changed afterwards.

OutcomeRail is a read-only public-data analysis layer. Our first adapter uses public Polymarket Gamma and CLOB data. It normalizes a market snapshot, runs deterministic visible-depth, spread, freshness, and price-impact checks, and produces a canonical analysis receipt. The receipt binds the request input, source and snapshot hashes, policy version, analysis result, and evidence hash. If a bound field changes, verification fails.

The point is not to give trading advice or place orders. OutcomeRail is a validation and provenance layer for agent-generated market analysis. It can classify a public snapshot as fully supported, partially supported, or unsupported by visible data and versioned policy rules. It does not connect user wallets, hold funds, use venue credentials, or make investment recommendations.

For the Arc integration, we demonstrated two bounded ERC-8183 agent-job paths on Arc Testnet using the predeployed reference contract and test-USDC. In Job A, a verified OutcomeRail receipt hash was submitted as the deliverable and the job was completed. In Job B, a separate job passed its expiry and the client refund path was executed. Both paths are linked in our public repository and Arc evidence bundle.

What is working today is the public-data adapter, deterministic receipt generation and verification, policy guardrails, local and Foundry tests, a clean-clone reproduction check, and the Arc Testnet completion and refund evidence.

Next, we will standardize the agent deliverable schema and add signed callbacks or external checkpoints. We also want to evaluate the validation layer against read-only signal workflows: whether it prevents low-depth, stale, or poor-quality market actions without blocking good opportunities.

Thank you for reviewing OutcomeRail. The repository, live deck, and Arc Testnet evidence are all public and linked in the submission.
