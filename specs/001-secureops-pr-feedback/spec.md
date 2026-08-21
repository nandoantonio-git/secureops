# Feature Specification: SecureOps PR Vulnerability Feedback

**Feature Branch**: `001-secureops-pr-feedback`

**Created**: 2026-08-21

**Status**: Draft

**Input**: Plataforma que analisa Pull Requests em busca de vulnerabilidades de código e devolve feedback diretamente no PR: o que foi encontrado, por que é um risco, e como corrigir de forma concreta e confiável.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receber feedback acionável no Pull Request (Priority: P1)

Como pessoa desenvolvedora, quero receber no Pull Request uma explicação clara de cada vulnerabilidade identificada, para entender o risco e corrigir o problema sem depender de uma lista técnica genérica.

**Why this priority**: Este é o fluxo central de valor do produto.

**Independent Test**: Submeter um Pull Request controlado contendo vulnerabilidades conhecidas e verificar se cada finding válido recebe causa, evidência, impacto, correção recomendada e exemplo seguro.

**Acceptance Scenarios**:

1. **Given** um Pull Request com uma vulnerabilidade conhecida na linguagem principal, **When** a análise é concluída, **Then** o Pull Request recebe feedback estruturado com causa, evidência, impacto e correção concreta com exemplo seguro.
2. **Given** um padrão de vulnerabilidade comum e conhecido, **When** a recomendação é gerada, **Then** a correção segue um modelo revisado e adaptado ao contexto do código.

---

### User Story 2 - Demonstrar análise em duas linguagens (Priority: P2)

Como avaliador externo, quero verificar que a plataforma analisa duas linguagens, com profundidade desigual, para confirmar suporte multilíngua real sem exigir paridade completa.

**Why this priority**: Duas linguagens são obrigatórias para avaliação, mas a profundidade precisa preservar qualidade no fluxo principal.

**Independent Test**: Rodar uma suíte controlada com casos vulneráveis e seguros nas duas linguagens.

**Acceptance Scenarios**:

1. **Given** código na linguagem principal, **When** a análise é executada, **Then** a plataforma identifica vulnerabilidades determinísticas e fluxos inseguros de dados.
2. **Given** código na segunda linguagem, **When** a análise é executada, **Then** a plataforma identifica padrões mínimos de vulnerabilidade previamente definidos e documentados.

---

### User Story 3 - Controlar bloqueios de merge com confiança (Priority: P3)

Como Security Champion ou Tech Lead, quero que o bloqueio automático comece consultivo e só bloqueie casos críticos de alta confiança, para evitar interrupções indevidas.

**Why this priority**: Bloqueios indevidos destroem a confiança dos desenvolvedores.

**Independent Test**: Usar Pull Requests controlados limpos e com vulnerabilidades críticas conhecidas.

**Acceptance Scenarios**:

1. **Given** modo advisory padrão, **When** um finding crítico é detectado, **Then** o PR recebe aviso sem bloqueio automático.
2. **Given** modo blocking habilitado, **When** há vulnerabilidade crítica conhecida sem proteção validada por múltiplos sinais, **Then** o merge é bloqueado com justificativa clara.
3. **Given** criticidade baseada apenas em IA, **When** o gate avalia o PR, **Then** esse sinal não pode bloquear merge isoladamente.

---

### User Story 4 - Gerenciar ciclo de vida de findings (Priority: P4)

Como responsável de segurança, quero alterar status e registrar sobrescritas manuais, para corrigir falsos positivos, aceitar riscos e manter rastreabilidade mínima.

**Why this priority**: Findings precisam ser reversíveis e governáveis.

**Independent Test**: Alterar o status de um finding e confirmar histórico da mudança.

**Acceptance Scenarios**:

1. **Given** um finding aberto, **When** o responsável altera para falso positivo ou risco aceito, **Then** o status e histórico ficam visíveis.
2. **Given** uma severidade contestada, **When** o responsável sobrescreve a decisão, **Then** a decisão humana prevalece.

### Edge Cases

- PR contém arquivos das duas linguagens.
- PR contém apenas arquivos fora das linguagens suportadas.
- Evidência suficiente para detectar risco, mas insuficiente para sugerir correção segura específica.
- Mesmo finding reaparece após ser marcado como falso positivo.
- Componente de IA indisponível.
- Finding crítico detectado por apenas um sinal isolado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST analyze Pull Requests and return vulnerability feedback directly in the Pull Request context.
- **FR-002**: System MUST support exactly two programming languages in this version, with one primary language and one secondary language.
- **FR-003**: System MUST provide deeper analysis for the primary language, including unsafe data-flow detection from untrusted inputs to sensitive locations.
- **FR-004**: System MUST provide minimum real deterministic coverage for the secondary language through documented vulnerability patterns.
- **FR-005**: System MUST generate findings with location, category, severity, evidence, status, and source.
- **FR-006**: System MUST publish each finding with cause, evidence, impact, recommended correction, and safe example.
- **FR-007**: System MUST NOT publish generic or unsupported remediation advice as concrete correction.
- **FR-008**: System MUST use reviewed remediation templates for common known patterns and adapt them to context.
- **FR-009**: System MUST distinguish advisory feedback from automatic merge blocking.
- **FR-010**: System MUST default to advisory mode.
- **FR-011**: System MUST allow automatic blocking only for a restricted subset of critical findings validated by multiple deterministic detection signals.
- **FR-012**: System MUST NOT allow a merge block decision to depend exclusively on AI-assisted judgment.
- **FR-013**: System MUST avoid blocking clean Pull Requests or Pull Requests without validated critical vulnerabilities.
- **FR-014**: System MUST maintain lifecycle status for each finding: open, in investigation, resolved, false positive, or accepted risk.
- **FR-015**: System MUST allow a responsible person to manually override finding status or automatic assessment.
- **FR-016**: System MUST retain minimal history for manual status changes and overrides.
- **FR-017**: System MUST preserve findings across analyses to distinguish new, existing, resolved, and overridden findings.
- **FR-018**: System MUST make scope limitations visible, including asymmetric depth between languages.
- **FR-019**: System MUST include a controlled validation set covering both languages, clean code, and known critical vulnerabilities.
- **FR-020**: System MAY include analytical views only as supporting context, not as the primary workflow.
- **FR-021**: System MUST NOT require model training, fine-tuning, or adaptive learning to function correctly in this version.

### Key Entities

- **Pull Request Analysis**: Analysis run for a proposed code change.
- **Finding**: Vulnerability report tied to a code location and category.
- **Remediation Recommendation**: Structured correction guidance attached to a finding.
- **Detection Signal**: Independent basis for identifying or validating a vulnerability.
- **Language Coverage Profile**: Declared analysis depth for each supported language.
- **Manual Override**: Human decision changing status or automatic assessment.
- **Validation Scenario**: Controlled PR or test case with expected behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 80% of valid findings in the validation set have correction rated useful by human reviewers.
- **SC-002**: Clean-code validation scenarios produce zero undue automatic merge blocks.
- **SC-003**: A known unprotected critical vulnerability is blocked when restricted blocking is enabled.
- **SC-004**: 100% of published findings include cause, evidence, impact, correction, and safe example.
- **SC-005**: 100% of automatic blocking decisions are traceable to critical findings validated by multiple deterministic signals and not based solely on IA.
- **SC-006**: Validation set demonstrates both languages, including deep primary-language analysis and at least one real secondary-language pattern.

## Assumptions

- Primary language is Python.
- Secondary language has deterministic minimum coverage and no complete taint analysis in this phase.
- Primary user is the developer receiving PR feedback.
- Governance user is a Security Champion or Tech Lead.
- Advisory mode is default.
- Fine-tuning is stretch goal only.
- Dashboard, RBAC/audit log completo, DAST, and async queues are out of this phase.
