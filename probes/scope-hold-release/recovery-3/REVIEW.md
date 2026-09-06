# Recovery 3: construction rollback

## Evidence

The contributor reports 3/3 low-effort successes within 90 seconds. The three supplied exports
are preserved beside this report. 3RfBuTd and 9tdtbYd read core and policies in two calls;
yZEpcwt reads all code and then executes the inputs. Each commits to the same four repairs
before its third and final tool call. Patch commands are clipped. The old reference models
their reported strategy; it is not an exact recovered submission.

The earlier quality criticism is confirmed: the compact tree and instruction supplied the
whole plan. The contributor approved transactional construction before tests were changed.
The rejected archive remains in recovery-2/quality-rejected.zip.

## Repair

Constructors can fail after dependencies finish. Fault switches change availability between
operations, allowing cached reuse while new construction fails. Rollback removes completed
objects from one attempt across all ownership scopes. Older borrowed cache entries survive.

The completion log omits unfinished singleton parents, but those parents still determine
rollback ownership. The allocation history contains them and also unfinished objects that
must not be disposed. Scope ownership cannot identify transaction membership. Leaving new
cache entries changes retries; clearing all entries destroys older committed objects.

The driver applies one attempt boundary to resolutions, captured factory calls and parting
calls. Refusal location and build scope remain distinct. Failed holder resolutions retain
older tokens. Rollback disposal runs no parting calls. The original four repairs remain needed.

Tactics: A1/A3, interacting B2, positive/negative C1 and exact C4. There is no performance
gate or claim that this compact tree creates distributed-repository difficulty.

## Contract review

- instruction.md:72-101 defines failure controls, cache bypass, construction order, refusal
  timing, rollback membership, ownership, retries, factory preservation and parting behavior.
  The seven artifact paths and 14,400-second budget remain explicit.
- core.py:33-61 reserves identities before recursive builds, records entered allocations and
  publishes only finished objects. The core and pristine overlay agree.
- solution/plan.py:15-35 derives ownership before removing provisional history, disposes only
  completed objects and restores saved caches.
- tests/oracle.py carries ancestry downward and removes cache entries by allocation identity.
  It shares no implementation with the reference. Eight manually written traces check it.
- tests/test_outputs.py:125-175 checks 42 fixed and 600 nonce-generated streams. All 22 old
  expected outputs remain unchanged. No tolerance or assertion has been weakened.
- test.sh, reap.py and both Dockerfiles remain byte-identical. Code executes as the sandbox
  user before trusted grading. Answers and reward remain root-owned. Two integrity probes
  return correct traces and fail only their intended integrity assertion.
- All ten visible fixtures contain inputs only. Agent/pristine files match byte-for-byte.
  Reference code and expected outputs remain outside the agent build context. Dockerignore
  excludes bytecode caches.
- Metadata describes five repairs, incomplete ancestry and provisional cache state. Category
  remains Software / Systems. It does not claim that file count is the source of difficulty.

## Measurements

Python 3.12.13 with pytest==9.1.1 and pytest-json-ctrf==0.5.2:

- Reference and four alternatives each match 42 fixed plus 2,400 generated streams.
- All seven real Python grader assertions pass for the reference.
- No-op, 23 wrong-reading policies, forged output and two integrity probes are rejected.
- The old four-fix strategy passes the 22 legacy examples but fails 9 new hand cases and
  all 300 construction streams in its mutation run.
- All ten visible fixtures match the reference and fail in the starting tree.
- The actual solve.sh installs all five policies and executes all ten fixtures.
- All 36 shell scripts pass syntax checks. Preflight has zero errors and 18 reviewed
  import-indirection warnings. Structure, hint, category, dead-field, solution-layout
  and extraneous-file screens pass.

Detailed results are in validation.json. These are host results, not Claude solve rates.

## Outstanding review and limits

The new instruction paragraphs are suggested additions to the existing brief and still need
contributor wording review. The local prose heuristic flags one three-item list; it is not an
authorship detector and no external authorship pass is claimed.

Subsequent update: the contributor approved the instruction and requested the packaged ZIP.
The wording review is complete and archive delivery is authorized. External gates remain pending.

The reference is still short. A strong agent choosing a cache snapshot and distinguishing
entered from completed allocations may solve quickly. The earlier strategy demonstrably
fails, but that does not establish a new solve rate or years of required expertise. The
one-line checker covers only the old ownership decisions, not the new rollback mechanism.

Docker/Podman and provider credentials are absent. Image builds, image answer-leak checks,
Harbor oracle/nop, Linux reward isolation, external quality review and fresh Claude probes
remain unrun. Recovery remains pending these gates. No submission-ready status is claimed.
