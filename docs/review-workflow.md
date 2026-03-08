# Review Workflow Notes

Use the benchmark branches as small, focused pull requests.

Recommended review loop:

1. inspect the title and short description
2. read the diff without running the code first
3. classify findings by category and severity
4. compare the output against the ground truth only after review is complete

The benchmark intentionally mixes:

- clean pull requests
- style-only regressions
- logic bugs that may still pass tests
- cross-file contract problems
- security and performance issues that require code evidence
