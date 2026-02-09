from flask import Blueprint, render_template
education_bp = Blueprint('education_bp', __name__)
@education_bp.route('/education')
def education():
    return render_template('pages/education.html')
