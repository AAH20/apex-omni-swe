# APEX_OMNI_SWE Automation Makefile
# Governed by Apex Growth Systems LLC. Zero external dependencies.

.PHONY: test benchmark solve autoharness clean lint

test:
	python3 -m unittest discover -s tests -v

benchmark:
	python3 -m benchmarks.benchmark_runner

solve:
	python3 -m apex_omni_swe.cli solve --diff

autoharness:
	python3 -m apex_omni_swe.cli autoharness

lint:
	python3 -m py_compile apex_omni_swe/*.py apex_omni_swe/*/*.py tests/*.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build dist *.egg-info
