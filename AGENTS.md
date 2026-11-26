# Agent instructions

## Objective
Build an educational AWS-backed S3-compatible object storage QA automation framework. The user is a QA engineer learning infrastructure and automation; explain commands and design choices in Korean. Prioritize hands-on learning over generating everything at once.

## Workflow
- Read docs/PROJECT_SPEC.md before implementing.
- Start at Phase 1; inspect existing files and git status first. Do not overwrite existing work.
- Implement one phase at a time, explain changes and provide executable commands, expected results and troubleshooting. Run available checks and report actual results; never invent test results.
- Keep tests isolated using unique buckets and cleanup fixtures; separate common API tests from provider-specific and destructive tests.
- Pin verified dependency and image versions. Verify MinIO source/build availability against upstream before selecting a version; use isolated lab only, never expose unsupported MinIO to the internet.
- No real credentials in source, logs or reports. Use environment variables locally and AWS credential provider chain / GitHub OIDC in cloud. Use least privilege.
- Do not create paid AWS resources, push remote commits, deploy, or destroy resources without explicit user authorization. Show cost implications and terraform plan first. Restrict destructive tests to explicitly designated disposable targets.
- Document requirements-to-test traceability, actual evidence and limitations. Treat EKS and performance tooling as optional.
