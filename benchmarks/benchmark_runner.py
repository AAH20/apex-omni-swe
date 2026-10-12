"""
Top-level benchmark runner shim for APEX_OMNI_SWE.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from __future__ import annotations
import sys
import os

# Add apex_omni_swe package root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apex_omni_swe.benchmarks.benchmark_runner import run_all_institutional_benchmarks

if __name__ == "__main__":
    sys.exit(run_all_institutional_benchmarks())
