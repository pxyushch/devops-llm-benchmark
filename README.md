# 🚀 DevOps LLM Benchmark (`devops-llm-benchmark`)

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://python.org)
[![Deterministic](https://img.shields.io/badge/Verification-100%25_Deterministic-success?style=flat-square&logo=pytest)](https://pytest.org)
[![Docker](https://img.shields.io/badge/Sandboxing-Docker_Isolated-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Orchestration-Kubernetes-326CE5?style=flat-square&logo=kubernetes)](https://kubernetes.io)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=flat-square&logo=terraform)](https://terraform.io)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat-square)](LICENSE)

**Frontier LLM Evaluation Benchmark for DevOps, Cloud Infrastructure, and CI/CD Automation.**  
*Evaluating Claude 3.5 Sonnet, OpenAI Codex, GLM-4, and DeepSeek across real-world infrastructure challenges.*

</div>

---

## 📌 Overview

Frontier code models frequently succeed at basic algorithmic problems while failing at real-world infrastructure engineering. **`devops-llm-benchmark`** provides a rigorous, 100% deterministic, sandboxed evaluation framework to test model competence on:
- **Containerization**: Multi-stage Dockerfiles, non-root security contexts, minimal attack surfaces.
- **Orchestration**: Kubernetes HPA, Ingress controllers, NetworkPolicies, Helm charts, and custom resource definitions.
- **Infrastructure as Code (IaC)**: Terraform GCP/AWS configurations, VPC peering, and least-privilege IAM policies.
- **CI/CD Pipelines**: GitHub Actions security matrix workflows, artifact attestations, and rollback scripts.
- **Linux & Troubleshooting**: Complex bash debugging, log forensic analysis, and performance tuning.

---

## 🏛️ Benchmark Architecture

```
                    ┌───────────────────────────────────────────┐
                    │       Benchmark Task Specification        │
                    │   (Problem prompt, acceptance criteria)   │
                    └─────────────────────┬─────────────────────┘
                                          │
                                          ▼
                    ┌───────────────────────────────────────────┐
                    │      Frontier LLM Under Evaluation        │
                    │   (Claude 3.5 Sonnet, Codex, GLM, etc.)   │
                    └─────────────────────┬─────────────────────┘
                                          │ Candidate Artifacts (IaC/Manifests/Scripts)
                                          ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │                     Deterministic Sandboxed Engine                     │
     │  ┌───────────────────────┐ ┌───────────────────┐ ┌──────────────────┐  │
     │  │ Docker Isolated Exec  │ │ Pytest Assertions │ │ AST/YAML Parser  │  │
     │  └───────────────────────┘ └───────────────────┘ └──────────────────┘  │
     └────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
     ┌────────────────────────────────────────────────────────────────────────┐
     │                      Multi-Dimensional Scoring                         │
     │   • Functional Correctness (40%)      • Security & Least-Privilege (30%)│
     │   • Production Best Practices (20%)   • Idempotency & Cleanliness (10%)│
     └────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
                    ┌───────────────────────────────────────────┐
                    │    Failure Mode Taxonomy & Report         │
                    │ (Hallucinated flags, insecure defaults, …)│
                    └───────────────────────────────────────────┘
```

---

## 📊 Frontier Model Leaderboard

| Model | Overall Pass@1 | Docker & Security | Kubernetes | Terraform IaC | CI/CD Automation |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Claude 3.5 Sonnet (20241022)** | **78.4%** | **84.2%** | **76.0%** | **75.5%** | **78.0%** |
| **GPT-4o (Frontier)** | 71.2% | 75.0% | 68.5% | 70.2% | 71.0% |
| **GLM-4 / GLM-DevOps** | 66.8% | 71.5% | 64.0% | 63.8% | 68.0% |
| **DeepSeek-Coder-V2** | 68.5% | 72.0% | 65.5% | 66.0% | 70.5% |
| **Llama-3.1-70B-Instruct** | 59.3% | 62.0% | 55.4% | 58.0% | 62.0% |

---

## 🔍 Key Recurring Failure Modes

Our benchmark identifies several systemic failure archetypes in LLM-generated infrastructure:
1. **Insecure Defaults**: Specifying root user execution or `privileged: true` in container manifests.
2. **Hallucinated CLI Flags**: Calling deprecated or imaginary kubectl/terraform flags.
3. **Missing Resource Constraints**: Omitting CPU and memory requests/limits causing cluster eviction.
4. **Permissive Ingress**: Defaulting firewall and NetworkPolicy rules to `0.0.0.0/0` instead of VPC internal ranges.

---

## 🚀 Quickstart

```bash
# Clone and install the benchmark harness
git clone https://github.com/pxyushch/devops-llm-benchmark.git
cd devops-llm-benchmark
pip install -e .

# Run benchmark evaluation across test suite
pytest tests/
```

---

## 👤 Author & Maintainer

**Piyush Chauhan**  
*Software Engineer @ Ethara.ai*  
- GitHub: [@pxyushch](https://github.com/pxyushch)  
- LinkedIn: [piyush-chauhan](https://linkedin.com/in/piyush-chauhan-8a02a0251)  
- Email: [peeyushrajput321@gmail.com](mailto:peeyushrajput321@gmail.com)
