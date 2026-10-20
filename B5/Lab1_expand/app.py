from flask import Flask

from models import Author, Book, Category, Review, User, db
from routes.books import bp as books_bp

def seed_data():
    if db.session.query(Book).count() > 0:
        return
    tech = Category(name="Công nghệ", slug="tech")
    novel = Category(name="Tiểu thuyết", slug="novel")

    martin = Author(name="Robert C. Martin", bio="Tác giả Clean Code")
    fowler = Author(name="Martin Fowler", bio="Tác giả Refactoring")
    gamma = Author(name="Erich Gamma", bio="Đồng tác giả Design Patterns")
    hunt = Author(name="Andrew Hunt", bio="Đồng tác giả The Pragmatic Programmer")
    nam_cao = Author(name="Nam Cao", bio="Nhà văn hiện thực")
    vtp = Author(name="Vũ Trọng Phụng", bio="Nhà văn hiện thực trào phúng")
    to_hoai = Author(name="Tô Hoài", bio="Nhà văn")

    clean_code = Book(title="Clean Code", isbn="9780132350884", price_vnd=450000,
                      stock=10, category=tech, authors=[martin])
    refactoring = Book(title="Refactoring", isbn="9780134757599", price_vnd=520000,
                       stock=0, category=tech, authors=[fowler])
    chi_pheo = Book(title="Chí Phèo", isbn="9786049691234", price_vnd=60000,
                    stock=25, category=novel, authors=[nam_cao])
    #Thêm sách có giá trùng nhau để test sort nhiều cột
    clean_arch = Book(title="Clean Architecture", isbn="9780134494166", price_vnd=450000,
                      stock=5, category=tech, authors=[martin])
    design_patterns = Book(title="Design Patterns", isbn="9780201633610", price_vnd=520000,
                           stock=3, category=tech, authors=[gamma])
    pragmatic = Book(title="The Pragmatic Programmer", isbn="9780135957059", price_vnd=380000,
                     stock=7, category=tech, authors=[hunt])
    so_do = Book(title="Số Đỏ", isbn="9786049691235", price_vnd=75000,
                 stock=12, category=novel, authors=[vtp])
    de_men = Book(title="Dế Mèn Phiêu Lưu Ký", isbn="9786049691236", price_vnd=60000,
                  stock=0, category=novel, authors=[to_hoai])

    user = User(email="an@example.com", display_name="An")
    review = Review(rating=5, book=clean_code, user=user)

    db.session.add_all([tech, novel, martin, fowler, gamma, hunt, nam_cao, vtp, to_hoai,
                        clean_code, refactoring, chi_pheo, clean_arch, design_patterns,
                        pragmatic, so_do, de_men, user, review])
    db.session.commit()
    
def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
    if config:
        app.config.update(config)
    app.json.ensure_ascii = False

    db.init_app(app)
    app.register_blueprint(books_bp)

    with app.app_context():
        db.create_all()
        seed_data()
    return app
        
if __name__ == "__main__":
    create_app().run(port=5000, debug=True)