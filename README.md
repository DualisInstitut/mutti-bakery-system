# Mutti's Bakery System — Version Control Workspace
> **Module:** LF5.3 – Development Tools & Version Control (The Workshop Setup)  
> **Environment:** Ubuntu Linux Sandbox Localization  

---

## 1. Project Overview
This repository serves as a collaborative sandbox environment for Module LF5.3 to master version control, repository management, and team synchronization using Git and GitHub. The project simulates a multi-developer workflow centered around a local recipe system configuration.

---

## 2. Repository Access & Branching Policy
> 🔐 **Shared Admin Topology:** All core team members (Ali, David, Philip, Tim, Lothar) hold equal administrative permissions (`Admin Access`) to facilitate fluid integration.

To preserve the stability of the production-ready `main` branch, the team strictly adheres to a **Feature Branch Workflow**. Developers push modifications exclusively to their assigned branches before merging.

### Branch Assignment Matrix
| Developer | Active Feature Branch | Component Focus | Access Level |
| :--- | :--- | :--- | :--- |
| **Ali** | `feature/profile-ali` | Local Configuration & `team-members/alinazari.md`. | Shared Admin |
| **David** | `feature/profile-david` | Local Configuration & Student Profile. | Shared Admin |
| **Philip** | `feature/profile-philip` | Local Configuration & Student Profile. | Shared Admin |
| **Tim** | `feature/profile-tim` | Local Configuration & Student Profile. | Shared Admin |
| **Lothar** | `feature/profile-lothar` | Local Configuration & Student Profile. | Shared Admin |

---

## 3. Project File Structure
```text
mutti-bakery-system
│
├── .gitignore          # Standard Python exclusion matrix
├── README.md           # Master technical repository overview 
│
└── team-members/       # Standardized index for student profiles
  

4. Execution Guideline

The workspace enforces the Conventional Commits standard for clear auditing history:

    feat: For new functional configurations.

    fix: For immediate logic adjustments.

    docs: For repository documentation updates (e.g., updates to this README).

Developed under compliance with the Dualis Institut software specifications for Module LF5.3.