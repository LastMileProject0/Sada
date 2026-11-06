"""Reviewed acceptance data ONLY. Never used to generate/replace an answer.

These two snapshots must continue to match the existing approved local KB.
Unknown paraphrases/claims are deliberately outside the hackathon scope.
"""
PASSAGES = {
    'SRC-01-E01': {
        'source_id': 'SRC-01',
        'source_title': 'Common Alerting Protocol (CAP) Version 1.2',
        'section': '§3.2.2 info / instruction (OPTIONAL)',
        'official_url': 'https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html',
        'locator': 'Official HTML; §3.2.2 info / instruction (OPTIONAL)',
        'text': 'The text describing the recommended action to be taken by recipients of the alert message (OPTIONAL)',
        'claims': {
            'cap.content': {
                'en': 'This passage describes the content of the CAP instruction field',
                'ar': 'تصف هذه الفقرة محتوى حقل instruction في معيار CAP',
            },
            'cap.recipient_action': {
                'en': 'The passage describes text about an action for recipients of an alert message',
                'ar': 'تصف الفقرة نصًا عن إجراء موجّه إلى متلقي رسالة التنبيه',
            },
        },
    },
    'SRC-02-E01': {
        'source_id': 'SRC-02',
        'source_title': 'ITU-T Y.3172 — Architectural framework for machine learning in future networks including IMT-2020',
        'section': 'Summary',
        'official_url': 'https://www.itu.int/rec/T-REC-Y.3172-201906-I/en',
        'locator': 'PDF page 3; Summary',
        'text': 'ITU-T Y.3172 specifies an architectural framework for machine learning (ML) in future networks including IMT-2020.',
        'claims': {
            'itu.scope': {
                'en': 'ITU-T Y.3172 describes a machine-learning architecture for future networks, including IMT-2020',
                'ar': 'يصف ITU-T Y.3172 إطارًا معماريًا للتعلم الآلي في شبكات المستقبل، بما فيها IMT-2020',
            },
        },
    },
}
