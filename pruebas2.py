import sqlite3

#diccionario = {'datos': [(1, 'pba', 20), (16, 'pbc', 20)]}

con = sqlite3.connect('terranorte.db')
cur = con.cursor()
cur.execute('''select rowid, * from recibos where rowid IN (1, 2, 1632, 1633) ''')
result = cur.fetchall()
cur.close()
con.close()
print(result)
