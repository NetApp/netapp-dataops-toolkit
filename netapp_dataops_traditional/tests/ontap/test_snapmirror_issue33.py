"""
Regression tests for GitHub issue #33:
  "List SnapMirror Relationships tool fails with 'policy field has not been set' error."

Production file under test (never modified here):
  netapp_dataops_traditional/netapp_dataops/traditional/ontap/snapmirror_operations.py

These are UNIT TESTS only.  All network-dependent behaviour is replaced with
mocks, so no ONTAP credentials, network access, or real NetApp cluster are
needed or contacted.

Real SnapmirrorRelationship objects are constructed via
  SnapmirrorRelationship.from_dict(...)
so that the SDK's own attribute-guard logic fires exactly as in production.
Only three I/O entry points are patched:

  _retrieve_config          → returns a static config dict
  _instantiate_connection   → no-op, no connection attempted
  NetAppSnapmirrorRelationship.get_collection
                            → yields one fake relationship object

Two test functions:

  test_missing_policy_returns_none
      Regression test for issue #33.
      The relationship omits the 'policy' field.  After the fix the function
      must NOT raise; it must return a list with one entry whose "Type" is None.

  test_present_policy_returns_type
      Control / happy-path test.
      The relationship has policy.type == "async".  The function must return
      a list with one entry whose "Type" == "async".
"""

import pytest
from unittest.mock import patch, MagicMock

from netapp_ontap.resources import SnapmirrorRelationship as NetAppSnapmirrorRelationship
from netapp_dataops.traditional.ontap.snapmirror_operations import (
    list_snap_mirror_relationships,
)


# ---------------------------------------------------------------------------
# Patch-target constants — match what the production module imports
# ---------------------------------------------------------------------------
_MOD = "netapp_dataops.traditional.ontap.snapmirror_operations"
_RETRIEVE_CONFIG    = f"{_MOD}._retrieve_config"
_INSTANTIATE_CONN   = f"{_MOD}._instantiate_connection"
_GET_COLLECTION     = f"{_MOD}.NetAppSnapmirrorRelationship.get_collection"


# ---------------------------------------------------------------------------
# Minimal valid config (no real credentials required)
# ---------------------------------------------------------------------------
_FAKE_CONFIG = {
    "connectionType": "ONTAP",
    "hostname":       "fake-cluster.example.com",
    "username":       "admin",
    "password":       "fake-password",
    "svm":            "fake_svm",
    "dataLIF":        "192.0.2.1",
    "verifySSLCert":  False,
}

# Minimal fields shared by both test objects
_BASE_FIELDS = {
    "uuid":        "aaaabbbb-1234-5678-abcd-ef0123456789",
    "source":      {"svm": {"name": "source_svm"}, "path": "source_svm:source_vol"},
    "destination": {"svm": {"name": "dest_svm"},   "path": "dest_svm:dest_vol"},
    "healthy":     True,
}


# ---------------------------------------------------------------------------
# Helper: patch I/O and run the real production function
# ---------------------------------------------------------------------------

def _run(fake_rel):
    """
    Patch the three I/O entry points, inject *fake_rel* as the sole
    relationship returned by get_collection(), and call the real
    list_snap_mirror_relationships().  Returns the function's return value
    or re-raises whatever it raises.
    """
    # Patch get() on the real SDK object so it does not attempt HTTP
    fake_rel.get = MagicMock(return_value=None)

    with patch(_RETRIEVE_CONFIG,  return_value=_FAKE_CONFIG), \
         patch(_INSTANTIATE_CONN, return_value=None), \
         patch(_GET_COLLECTION,   return_value=iter([fake_rel])):
        return list_snap_mirror_relationships(print_output=False)


# ===========================================================================
# Test 1 — Regression: missing policy must not crash; Type must be None
# ===========================================================================

def test_missing_policy_returns_none():
    """
    Regression test for issue #33.

    A real SnapmirrorRelationship built without a 'policy' key causes the
    NetApp SDK to raise:
        AttributeError: The 'policy' field has not been set ...

    After the production fix (try/except AttributeError → policy_type = None)
    the function must complete successfully and return a list whose sole
    entry has "Type" set to None.

    This is a mock-based unit test.  No ONTAP cluster, credentials, or
    network access are used.
    """
    fake_rel = NetAppSnapmirrorRelationship.from_dict(_BASE_FIELDS)

    # Confirm the SDK raises as expected — documents the bug precondition
    with pytest.raises(AttributeError, match="policy.*has not been set"):
        _ = fake_rel.policy

    result = _run(fake_rel)

    assert len(result) == 1,            f"Expected 1 relationship, got {len(result)}"
    assert result[0]["Type"] is None,   f"Expected Type=None, got {result[0]['Type']!r}"

    # Spot-check the other fields are still populated correctly
    assert result[0]["UUID"]          == "aaaabbbb-1234-5678-abcd-ef0123456789"
    assert result[0]["Source SVM"]    == "source_svm"
    assert result[0]["Source Volume"] == "source_vol"
    assert result[0]["Dest SVM"]      == "dest_svm"
    assert result[0]["Dest Volume"]   == "dest_vol"
    assert result[0]["Healthy"]       is True


# ===========================================================================
# Test 2 — Control: present policy must pass through unchanged
# ===========================================================================

def test_present_policy_returns_type():
    """
    Control / happy-path test.

    When policy.type IS present the function must return it unchanged.
    This verifies the fix does not regress the normal code path.

    This is a mock-based unit test.  No ONTAP cluster, credentials, or
    network access are used.
    """
    fake_rel = NetAppSnapmirrorRelationship.from_dict({
        **_BASE_FIELDS,
        "policy": {"type": "async"},
    })

    result = _run(fake_rel)

    assert len(result) == 1,                f"Expected 1 relationship, got {len(result)}"
    assert result[0]["Type"] == "async",    f"Expected Type='async', got {result[0]['Type']!r}"

    assert result[0]["UUID"]          == "aaaabbbb-1234-5678-abcd-ef0123456789"
    assert result[0]["Source SVM"]    == "source_svm"
    assert result[0]["Source Volume"] == "source_vol"
    assert result[0]["Dest SVM"]      == "dest_svm"
    assert result[0]["Dest Volume"]   == "dest_vol"
    assert result[0]["Healthy"]       is True
