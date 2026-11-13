"""Compute current evidence status without claiming human acceptance."""


def report_status(verification, validation):
    automated = verification.get('automated_status', 'MISSING')
    accepted = validation.get('status', 'MISSING')
    return {
        'automated_status': automated,
        'agent_validation': accepted,
        'technical_gate': 'GO' if automated == accepted == 'PASS' else 'REVISE',
        'validation_actor': 'Codex (delegated by user)',
        'human_validation': 'NOT_PERFORMED',
    }
