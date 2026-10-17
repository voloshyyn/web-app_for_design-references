"""
SDD Project Management Automation Script:
Calculates CPM (Critical Path Method), Slack, Durations (Human vs AI),
and generates Mermaid Gantt and decomposition tables.
"""
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class SDDTask:
    id: str
    name: str
    ticket_type: str  # Specification, Addendum, Test, Feature, Verification, Validation, Documentation, Gate
    req_ids: List[str]
    assignee_role: str  # AI Agent, Human, Automated / CI, Joint
    duration_ai_h: float
    duration_human_h: float
    predecessors: List[str] = field(default_factory=list)
    is_high_cost_of_failure: bool = False
    notes: str = ""

    # CPM fields (in hours)
    es: float = 0.0  # Early Start
    ef: float = 0.0  # Early Finish
    ls: float = 0.0  # Late Start
    lf: float = 0.0  # Late Finish
    slack: float = 0.0
    is_critical: bool = False

    @property
    def total_duration(self) -> float:
        return self.duration_ai_h + self.duration_human_h


def get_project_tasks() -> Dict[str, SDDTask]:
    tasks = [
        # --- Stage 0: Requirements Baseline & Gate Review ---
        SDDTask(
            id="SPEC-BASE",
            name="Аудит базової лінії SRS v1.0 та верифікація меж",
            ticket_type="Specification",
            req_ids=["REQ-F-001..008", "REQ-NF-001..005"],
            assignee_role="Human",
            duration_ai_h=0.2,
            duration_human_h=1.0,
            predecessors=[],
            notes="Людина верифікує відсутність прогалин перед початком робіт"
        ),
        SDDTask(
            id="GATE-PLAN",
            name="Контрольна точка PLAN-GATE (Рішення GO)",
            ticket_type="Gate",
            req_ids=["ALL"],
            assignee_role="Human",
            duration_ai_h=0.1,
            duration_human_h=0.5,
            predecessors=["SPEC-BASE"],
            notes="Бінарне рішення GO/REVISE. Дозвіл на початок робіт"
        ),

        # --- Sprint 1: Core Reference & Integrity (High Cost of Failure) ---
        SDDTask(
            id="TEST-01",
            name="Розробка BDD-тестів створення та валідації URL (SCN-01, SCN-02)",
            ticket_type="Test",
            req_ids=["REQ-F-001", "REQ-NF-004"],
            assignee_role="Joint",
            duration_ai_h=0.3,
            duration_human_h=0.7,
            predecessors=["GATE-PLAN"],
            is_high_cost_of_failure=True,
            notes="ШІ пише тест, Людина перевіряє сценарії блокування javascript: та XSS"
        ),
        SDDTask(
            id="FEAT-01",
            name="Імплементація сутності Reference та валідатора URL/XSS",
            ticket_type="Feature",
            req_ids=["REQ-F-001", "REQ-NF-004"],
            assignee_role="AI Agent",
            duration_ai_h=0.5,
            duration_human_h=0.2,
            predecessors=["TEST-01"],
            is_high_cost_of_failure=True,
            notes="Блокується до створення та схвалення TEST-01 (TDD)"
        ),
        SDDTask(
            id="TEST-02",
            name="Розробка тестів категорій та Fallback до 'General' (SCN-05)",
            ticket_type="Test",
            req_ids=["REQ-F-002", "REQ-NF-003"],
            assignee_role="AI Agent",
            duration_ai_h=0.2,
            duration_human_h=0.3,
            predecessors=["TEST-01"],
            is_high_cost_of_failure=True,
            notes="Перевірка 0% втрати даних при видаленні категорії"
        ),
        SDDTask(
            id="FEAT-02",
            name="Реалізація категорій та механізму цілісності",
            ticket_type="Feature",
            req_ids=["REQ-F-002", "REQ-NF-003"],
            assignee_role="AI Agent",
            duration_ai_h=0.4,
            duration_human_h=0.2,
            predecessors=["FEAT-01", "TEST-02"],
            notes="Прив'язка до дефолтної категорії General"
        ),
        SDDTask(
            id="GATE-CORE",
            name="Контрольна точка CORE-GATE (Перевірка ядра та безпеки)",
            ticket_type="Gate",
            req_ids=["REQ-F-001", "REQ-F-002", "REQ-NF-003", "REQ-NF-004"],
            assignee_role="Human",
            duration_ai_h=0.1,
            duration_human_h=0.8,
            predecessors=["FEAT-02"],
            is_high_cost_of_failure=True,
            notes="Аудит людиною захисту від ін'єкцій та цілісності даних"
        ),

        # --- Sprint 2: Tagging, Facets & Instant Search ---
        SDDTask(
            id="TEST-03",
            name="Тести фасетного тегування та AND-фільтрації (SCN-03, SCN-04)",
            ticket_type="Test",
            req_ids=["REQ-F-004", "REQ-F-005", "REQ-NF-001"],
            assignee_role="AI Agent",
            duration_ai_h=0.3,
            duration_human_h=0.3,
            predecessors=["GATE-CORE"],
            notes="Перевірка префіксів namespace:value та SLA швидкодії <50мс"
        ),
        SDDTask(
            id="FEAT-03",
            name="Імплементація нормалізації тегів та фасетного індексатора",
            ticket_type="Feature",
            req_ids=["REQ-F-004", "REQ-F-005"],
            assignee_role="AI Agent",
            duration_ai_h=0.6,
            duration_human_h=0.2,
            predecessors=["TEST-03"],
            notes="Реалізація перетину множин тегів у Catalog.filter_by_tags"
        ),
        SDDTask(
            id="TEST-04",
            name="Тести повнотекстового пошуку (SCN-06) та колекцій N:M (SCN-07)",
            ticket_type="Test",
            req_ids=["REQ-F-003", "REQ-F-006", "REQ-F-007", "REQ-F-008"],
            assignee_role="AI Agent",
            duration_ai_h=0.3,
            duration_human_h=0.3,
            predecessors=["TEST-03"],
            notes="Пошук за підрядками без урахування регістру та зв'язки колекцій"
        ),
        SDDTask(
            id="FEAT-04",
            name="Імплементація пошуку, колекцій та операцій CRUD",
            ticket_type="Feature",
            req_ids=["REQ-F-003", "REQ-F-006", "REQ-F-007", "REQ-F-008"],
            assignee_role="AI Agent",
            duration_ai_h=0.7,
            duration_human_h=0.2,
            predecessors=["FEAT-03", "TEST-04"],
            notes="Пошук у Catalog.search, моделі Collection та видалення"
        ),

        # --- Sprint 3: Verification, Validation & Final Gate ---
        SDDTask(
            id="VERIF-ALL",
            name="Автоматизована верифікація та бенчмарк SLA (CI Suite)",
            ticket_type="Verification",
            req_ids=["REQ-NF-001", "REQ-NF-005"],
            assignee_role="Automated / CI",
            duration_ai_h=0.3,
            duration_human_h=0.2,
            predecessors=["FEAT-04"],
            notes="100% проходження pytest та перевірка Latency < 50 мс"
        ),
        SDDTask(
            id="VALID-UX",
            name="Валідація людиною (UX audit, відповідність концепції)",
            ticket_type="Validation",
            req_ids=["REQ-NF-002"],
            assignee_role="Human",
            duration_ai_h=0.1,
            duration_human_h=1.0,
            predecessors=["VERIF-ALL"],
            notes="Перевірка додавання референсу за <= 3 дії, відсутність gold plating"
        ),
        SDDTask(
            id="DOC-RTM",
            name="Фіналізація документації та матриці RTM",
            ticket_type="Documentation",
            req_ids=["ALL"],
            assignee_role="Joint",
            duration_ai_h=0.4,
            duration_human_h=0.6,
            predecessors=["VALID-UX"],
            notes="Синхронізація traceability-matrix.md та user-guide.md"
        ),
        SDDTask(
            id="GATE-FINAL",
            name="Контрольна точка RELEASE-GATE (Фінальне схвалення)",
            ticket_type="Gate",
            req_ids=["ALL"],
            assignee_role="Human",
            duration_ai_h=0.1,
            duration_human_h=0.5,
            predecessors=["DOC-RTM"],
            notes="Остаточний допуск релізу до розгортання"
        ),
    ]
    return {t.id: t for t in tasks}


def calculate_cpm(tasks: Dict[str, SDDTask]) -> float:
    # Forward Pass: calculate ES and EF
    for task_id, task in tasks.items():
        if not task.predecessors:
            task.es = 0.0
        else:
            task.es = max(tasks[p].ef for p in task.predecessors)
        task.ef = task.es + task.total_duration

    # Project duration
    project_duration = max(t.ef for t in tasks.values())

    # Build successors mapping
    successors: Dict[str, List[str]] = {t_id: [] for t_id in tasks}
    for t_id, task in tasks.items():
        for p in task.predecessors:
            successors[p].append(t_id)

    # Backward Pass: calculate LF and LS
    # Traverse in reverse topological order (by decreasing EF)
    sorted_tasks = sorted(tasks.values(), key=lambda t: t.ef, reverse=True)
    for task in sorted_tasks:
        if not successors[task.id]:
            task.lf = project_duration
        else:
            task.lf = min(tasks[s].ls for s in successors[task.id])
        task.ls = task.lf - task.total_duration
        task.slack = round(task.ls - task.es, 4)
        if abs(task.slack) < 1e-4:
            task.slack = 0.0
            task.is_critical = True
        else:
            task.is_critical = False

    return project_duration


def main():
    tasks = get_project_tasks()
    total_proj_duration = calculate_cpm(tasks)

    total_ai_hours = sum(t.duration_ai_h for t in tasks.values())
    total_human_hours = sum(t.duration_human_h for t in tasks.values())
    total_effort = total_ai_hours + total_human_hours

    critical_tasks = [t for t in tasks.values() if t.is_critical]

    print("=" * 70)
    print("SDD CRITICAL PATH METHOD (CPM) & SCHEDULE ANALYSIS")
    print("=" * 70)
    print(f"Total Project Duration (Calendar/Sequential Critical Path): {total_proj_duration:.2f} hours")
    print(f"Total Work Effort: {total_effort:.2f} person-hours")
    print(f"  - AI Agent Effort:    {total_ai_hours:.2f} hours ({total_ai_hours/total_effort*100:.1f}%)")
    print(f"  - Human (Lead) Effort: {total_human_hours:.2f} hours ({total_human_hours/total_effort*100:.1f}%)")
    print("\nCRITICAL PATH TASKS (Slack = 0):")
    for ct in critical_tasks:
        print(f"  * [{ct.id}] {ct.name} (Dur: {ct.total_duration:.1f}h, ES={ct.es:.1f}h, EF={ct.ef:.1f}h, Role: {ct.assignee_role})")

    print("\nALL TASKS BREAKDOWN TABLE:")
    print(f"{'ID':<11} | {'Type':<12} | {'Dur(AI+Hum)':<12} | {'ES':<5} | {'EF':<5} | {'LS':<5} | {'LF':<5} | {'Slack':<5} | {'Critical?'}")
    print("-" * 85)
    for t in tasks.values():
        crit_str = "YES (CRIT)" if t.is_critical else "No"
        dur_str = f"{t.total_duration:.1f}h ({t.duration_ai_h:.1f}+{t.duration_human_h:.1f})"
        print(f"{t.id:<11} | {t.ticket_type:<12} | {dur_str:<12} | {t.es:<5.1f} | {t.ef:<5.1f} | {t.ls:<5.1f} | {t.lf:<5.1f} | {t.slack:<5.1f} | {crit_str}")


if __name__ == "__main__":
    main()
