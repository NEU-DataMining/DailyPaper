import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS papers
                            (title TEXT PRIMARY KEY,
                            updated TEXT,
                            published TEXT,
                            pdf_url TEXT,
                            query TEXT,
                            doi TEXT,
                            authors TEXT,
                            journal_ref TEXT,
                            summary TEXT)''')
        self.conn.commit()

    def add_paper(self, paper_dict):
        search_dict = {'title': paper_dict['title']}
        existing_paper = self.search_paper(search_dict)
        if existing_paper:
            self.update_paper(paper_dict)
            return False
        else:
            self.cursor.execute('''INSERT INTO papers (title, updated, published, pdf_url, query, doi, authors, journal_ref, summary)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', tuple(paper_dict.values()))
            self.conn.commit()
            return True

    def delete_paper(self, title):
        self.cursor.execute('''DELETE FROM papers WHERE title = ?''', (title,))
        self.conn.commit()

    def update_paper(self, update_dict):
        title = update_dict['title']
        update_str = ', '.join([f'{key} = ?' for key in update_dict.keys()])
        update_values = tuple(update_dict.values()) + (title,)
        self.cursor.execute(f'''UPDATE papers SET {update_str} WHERE title = ?''', update_values)
        self.conn.commit()

    def search_paper(self, search_dict):
        search_str = ' AND '.join([f'{key} = ?' for key in search_dict.keys()])
        search_values = tuple(search_dict.values())
        self.cursor.execute(f'''SELECT * FROM papers WHERE {search_str}''', search_values)
        return self.cursor.fetchall()
    
    # 需要修改
    def delete_papers_by_date(self, date):
        self.cursor.execute('''DELETE FROM papers WHERE updated <= ?''', (date,))
        self.conn.commit()