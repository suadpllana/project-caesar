"""Verifier for the signed-callback task.

The task is to harden /app/svc/auth/verify.py so that an accepted request is one the
holder of the named key actually signed, in every part that changes what the service
does with it, while the traffic partners and the relay produce today keeps working.

These tests exercise the composed service end to end. Each one either

  * builds traffic the partner client library really produces and requires the service
    to accept it and record exactly the signed document, or
  * builds a forgery a relaying intermediary or a key holder could mount and requires
    the service to reject it and record nothing.

A forgery counts as rejected only when verification refuses it (HTTP 401 from
/app/svc/wsgi.py) and the ingest ledger gained no entry, so a solution cannot pass by
letting a request through and failing later.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import harness  # noqa: E402


def setup_function(function):
    harness.reset_ledger()


# ---------------------------------------------------------------------------
# 1. Legitimate traffic. This is the must-still-work side of the contract: it
#    fails any solution that tightens verification past what partners and the
#    relay actually send (extra unsigned relay headers, partner-chosen cover
#    lists and orderings, context values carrying the scheme's punctuation,
#    unicode payloads, bodies that are not in canonical serialization).
# ---------------------------------------------------------------------------


def test_partner_traffic_is_accepted_and_recorded_exactly():
    rng = harness.rng_for("legitimate")
    for index in range(200):
        request = harness.legitimate(rng)
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 200, (
            "legitimate partner request %d was refused (%s); every request the client "
            "library in /app/sdk/signer.py produces must still verify" % (index, payload)
        )
        assert len(records) == 1, (
            "legitimate request %d produced %d ledger entries, expected 1" % (index, len(records))
        )
        record = records[0]
        assert record["partner"] == request["partner"]
        assert record["target"] == request["target"]
        assert record["doc"] == request["doc"], (
            "the handler acted on a different document than the partner signed, on "
            "legitimate request %d" % index
        )


def test_unsigned_relay_headers_do_not_break_verification():
    rng = harness.rng_for("relay-headers")
    for index in range(25):
        request = harness.legitimate(rng, relay_headers=False)
        for name in harness.RELAY_HEADERS:
            request["headers"][name] = harness.text(rng, 12)
        request["headers"]["x-relay-note"] = harness.context_value(rng)
        status, _, records = harness.deliver(request["headers"], request["body"])
        assert status == 200, (
            "request %d was refused after the relay added its own unsigned headers; the "
            "relay always adds them and partners never sign them" % index
        )
        assert len(records) == 1


# ---------------------------------------------------------------------------
# 2. Coverage of the signature. A signature that does not cover a header cannot
#    authorize that header's value, so whatever is signed once must not be
#    mutable afterwards. Each case signs a well-formed request whose cover list
#    omits one field, then changes that field the way a relay would.
# ---------------------------------------------------------------------------


def test_partner_attribution_cannot_be_changed_after_signing():
    rng = harness.rng_for("cover-partner")
    for index in range(25):
        request = harness.legitimate(rng, partner="pt-beta", cover_drop="x-partner")
        request["headers"]["x-partner"] = "pt-alpha"
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 401, (
            "case %d: the service accepted a request attributed to pt-alpha whose "
            "signature never covered the partner header (%s)" % (index, payload)
        )
        assert records == []


def test_routing_target_cannot_be_changed_after_signing():
    rng = harness.rng_for("cover-target")
    for index in range(25):
        request = harness.legitimate(rng, target="notify", cover_drop="x-target")
        request["headers"]["x-target"] = "settle"
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 401, (
            "case %d: a request signed for the notify target was accepted after being "
            "re-pointed at settle (%s)" % (index, payload)
        )
        assert records == []


def test_body_cannot_be_swapped_when_its_digest_is_not_covered():
    rng = harness.rng_for("cover-body")
    for index in range(25):
        request = harness.legitimate(rng, cover_drop="x-body-sha256")
        replacement = harness.document(rng)
        request["headers"]["x-body-sha256"] = harness.signer.body_tag(replacement)
        status, payload, records = harness.deliver(
            request["headers"], harness.signer.body_bytes(replacement)
        )
        assert status == 401, (
            "case %d: the whole document was replaced and the request was still "
            "accepted, because the body digest was outside the signature (%s)"
            % (index, payload)
        )
        assert records == []


def test_stale_capture_cannot_be_refreshed_when_the_timestamp_is_not_covered():
    rng = harness.rng_for("cover-ts")
    stale = int(time.time()) - (harness.MAX_SKEW_SEC * 6)
    for index in range(25):
        request = harness.legitimate(rng, ts=stale, cover_drop="x-ts")
        request["headers"]["x-ts"] = str(int(time.time()))
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 401, (
            "case %d: an old captured request was accepted after its timestamp was "
            "rewritten to now, which the signature did not cover (%s)" % (index, payload)
        )
        assert records == []


def test_nonce_cannot_be_changed_when_it_is_not_covered():
    rng = harness.rng_for("cover-nonce")
    for index in range(25):
        request = harness.legitimate(rng, cover_drop="x-nonce")
        request["headers"]["x-nonce"] = harness.text(rng, 24)
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 401, (
            "case %d: the nonce was rewritten on a request whose signature did not "
            "cover it, and the service accepted the result (%s)" % (index, payload)
        )
        assert records == []


# ---------------------------------------------------------------------------
# 3. The document the handler works with. The digest in the signed headers has
#    to bind the document the ingest handler actually ends up with, not some
#    other reading of the same bytes.
# ---------------------------------------------------------------------------


def _inject_repeated_key(raw, key, value, front=True):
    """Insert a repeated member into the outermost object of a JSON document."""
    text = raw.decode("utf-8")
    opening = text.index("{")
    member = json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)
    if front:
        rest = text[opening + 1:].lstrip()
        if rest.startswith("}"):
            return None
        return (text[:opening + 1] + member + ", " + rest).encode("utf-8")
    closing = text.rindex("}")
    return (text[:closing].rstrip() + ", " + member + text[closing:]).encode("utf-8")


def test_document_cannot_be_reshaped_under_a_valid_signature():
    rng = harness.rng_for("body-differential")
    checked = 0
    for index in range(60):
        request = harness.legitimate(rng)
        target_key = sorted(request["doc"])[0]
        original = request["doc"][target_key]
        replacement = harness.text(rng, 9) if not isinstance(original, int) else original + 4242
        if replacement == original:
            continue
        forged = _inject_repeated_key(request["body"], target_key, replacement, front=True)
        if forged is None or forged == request["body"]:
            continue
        checked += 1
        status, payload, records = harness.deliver(request["headers"], forged)
        assert status == 401, (
            "case %d: a rewritten body was accepted under the original signature; the "
            "handler and the signature check must agree on what the document is (%s)"
            % (index, payload)
        )
        assert records == [], (
            "case %d: a rewritten body reached the ingest handler and was recorded"
            % index
        )
    assert checked >= 40, "the body-mutation corpus did not build enough cases"


def test_nested_document_cannot_be_reshaped_under_a_valid_signature():
    rng = harness.rng_for("body-differential-nested")
    checked = 0
    for index in range(60):
        doc = {"ref": harness.text(rng, 8),
               "order": {"account": harness.text(rng, 6), "amount": rng.randint(1, 5000)},
               "note": harness.text(rng, 12, wide=True)}
        request = harness.legitimate(rng, doc=doc)
        text = request["body"].decode("utf-8")
        marker = '"order": {'
        if marker not in text:
            continue
        cut = text.index(marker) + len(marker)
        forged = (text[:cut] + '"amount": ' + str(rng.randint(90000, 99999)) + ", "
                  + text[cut:]).encode("utf-8")
        checked += 1
        status, payload, records = harness.deliver(request["headers"], forged)
        assert status == 401, (
            "case %d: a nested field was rewritten under the original signature and the "
            "request was accepted (%s)" % (index, payload)
        )
        assert records == []
    assert checked >= 50, "the nested body-mutation corpus did not build enough cases"


def test_appended_document_changes_are_rejected():
    rng = harness.rng_for("body-append")
    for index in range(25):
        request = harness.legitimate(rng)
        forged = _inject_repeated_key(request["body"], "amount_override",
                                      rng.randint(10000, 99999), front=False)
        status, payload, records = harness.deliver(request["headers"], forged)
        assert status == 401, (
            "case %d: an extra member appended to the body was accepted (%s)"
            % (index, payload)
        )
        assert records == []


# ---------------------------------------------------------------------------
# 4. Freshness and replay. The relay can hold a request and send it again, or
#    send it twice. Two partners picking the same nonce is ordinary traffic and
#    must not be mistaken for a replay.
# ---------------------------------------------------------------------------


def test_a_delivered_request_is_not_accepted_a_second_time():
    rng = harness.rng_for("replay")
    for index in range(15):
        request = harness.legitimate(rng)
        first_status, _, first_records = harness.deliver(request["headers"], request["body"])
        assert first_status == 200, "case %d: the first delivery should be accepted" % index
        assert len(first_records) == 1
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 401, (
            "case %d: the relay re-sent an accepted request byte for byte and the "
            "service accepted it again (%s)" % (index, payload)
        )
        assert records == []


def test_the_same_nonce_from_different_keys_is_ordinary_traffic():
    rng = harness.rng_for("nonce-collision")
    assert len(harness.SIGNING_KEYS) >= 2
    for index in range(15):
        shared = harness.text(rng, 20)
        for key_id in harness.SIGNING_KEYS:
            request = harness.legitimate(rng, key_id=key_id, nonce=shared)
            status, payload, records = harness.deliver(request["headers"], request["body"])
            assert status == 200, (
                "case %d: key %s was refused for reusing a nonce another key had already "
                "used; nonces are only unique per key (%s)" % (index, key_id, payload)
            )
            assert len(records) == 1


def test_requests_outside_the_configured_skew_are_refused():
    rng = harness.rng_for("skew")
    skew = harness.MAX_SKEW_SEC
    for index in range(15):
        now = int(time.time())
        for offset in (-(skew * 4), -(skew + 120), skew + 120, skew * 4):
            request = harness.legitimate(rng, ts=now + offset)
            status, payload, records = harness.deliver(request["headers"], request["body"])
            assert status == 401, (
                "case %d: a request stamped %+d seconds from now was accepted, outside "
                "the configured tolerance of %d seconds (%s)"
                % (index, offset, skew, payload)
            )
            assert records == []


def test_requests_inside_the_configured_skew_are_accepted():
    rng = harness.rng_for("skew-inside")
    skew = harness.MAX_SKEW_SEC
    for index in range(15):
        now = int(time.time())
        for offset in (0, -(skew // 3), skew // 3, -(skew // 2)):
            request = harness.legitimate(rng, ts=now + offset)
            status, payload, records = harness.deliver(request["headers"], request["body"])
            assert status == 200, (
                "case %d: a request stamped %+d seconds from now was refused even though "
                "the configured tolerance is %d seconds (%s)"
                % (index, offset, skew, payload)
            )
            assert len(records) == 1


# ---------------------------------------------------------------------------
# 5. Key policy. Only keys the service's configuration treats as valid for
#    signing may produce an accepted request.
# ---------------------------------------------------------------------------


def test_keys_the_configuration_excludes_cannot_sign():
    rng = harness.rng_for("key-state")
    assert harness.NON_SIGNING_KEYS, "the key store must contain keys that may not sign"
    for index in range(10):
        for key_id in harness.NON_SIGNING_KEYS:
            request = harness.legitimate(rng, key_id=key_id)
            status, payload, records = harness.deliver(request["headers"], request["body"])
            assert status == 401, (
                "case %d: key %s is in state %r, which the running profile does not "
                "accept for signing, yet its request was accepted (%s)"
                % (index, key_id, harness.keys.lookup(key_id)["state"], payload)
            )
            assert records == []


def test_keys_the_configuration_allows_can_sign():
    rng = harness.rng_for("key-state-ok")
    for key_id in harness.SIGNING_KEYS:
        request = harness.legitimate(rng, key_id=key_id)
        status, payload, records = harness.deliver(request["headers"], request["body"])
        assert status == 200, (
            "key %s is accepted for signing by the running profile but its request was "
            "refused (%s)" % (key_id, payload)
        )
        assert len(records) == 1


# ---------------------------------------------------------------------------
# 6. Plain tampering. Cheap cases that catch a verifier which stopped checking
#    the signature at all while chasing the harder properties.
# ---------------------------------------------------------------------------


def test_plain_tampering_is_refused():
    rng = harness.rng_for("tampering")
    for index in range(20):
        base = harness.legitimate(rng)

        flipped = dict(base["headers"])
        digit = flipped["x-sig"][0]
        flipped["x-sig"] = ("0" if digit != "0" else "1") + flipped["x-sig"][1:]
        cases = [("flipped signature", flipped, base["body"])]

        missing = dict(base["headers"])
        missing.pop("x-sig")
        cases.append(("missing signature", missing, base["body"]))

        unknown = dict(base["headers"])
        unknown["x-key-id"] = "k-does-not-exist"
        cases.append(("unknown key id", unknown, base["body"]))

        wrong_key = [k for k in harness.SIGNING_KEYS if k != base["key_id"]][0]
        foreign = harness.legitimate(rng, key_id=wrong_key, partner=base["partner"],
                                     target=base["target"], doc=base["doc"],
                                     nonce=base["nonce"])
        borrowed = dict(base["headers"])
        borrowed["x-sig"] = foreign["headers"]["x-sig"]
        cases.append(("signature from another key", borrowed, base["body"]))

        rewritten_cover = dict(base["headers"])
        rewritten_cover["x-sig-headers"] = ";".join(
            [n for n in rewritten_cover["x-sig-headers"].split(";") if n] + ["x-ctx"]
        )
        cases.append(("rewritten cover list", rewritten_cover, base["body"]))

        other = harness.legitimate(rng)
        cases.append(("body from another request", dict(base["headers"]), other["body"]))

        empty = dict(base["headers"])
        cases.append(("empty body", empty, b""))

        for label, headers, body in cases:
            status, payload, records = harness.deliver(headers, body)
            assert status == 401, (
                "case %d (%s): the service accepted a request it should have refused (%s)"
                % (index, label, payload)
            )
            assert records == [], "case %d (%s): a refused request still reached ingest" % (
                index, label,
            )


def test_environment_is_the_one_the_verifier_expects():
    """Fail loudly rather than silently grading against the wrong configuration."""
    report = harness.env_report()
    assert report["profile"] == "standard", report
    assert report["max_skew_sec"] > 0, report
    assert report["signing_keys"], report
    assert os.path.isfile("/app/svc/auth/verify.py"), report
