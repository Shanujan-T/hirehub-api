from flask import jsonify, request
from flask_jwt_extended import current_user

from app.extensions import db
from app.models import QuizAttempt, Skill, SkillQuiz, UserSkill
from app.models.user_model import NOTIFY_VIA_OPTIONS

PASS_THRESHOLD = 70


def update_notification_preferences():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    errors = []
    updates = {}

    if "notify_via" in data:
        channel = str(data.get("notify_via") or "").strip().lower()
        if channel not in NOTIFY_VIA_OPTIONS:
            errors.append(f"notify_via must be one of: {', '.join(NOTIFY_VIA_OPTIONS)}.")
        else:
            updates["notify_via"] = channel

    if "whatsapp_number" in data:
        raw = data.get("whatsapp_number")
        updates["whatsapp_number"] = (
            str(raw).strip() if raw not in (None, "") else None
        )

    if errors:
        return jsonify({"errors": errors}), 400

    if not updates:
        return jsonify({"error": "No valid fields to update."}), 400

    try:
        for key, value in updates.items():
            setattr(current_user, key, value)
        db.session.commit()
        return jsonify({
            "message": "Notification preferences updated.",
            "user": current_user.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500


def get_skill_quiz(skill_id):
    skill = db.session.get(Skill, skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404

    questions = SkillQuiz.query.filter_by(skill_id=skill_id).order_by(SkillQuiz.id).all()
    if not questions:
        return jsonify({"error": "No quiz available for this skill yet."}), 404

    return jsonify({
        "skill": skill.to_dict(),
        "questions": [q.to_public_dict() for q in questions],
    }), 200


def submit_skill_quiz(skill_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    skill = db.session.get(Skill, skill_id)
    if not skill:
        return jsonify({"error": "Skill not found."}), 404

    questions = SkillQuiz.query.filter_by(skill_id=skill_id).order_by(SkillQuiz.id).all()
    if not questions:
        return jsonify({"error": "No quiz available for this skill yet."}), 404

    answers = data.get("answers")
    if not isinstance(answers, list) or len(answers) != len(questions):
        return jsonify({
            "errors": [f"answers must be an array of {len(questions)} selected indices."],
        }), 400

    correct = 0
    for question, selected in zip(questions, answers):
        try:
            selected_index = int(selected)
        except (TypeError, ValueError):
            selected_index = -1
        if selected_index == question.correct_index:
            correct += 1

    score = round((correct / len(questions)) * 100)
    passed = score >= PASS_THRESHOLD

    user_skill = UserSkill.query.filter_by(
        user_id=current_user.id,
        skill_id=skill_id,
    ).first()
    if not user_skill:
        return jsonify({
            "error": "Add this skill to your profile before taking the quiz.",
        }), 400

    try:
        attempt = QuizAttempt(
            user_id=current_user.id,
            skill_id=skill_id,
            score=score,
            passed=passed,
        )
        db.session.add(attempt)

        if passed:
            user_skill.verified = True
            user_skill.verified_by = None

        db.session.commit()
        return jsonify({
            "message": "Quiz submitted successfully.",
            "score": score,
            "passed": passed,
            "pass_threshold": PASS_THRESHOLD,
            "correct_count": correct,
            "total_questions": len(questions),
            "user_skill": user_skill.to_dict(),
            "attempt": attempt.to_dict(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "An internal server error occurred."}), 500
