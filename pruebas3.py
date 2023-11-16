import sqlite3


con = sqlite3.connect("terranorte.db")
cur = con.cursor()

# cur.execute('''SELECT recibos.edificio,
#                 recibos.apartamento,
#                 unidades.propietario,
#                 COUNT(recibos.fecha),
#                 SUM(recibos.cuota_comun),
#                 SUM(recibos.cuota_edificio),
#                 SUM(recibos.cuota_agua),
#                 SUM(recibos.cuota_otro)
#                 FROM recibos
#                 INNER JOIN unidades ON recibos.edificio = unidades.edificio AND recibos.apartamento =
#                 unidades.apartamento
#                 WHERE recibos.procesado = 0
#                 GROUP BY recibos.edificio, recibos.apartamento
#                 ''')
# datos = cur.fetchall()


# cur.execute('''SELECT edificio,
#                 apartamento,
#                 COUNT(fecha),
#                 SUM(cuota_comun)
#                 FROM recibos
#                 GROUP BY edificio, apartamento ''')
# datos = cur.fetchall()

cur.execute('''SELECT SUM(cuota_comun)
                FROM recibos
                ''')
datos = cur.fetchall()

print(datos)