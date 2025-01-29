from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///japanese_flashcards.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your-secret-key"  # 用於 flash 訊息

db = SQLAlchemy(app)


# 資料模型
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    words = db.relationship(
        "Word", backref="category", lazy=True, cascade="all, delete-orphan"
    )


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kanji = db.Column(db.String(50))  # 漢字
    furigana = db.Column(db.String(50))  # 假名
    meaning = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_ruby(self):
        """將漢字和假名配對，返回 (漢字, 假名) 的列表"""

        # 分割假名
        furigana_parts = self.furigana.split()
        # 分割漢字
        kanji_parts = self.kanji.split()

        # 確保兩者長度相同
        if len(furigana_parts) != len(kanji_parts):
            # 如果長度不同，返回整個字串作為一組
            return [(self.kanji, self.furigana)]

        return list(zip(kanji_parts, furigana_parts))


# 主頁面
@app.route("/")
def index():
    # 取得所有分類
    categories = Category.query.order_by(Category.created_at.desc()).all()
    return render_template("index.html", categories=categories)


# 新增類別
@app.route("/category/add", methods=["POST"])
def add_category():
    name = request.form.get("name")
    if name:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash("分類已新增", "success")
    return redirect(url_for("index"))


# 編輯類別
@app.route("/category/<int:id>/edit", methods=["GET", "POST"])
def edit_category(id):
    category = Category.query.get_or_404(id)
    if request.method == "POST":
        category.name = request.form.get("name")
        db.session.commit()
        flash("分類已更新", "success")
        return redirect(url_for("index"))
    return render_template("edit_category.html", category=category)


# 刪除類別
@app.route("/category/<int:id>/delete", methods=["POST"])
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash("分類已刪除", "success")
    return redirect(url_for("index"))


# 查看類別內容
@app.route("/category/<int:id>")
def view_category(id):
    category = Category.query.get_or_404(id)
    words = Word.query.filter_by(category_id=id).order_by(Word.created_at.desc()).all()
    return render_template("category.html", category=category, words=words)


# 更新筆記
@app.route("/category/<int:id>/notes", methods=["POST"])
def update_notes(id):
    category = Category.query.get_or_404(id)
    category.notes = request.form.get("notes", "")
    db.session.commit()
    return jsonify({"status": "success"})


# 新增/查詢單字
@app.route("/category/<int:id>/word/add", methods=["GET", "POST"])
def add_word(id):
    category = Category.query.get_or_404(id)
    if request.method == "POST":
        word = Word(
            kanji=request.form.get("kanji"),
            furigana=request.form.get("furigana"),
            meaning=request.form.get("meaning"),
            category_id=id,
        )
        db.session.add(word)
        db.session.commit()
        flash("單字已新增", "success")
        return redirect(url_for("view_category", id=id))
    return render_template("add_word.html", category=category)


# 編輯單字
@app.route("/word/<int:id>/edit", methods=["GET", "POST"])
def edit_word(id):
    word = Word.query.get_or_404(id)
    if request.method == "POST":
        word.kanji = request.form.get("kanji")
        word.furigana = request.form.get("furigana")
        word.meaning = request.form.get("meaning")
        db.session.commit()
        flash("單字已更新", "success")
        return redirect(url_for("view_category", id=word.category_id))
    return render_template("edit_word.html", word=word)


# 刪除單字
@app.route("/word/<int:id>/delete", methods=["POST"])
def delete_word(id):
    word = Word.query.get_or_404(id)
    category_id = word.category_id
    db.session.delete(word)
    db.session.commit()
    flash("單字已刪除", "success")
    return redirect(url_for("view_category", id=category_id))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
