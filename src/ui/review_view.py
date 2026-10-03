"""Human-readable presentation of completed guard reports."""


def headline(decision):
    if decision['reason_code'] == 'PERMISSION_REVOKED':
        return 'Not used: permission revoked'
    if decision['kind'] == 'withheld':
        return 'Ask for permission before using this record'
    if decision['guard_verdict'] == 'ESCALATE':
        return 'Allergy: confirm ingredients and cross-contact with the preparer'
    if decision['guard_verdict'] == 'VERIFY_EXTERNAL':
        return 'Check current preparation with the preparer'
    if decision['memory_action'] == 'ASK':
        return 'Ask your friend before applying this preference'
    if decision['memory_action'] == 'USE':
        return 'Preference applies: request a change or choose another dish'
    if 'WEEKDAY_OUT_OF_SCOPE' in decision['observations']:
        return 'Preference does not apply on this meal date'
    if 'SUPERSEDED' in decision['reason_code']:
        return 'An updated record replaces this preference'
    return 'No relevant ingredient detected; this is not clearance'


def show_report(screen, report, lines):
    screen.say(screen.t('\nMenu review'), 'title')
    screen.say(f"{report['friend']} | Meal date {report['meal_date']}")
    mode = report['extraction_mode']
    screen.say(screen.t('Synthetic canned demo; no AI ran.') if mode == 'canned-demo' else
               (screen.t('Validated cached extraction: ') + report['model'] if mode == 'local-ollama-cached-extraction' else
               (screen.t('Local model: ') + report['model'] if report['model'] else screen.t('Permission withheld; no AI ran.'))))
    screen.paragraph(report['notice'])
    # Persistent allergy warning even when no ingredient was detected.
    for d in report['decisions']:
        if d['guard_verdict'] == 'ESCALATE':
            screen.say(screen.t('\n! ') + screen.t(headline(d)), 'warn')
            screen.paragraph(d['memory'])
    for line in lines:
        screen.say('\n' + line['line_id'], 'title')
        screen.paragraph(line['text'])
        relevant = [d for d in report['decisions'] if any(c['line_id'] == line['line_id'] for c in d['candidates'])]
        if not relevant:
            screen.paragraph(screen.t('No matching note detected for this line. Missing ingredients and cross-contact are not checked.'))
        for d in relevant:
            screen.paragraph(screen.t(headline(d)) + screen.t(': ') + d['memory'])
    screen.say(screen.t('\nNotes for this meal'), 'title')
    for d in report['decisions']:
        screen.paragraph(d['memory_id'] + screen.t(' | ') + screen.t(headline(d)))
    screen.say(screen.t('Use preferences to confirm, edit or revoke a note; details shows the rule trace.'))
