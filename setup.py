#!/usr/bin/env python3
"""
APEX_OMNI_SWE Setup Configuration.
Governed by Apex Growth Systems LLC. Zero external dependencies.
"""

from setuptools import setup, find_packages

setup(
    name="apex-omni-swe",
    version="1.0.0",
    description="Sovereign Autonomous Software Engineering Hypervisor, AutoHarness Evolution Engine, and GraphRAG Synthesis Kernel.",
    author="Apex Growth Systems LLC",
    author_email="engineering@apexgrowth.io",
    packages=find_packages(include=["apex_omni_swe*"]),
    python_requires=">=3.9",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "apex-omni-swe=apex_omni_swe.cli:main",
        ],
    },
)
