# import sqlite3

# con = sqlite3.connect("terranorte.db")
# cur = con.cursor()
# cur.execute('''select rowid,* from recibos where rowid IN ()''')
# result = cur.fetchall()
# print(result)

x = "1,2"
y = x.split(',') # lista
print(y)

lista = ['1','2','0']



tupla = (1,2,3)
listanueva = list(tupla)
print(listanueva)
print(','.join([str(x) for x in tupla]))
