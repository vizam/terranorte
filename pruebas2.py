import sqlite3

diccionario = {'datos': [(1, 'pba', 20), (16, 'pbc', 20)]}

con = sqlite3.connect('terranorte.db')
cur = con.cursor()
cur.execute('''select rowid, * from pagos where rowid=4 ''')
result = cur.fetchone()
cur.close()
con.close()
print(result)
