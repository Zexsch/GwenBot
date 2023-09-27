import sqlite3

class Database():
    def create_db(self) -> None:
        """Try to create the Database tables each time the bot runs."""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            try:
                cur.execute('CREATE TABLE Subs(id INTEGER PRIMARY KEY, user_id INTEGER, server_id INTEGER)')
                cur.execute('CREATE TABLE Blacklist(id INTEGER PRIMARY KEY, user_id INTEGER, server_id INTEGER)')
                cur.execute('CREATE TABLE Quote(id INTEGER PRIMARY KEY, server_id INTEGER)')
            except sqlite3.OperationalError:
                print('eee')
                pass

    def fetch_gwen_sub(self, user_id: int, server_id: int) -> bool:
        """Return True if user is subbed, else return False"""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM Subs WHERE user_id=? AND server_id=?',(user_id,server_id)).fetchall()
            
            return True if res else False
    
    def fetch_blacklist(self, user_id: int, server_id: int) -> bool:
        """Return True if user is blacklisted, else return False"""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM Blacklist WHERE user_id=? AND server_id=?',(user_id, server_id)).fetchall()
            
            return True if res else False
        
    def fetch_quote(self, server_id: int) -> bool:
        """Return True if server uses quote, else return False"""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM Quote WHERE server_id=?',(server_id,)).fetchall()
            
            return True if res else False
        
    def _fetch_entire_blacklist(self):
        """Return everything from Blacklist table."""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            return cur.execute('SELECT * FROM Blacklist').fetchall()
    
    def _fetch_all_subs(self):
        """Return everything from Subs table."""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            return cur.execute('SELECT * FROM Subs').fetchall()
    
    def add_to_gwen_sub(self, user_id: int, server_id: int) -> None:
        """Add user to the subscribed user database"""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            cur.execute('INSERT INTO Subs(user_id, server_id) VALUES(?,?)', (user_id, server_id))
        
    def add_to_blacklist(self, user_id: int, server_id: int) -> None:
        """Add user to the blacklist."""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            cur.execute('INSERT INTO Blacklist(user_id, server_id) VALUES(?,?)', (user_id, server_id))
            
    def add_to_quote(self, server_id: int) -> None:
        """Add server to quote"""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            cur.execute('INSERT INTO Quote(server_id) VALUES(?)', (server_id,))
     
    def remove_from_gwen_sub(self, user_id: int, server_id: int) -> bool:
        """Remove user from GwenBot subscription. Return true if successfull else false."""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            
            res = cur.execute('SELECT * FROM Subs WHERE user_id=? AND server_id=?', (user_id, server_id)).fetchall()
            if res:
                cur.execute('DELETE FROM Subs WHERE user_id=? AND server_id=?', (user_id, server_id))
                return True
            else:
                return False
    
    def remove_from_blacklist(self, user_id: int, server_id: int) -> None:
        """Remove user from the blacklist."""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            
            cur.execute('DELETE FROM Blacklist WHERE user_id=? AND server_id=?', (user_id, server_id))
            
    def remove_from_quote(self, server_id: int) -> None:
        """Remove server from quote"""
        
        with sqlite3.connect('GwenUsers') as con:
            cur = con.cursor()
            cur.execute('DELETE FROM Quote WHERE server_id=?', (server_id,))
