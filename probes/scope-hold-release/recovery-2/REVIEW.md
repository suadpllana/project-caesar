# Recovery 2: evidence and repair

The contributor reports another easiness pass (0/3 low-effort solves) and difficulty failure
(0/8 xhigh solves). The six supplied exports contain clipped tool commands, collapsed reasoning
and abbreviated tool outputs. They do not contain final source files or verifier reports. We can
identify decisions from the visible summaries, but cannot replay the actual six submissions or
claim a measured change in frontier solve rate.

## Evidence retained

The six original text exports are copied byte-for-byte beside this file. `before.zip` preserves
the previously delivered bundle; `before-instruction.md` preserves its brief. `audit-results.json`
contains isolated decision models, first counterexamples and actual Python worker/grader results.

| Export | Visible decision | Interpretation |
|---|---|---|
| easiness-4gXiDiD.txt | Factory work charged to current scope; completion-order teardown; recursive admission | Wrong capture prior plus following the contradictory wrapper rule |
| easiness-AeUTHMn.txt | Factory build moved to invocation scope; completion-order teardown; recursive admission | Changes core-established identity behavior to fit a familiar lifetime model |
| easiness-ngR4hFD.txt | Correct factory capture; completion-order teardown; inherited marked owner; recursive admission | Correct central discovery still fails because the written rules encourage other wrong decisions |
| difficulty-AtTR7eA.txt | Correct factory capture; completion-order teardown; inherited ownership; recursive admission; rejects dead tokens | Explicitly follows wrapper-before-wrapped wording and adds unspecified lifetime restrictions |
| difficulty-n8so3oN.txt | Correct factory capture and allocation order; inherited marked owner | Closest visible method; explicitly reports the contradiction and chooses the grader-compatible side |
| difficulty-DBWMDtS.txt | Completion-order teardown; inherited marked owner; recursive admission; factory bound to holder owner; rejects dead tokens | Flags another ambiguity: holder build scope versus teardown owner |

All three low-effort exports commit after reading the tree and visible inputs in two tool calls.
The xhigh exports use four or five inspection calls and additional experiments. The decisive
difference is not exhaustion of the 14,400-second allowance: no export shows a timeout. All three
xhigh summaries identify factory capture, while two choose the ordering required by the brief
and rejected by the grader. The third explicitly calls it a judgment call. There is no evidence
that additional independent repairs were the main cause of this round's 0/8.

## The defects in the previous brief

1. It promised wrapped objects would be torn down after their wrappers. Core reserves the wrapper
   serial before recursive builds; the reference tears down descending serial. The named wrapper
   case therefore expects `log, core, skin`, the opposite of the prose. A misleading case label and
   solution metadata repeated the error. The earlier assistant review missed this contradiction.
2. "Owned by the scope its holder was built in" encouraged ordinary parent-owner inheritance.
   The actual rule propagates singleton ancestry, while marking changes only one instance's owner.
3. The admission text did not distinguish requested-name checks from checks on every dependency.
   The reference refuses an unmatched mark on the requested name, but an unmatched mark reached
   below an admitted request falls back to root ownership. It does not recursively rerun admission.
4. Token rebinding, holder owner versus resolve scope, and invocation after capture-scope closure
   were not specified. These distinctions do occur in the generated input space.
5. The brief said inter-scope order was ungraded although the grader compares entire ordered dumps.

## Repair choice

Three directions were considered under the contributor's request to fix the existing task:

- Correct only wrapper ordering. Rejected as incomplete: the closest xhigh decision model still
  fails 72/1,200 generated streams through marked-parent inheritance.
- Align the existing brief with all graded boundaries and add one compound input fixture. Applied.
  This preserves the scoring contract and all four policy repairs, supplies a reproducible input
  for the missed interaction and resolves ambiguities that made reasonable xhigh work fail.
- Change the oracle to conventional wrapper-first teardown and recursive lifetime inheritance.
  Rejected: it would change correct outputs and move the task toward the approaches the low-effort
  agents already wrote. It is unnecessary for repairing the existing task.

The revised brief defines allocation order, singleton precedence, non-inherited marks, cache
identity, request-level admission, token replacement, closed capture scopes and full output order.
`crossing.txt` combines nested marks, repeated factory calls, a marked dependency with an unmarked
child, a separate singleton subtree and a parting call. It contains inputs only. No reference,
expected trace, local scoring function or solution code has been added to the agent environment.

The misleading wrapper case identifier was renamed in the case list, ground-truth key and
answer-key forgery probe. All fixed inputs and expected record sequences remain identical.
`contract_check.py` verifies this plus unchanged generator, oracle, executable assertions,
reference, policies, isolation code, artifact boundary and timeouts against `before.zip`.

## Measured decision models

These are author-written isolated mutations on the reference, based on visible trajectory
summaries. They are not recovered agent patches or new Claude attempts. Each uses 22 fixed cases
and the same 1,200 streams named `recovery2-0` through `recovery2-1199`.

| Decision model | Wrong fixed / 22 | Wrong generated / 1,200 |
|---|---:|---:|
| Reference | 0 | 0 |
| Unchanged starting policies | 12 | 972 |
| Reverse completion order | 9 | 641 |
| Inherit marked parent's owner | 0 | 72 |
| Recursively run admission | 0 | 334 |
| Charge factory invocation to active scope | 4 | 344 |
| Bind factory token to holder teardown owner | 0 | 7 |
| Refuse tokens whose capture scope has closed | 0 | 9 |

The marked-inheritance mutation models the remaining reported distinction in n8so3oN. Correcting
that decision restores agreement in this model. It does not establish that the actual omitted
patch would pass, or that this agent would make the correction after reading the new brief.

## Difficulty judgment

The empirical split supports keeping capture and ownership as the central work: two low-effort
agents moved invocation to the current scope, while all three xhigh summaries retained capture.
The revised brief also makes that rule clearer, so the old low-effort failure count cannot be
claimed as evidence of a new 0/3 result.

A1 remains the departure from conventional container ownership. A3/B2 remain the interaction of
build scope, teardown owner, token capture and instance reuse; C1/C4 retain exact positive and
negative cases. C2 means no standard-container oracle or shipped expected outputs, not withheld
requirements. B1 is not claimed for this 310-line tree. The new compound fixture deliberately
improves local testability; it should increase solvability, and may also raise low-effort success.

The design target is now a reproducible expert path within the 1-7/8 band. No numerical solve-rate
prediction is justified by these clipped exports. Fresh easiness and difficulty probes are
required before acceptance can be claimed.

## Quality review and limits

- Paths and output schema: instruction lines 14-26; seven artifacts in task.toml; grader lines
  121-122. The report file is verifier-generated and is not an agent output artifact.
- Ownership/caching: instruction lines 31-38 and 45-50; core build, reference homes, independent
  oracle grow and the generated differential replay agree.
- Allocation/wrapping: instruction lines 40-43 and 50-51; named wrapping case and completion-order
  mutation distinguish allocation from completion. The contradictory wrapper promise is removed.
- Admission and token behavior: instruction lines 56-65 and 71-79; gate, plan and oracle agree;
  recursive-admission, holder-owner and dead-token mutations produce concrete counterexamples.
- Full order and refusal locations: instruction lines 67-69 and 81-85; exact comparisons in
  test_outputs.py lines 134-158. The previous claim that inter-scope ordering was ungraded is gone.
- Reference: solve.sh lines 7-14 copies four code files and executes each fixture. No fixture
  output is embedded in the solution. Four structurally different alternatives remain available
  in authoring and match the unchanged oracle.
- Environment: Dockerfile copies only app_src; tests and solution remain separate. No comments,
  docstrings, reference outputs or probe history are added to the agent-facing tree.
- Isolation: test.sh keeps root grading separate from uid 1002 execution. Host Python checks test
  the real worker serialization and every grader assertion, including both integrity attacks.
  Docker is unavailable, so these checks do not prove Linux permissions, descriptor inheritance,
  reaping or actual Harbor rewards. Container-only reward-tampering probes remain unrun.
- Prose: corrections work from the existing brief and preserve its incident, paths and record
  description. Structure, hint and category screens pass. The comparative text heuristic flags
  sentence/paragraph rhythm and counts possessive apostrophes as contractions. These advisory
  metrics do not establish authorship; no artificial quirks were added to manipulate them.
- Similarity: mechanical overlap is confined to Docker boilerplate; the local conceptual check
  does not identify another task grading the same thing. This is not an external originality
  verdict. The task's semantics are unchanged from the earlier originality search.
- Metadata now describes the actual allocation, ownership and admission rules and distinguishes
  author-side measurements from frontier solve rates. All original category, resource and
  contributor-experience fields are retained.

No provider API key is present in the current environment for an external model rubric or probe.
The archive is a revised candidate for re-probing, not a claim that either external gate passed.

The first revised archive was rejected by the external instruction-authorship screen. For the
resubmission candidate, the brief was returned to the contributor's original tone and sentence
shapes, with edits confined to the factual conflicts listed above. The comparative local prose
screen now reports no findings: burstiness 0.829, 33 percent short sentences, and none of its
stock-phrase, hedge, canned-antithesis, triad or dash-aside markers. No artificial errors or
contrived quirks were introduced. This is not a guarantee about the opaque external classifier.

Final host validation used Python 3.12.13 with pytest==9.1.1, matching the container's Python
series and pytest pin. The reference passes every Python grader assertion; the no-op and all 15
semantic/integrity probes fail as intended. Both integrity probes fail only their own integrity
check while passing all output checks. Four alternative correct implementations agree on all
22 named and 1,200 generated streams. All 25 shell scripts pass `bash -n`; all 34 bundled Python
files parse. These results remain distinct from unrun Docker/Harbor and external model gates.
