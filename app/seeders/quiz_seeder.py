"""Seed skill self-assessment quizzes for demo skills."""

from app import create_app
from app.extensions import db
from app.models import Skill, SkillQuiz


QUIZ_DATA = [
    {
        "skill_names": ["Python", "python"],
        "questions": [
            {
                "question": "Which keyword defines a function in Python?",
                "options": ["func", "def", "function", "lambda only"],
                "correct_index": 1,
            },
            {
                "question": "What is the output type of len([1, 2, 3])?",
                "options": ["list", "int", "str", "tuple"],
                "correct_index": 1,
            },
            {
                "question": "Which structure is best for key-value pairs?",
                "options": ["list", "set", "dict", "tuple"],
                "correct_index": 2,
            },
        ],
    },
    {
        "skill_names": ["SQL", "MySQL", "mysql"],
        "questions": [
            {
                "question": "Which clause filters rows after grouping?",
                "options": ["WHERE", "HAVING", "ORDER BY", "LIMIT"],
                "correct_index": 1,
            },
            {
                "question": "Which command removes all rows but keeps the table structure?",
                "options": ["DROP", "DELETE", "TRUNCATE", "REMOVE"],
                "correct_index": 2,
            },
            {
                "question": "PRIMARY KEY ensures what?",
                "options": ["Sorted rows", "Unique identifiable rows", "Encrypted data", "Foreign links only"],
                "correct_index": 1,
            },
        ],
    },
    {
        "skill_names": ["Communication", "communication"],
        "questions": [
            {
                "question": "Active listening mainly involves:",
                "options": ["Waiting to speak", "Reflecting and confirming understanding", "Interrupting politely", "Taking notes only"],
                "correct_index": 1,
            },
            {
                "question": "In professional email, the subject line should be:",
                "options": ["Blank", "Clear and specific", "All caps", "A joke"],
                "correct_index": 1,
            },
            {
                "question": "Non-verbal communication includes:",
                "options": ["Only written text", "Body language and tone", "Database queries", "Spreadsheet formulas"],
                "correct_index": 1,
            },
        ],
    },
    {
        "skill_names": ["Excel", "Microsoft Excel", "excel"],
        "questions": [
            {
                "question": "Which function sums a range of cells?",
                "options": ["COUNT", "SUM", "AVG", "MAXIF"],
                "correct_index": 1,
            },
            {
                "question": "A cell reference like $A$1 is called:",
                "options": ["Relative", "Absolute", "Dynamic", "Volatile"],
                "correct_index": 1,
            },
            {
                "question": "Which feature quickly summarizes data by category?",
                "options": ["VLOOKUP", "Pivot Table", "Conditional Format only", "Text to Columns"],
                "correct_index": 1,
            },
        ],
    },
]


def _find_skill(names):
    for name in names:
        skill = Skill.query.filter(Skill.name.ilike(name)).first()
        if skill:
            return skill
    return None


def seed_skill_quizzes():
    app = create_app()
    with app.app_context():
        created = 0
        for bundle in QUIZ_DATA:
            skill = _find_skill(bundle["skill_names"])
            if not skill:
                print(f"  Skipped quiz (skill not found): {bundle['skill_names'][0]}")
                continue

            existing = SkillQuiz.query.filter_by(skill_id=skill.id).count()
            if existing:
                continue

            for item in bundle["questions"]:
                db.session.add(
                    SkillQuiz(
                        skill_id=skill.id,
                        question=item["question"],
                        options=item["options"],
                        correct_index=item["correct_index"],
                    )
                )
                created += 1

        db.session.commit()
        print(f"Skill quizzes seeded ({created} questions).")
        return 0


if __name__ == "__main__":
    raise SystemExit(seed_skill_quizzes())
