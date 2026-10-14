from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String, Text

db = SQLAlchemy()
class BookAuthor(db.Model):
    __tablename__ = "book_authors"
    book_id = mapped_column(ForeignKey("books.id"),
                            primary_key=True)
    author_id = mapped_column(ForeignKey("authors.id"),
                              primary_key=True)
    
class Category(db.Model):
    __tablename__ = "categories"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    slug = mapped_column(String(100), unique=True, nullable=False)
    books = relationship("Book", back_populates="category")
    
class Book(db.Model):
    __tablename__ = "books"
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(200), nullable=False)
    isbn = mapped_column(String(13), unique=True)
    price_vnd = mapped_column(Integer, default=0)
    stock = mapped_column(Integer, nullable=False)
    category_id = mapped_column(ForeignKey("categories.id"))
    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary="book_authors", back_populates="books")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    
    #Tạo book từ body JSON đã validate
    @classmethod
    def from_payload(cls, payload):
        book = cls(
            title=payload["title"],
            isbn=payload.get("isbn"),
            price_vnd=payload["price_vnd"],
            stock=payload.get("stock", 0),
            category_id=payload.get("category_id"),
        )
        book.authors = [db.session.get(Author, author_id) for
                        author_id in payload.get("author_ids", [])]
        return book

    def to_dict(self):
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price": {
                "amount": self.price_vnd,
                "currency": "VND"
            },
            "inStock": self.stock > 0,
            "category": {
                "id": self.category.id,
                "slug": self.category.slug
            } if self.category else None,
            "authors": [{
                "id": author.id,
                "name": author.name
            } for author in self.authors]
        }

class Author(db.Model):
    __tablename__ = "authors"
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    bio = mapped_column(Text)
    books = relationship("Book", secondary="book_authors", back_populates="authors")
    
class User(db.Model):
    __tablename__ = "users"
    id = mapped_column(Integer, primary_key=True)
    email = mapped_column(String(120), unique=True, nullable=False)
    display_name = mapped_column(String(100))
    reviews = relationship("Review", back_populates="user")
    
class Review(db.Model):
    __tablename__ = "reviews"
    id = mapped_column(Integer, primary_key=True)
    rating = mapped_column(Integer, nullable=False)
    book_id = mapped_column(ForeignKey("books.id"), nullable=False)
    user_id = mapped_column(ForeignKey("users.id"), nullable=False)
    book = relationship("Book", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    