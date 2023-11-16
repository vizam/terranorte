import sqlite3
# import re

# propiedad = '16-pba'
# patron_1 = '\d+'
# patron_2 = '[^\d-]+'
# edificio = re.findall(patron_1, propiedad)
# apartamento = re.findall(patron_2, propiedad)
# print(edificio)
# print(apartamento)

con = sqlite3.connect("terranorte.db")
cur = con.cursor()
cur.execute('''SELECT           recibos.edificio,
                                recibos.apartamento,
                                unidades.propietario,
                                COUNT(recibos.fecha),
                                SUM(recibos.cuota_comun),
                                SUM(recibos.cuota_edificio),
                                SUM(recibos.cuota_agua),
                                SUM(recibos.cuota_otro)
                FROM recibos
                INNER JOIN unidades ON recibos.edificio = unidades.edificio AND recibos.apartamento = unidades.apartamento
                WHERE recibos.procesado = 0
                GROUP BY recibos.edificio, recibos.apartamento
                 ''')
# cur.execute('''SELECT           edificio,
#                                apartamento,
#                                fecha,
#                                cuota_comun,
#                                cuota_edificio,
#                                 cuota_agua,
#                                 cuota_otro
#                  FROM recibos
                 
#                   ''')
datos = cur.fetchall()
print(datos)
print(len(datos))
cur.close()
con.close()


