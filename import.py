from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from dotenv import load_dotenv
import csv
import os


BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "IMPORT")

load_dotenv(os.path.join(BASE_DIR, 'credentials.env'))
x = os.environ.get('DATABASE_URL')
engine = create_engine(os.environ.get('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

create_authors_query = "CREATE TABLE IF NOT EXISTS authors(" \
                       "author_id SERIAL PRIMARY KEY, author VARCHAR (50) UNIQUE);"
db.execute(create_authors_query)
# db.commit()
create_books_query = "CREATE TABLE IF NOT EXISTS books(" \
                     "isbn VARCHAR(20) PRIMARY KEY, " \
                     "title VARCHAR(30), year integer, " \
                     "author_id INTEGER REFERENCES authors (author_id));"
db.execute(create_books_query)

with open("../project1/books.csv") as f:
    reader = csv.reader(f)
    header = next(reader)
#     # authors_list = []
#     # for i in reader:
#     #     authors_list.append(i[2])
#     # unique_authors = set(authors_list)
#     # for author in unique_authors:
#     #
    if db.execute("SELECT COUNT(*) FROM authors;").fetchone()[0] == 0 \
            or db.execute("SELECT COUNT(*) FROM books;").fetchone()[0] == 0:
        print('kklklklkk')
        for isbn, title, author, year in reader:
            db.execute("INSERT INTO authors (author) VALUES (:author) ON CONFLICT(author) DO UPDATE SET author=:author;",
                            {"author": author})
            db.execute("SELECT * FROM authors ORDER BY author_id;")
# db.commit()

        # db.execute('SELECT author_id FROM authors WHERE author=:author', {'author': author})
#         # db.execute(author_id_query)
#         # print(author_id_query)
#         # print(author_id_query[1])
# #         y= db.commit()
# #         print(author_id_query)
# #         x = db.execute('SELECT author_id FROM authors WHERE author=:author', {'author': author}).fetchone()[0]
# #         print(x)
            db.execute("INSERT INTO books (isbn, title, year, author_id) "
                    "VALUES (:isbn, :title, :year, :author_id)",
                    {"isbn": isbn, "title": title, "year": int(year), "author_id": db.execute('SELECT author_id FROM authors WHERE author=:author', {'author': author}).fetchone()[0]})
db.commit() # transactions are assumed, so close the transaction finished

