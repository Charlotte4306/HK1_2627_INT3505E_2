from flask import Flask

from models import Author, Book, Category, Review, User, db
from routes.books import bp as books_bp

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
app.json.ensure_ascii = False

db.init_app(app)
app.register_blueprint(books_bp)

def seed_data():
    if db.session.query(Book).count() > 0:
        return
    tech = Category(name="Công nghệ", slug="tech")
    novel = Category(name="Tiểu thuyết", slug="novel")

    martin = Author(name="Robert C. Martin", bio="Tác giả Clean Code")
    fowler = Author(name="Martin Fowler", bio="Tác giả Refactoring")
    nam_cao = Author(name="Nam Cao", bio="Nhà văn hiện thực")

    clean_code = Book(title="Clean Code", isbn="9780132350884", price_vnd=450000,
                      stock=10, category=tech, authors=[martin])
    refactoring = Book(title="Refactoring", isbn="9780134757599", price_vnd=520000,
                       stock=0, category=tech, authors=[fowler])
    chi_pheo = Book(title="Chí Phèo", isbn="9786049691234", price_vnd=60000,
                    stock=25, category=novel, authors=[nam_cao])
    lao_hac = Book(title="Lão Hạc", isbn="9786049691241", price_vnd=60000,
                   stock=12, category=novel, authors=[nam_cao])
    doi_thua = Book(title="Đời thừa", isbn="9786049691258", price_vnd=45000,
                    stock=8, category=novel, authors=[nam_cao])
    clean_arch = Book(title="Clean Architecture", isbn="9780134494166", price_vnd=450000,
                      stock=5, category=tech, authors=[martin])
    
    user = User(email="an@example.com", display_name="An")
    review = Review(rating=5, book=clean_code, user=user)
    
    db.session.add_all([tech, novel, martin, fowler, nam_cao, clean_code, refactoring, chi_pheo, lao_hac, doi_thua, clean_arch, user, review])
    db.session.commit()
    
with app.app_context():
    db.create_all()
    seed_data()
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)