
import sqlite3
import re


def unidades():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''SELECT * FROM unidades''')
    unidades = cur.fetchall()
    cur.close()
    con.close()
    return unidades


def ultimos_agregados(tabla: str) -> [(), ()]:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT  rowid, * FROM {tabla}
                ORDER BY rowid DESC LIMIT 200''')
    resultado = cur.fetchall()
    cur.close()
    con.close()
    return resultado

# def no_procesados(tabla: str) -> [(), ()]:
#     con = sqlite3.connect("terranorte.db")
#     cur = con.cursor()
#     cur.execute(f'''SELECT  rowid, * FROM {tabla} WHERE procesado=0
#                 ORDER BY fecha ''')
#     resultado = cur.fetchall()
#     cur.close()
#     con.close()
#     return resultado

def fechas_disponibles(tabla: str) -> [(), ()]:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f''' SELECT fecha FROM {tabla} ORDER BY fecha''')
    fechas = cur.fetchall()
    fechas = list(set([x[0][:7] for x in fechas])) # cut long dates or keep the original
    fechas.sort()
    cur.close()
    con.close()
    return fechas

def parse_propietario(propietario: str) -> [str, str, str]:
    edificio = re.findall('[0-9]+', propietario)[0]
    apartamento = re.findall('(?<=-)\\w+', propietario)[0]
    propietario = re.findall('(?<=-)[\\w\\s]+$', propietario)[0]
    return [edificio, apartamento, propietario]

# def procesar_recibo(formulario: dict[str, str]):
#     '''
#     Recibe formulario:  edificio, apartamento, fecha, concepto, 
#                         cuota_comun, cuota_edificio
#     '''
#     cuota_comun = int(formulario['cuota_comun'])
#     cuota_edificio = int(formulario['cuota_edificio'])
#     saldo = cuota_comun + cuota_edificio
#     con = sqlite3.connect("terranorte.db")
#     cur = con.cursor()
#     try:
#         cur.execute(''' INSERT INTO recibos (   edificio,
#                                                 apartamento,
#                                                 fecha,
#                                                 concepto,
#                                                 cuota_comun,
#                                                 cuota_edificio,
#                                                 saldo  )
#                         VALUES (?,?,?,?,?,?,?)''', (  int(formulario['edificio']),
#                                                     formulario['apartamento'].lower(),
#                                                     formulario['fecha'], 
#                                                     formulario['concepto'],
#                                                     cuota_comun,
#                                                     cuota_edificio,
#                                                     saldo   ))
#     except sqlite3.Error as err:
#         match err.sqlite_errorcode:
#             case 2067:
#                 print('Recibo ya emitido en esa fecha')
#             case 275:
#                 print('Edificio o Apartamento no valido')
#         return 'Error'
#     else:
#         con.commit()
#         return 'Ok'
#     finally:
#         cur.close()
#         con.close()




def consultar_pagos(edificio: int = 0, apartamento: str = "", fecha: str = "") -> [(), ()]:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor() 
    if edificio and apartamento:
        sql = f'''SELECT rowid, * FROM pagos WHERE edificio = {
            edificio} AND apartamento = '{apartamento}' '''
    if fecha:
        sql = f'''SELECT rowid, * FROM pagos WHERE fecha LIKE '{fecha}%' '''
    cur.execute(sql)
    resultado = cur.fetchall()
    cur.close()
    con.close()
    return resultado

def almacenar_gasto(post: object) -> str:
    #         Form                             Tabla
    # fecha                          fecha           TEXT NOT NULL
    # concepto                       concepto        TEXT NOT NULL
    # referencia                     referencia      TEXT
    # monto                          gasto_bs        REAL DEFAULT 0.00
    # moneda (bolivar, dolar)        gasto_usd       INTEGER DEFAULT 0
    # fondo                          fondo           TEXT NOT NULL
    #                                procesado       INTEGER DEFAULT 0
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    match post.get('moneda'):
        case 'bolivar':
            gasto_bs, gasto_usd = float(post.get('monto')), round(float(post.get('monto')) / float(post.get('tasa')))
        case 'dolar':
            gasto_usd, gasto_bs = int(post.get('monto')), 0.00
        case _:
            gasto_bs = 0.0
            gasto_usd = 0
    try:
        cur.execute(f'''INSERT   INTO gastos (fecha, concepto, referencia, gasto_bs, gasto_usd, fondo)
                                VALUES (   '{post.get('fecha')}',
                                            '{post.get('concepto')}',
                                            '{post.get('referencia')}',
                                            {gasto_bs},
                                            {gasto_usd},
                                            '{post.get('fondo')}' ) ''' )
        cur.execute(f'''SELECT {post.get('fondo')} FROM fondos''')
        fondo_monto = cur.fetchone()[0] # -> (fondo,)
        fondo_monto -= gasto_usd
        cur.execute(f"""UPDATE fondos SET {post.get('fondo')}={fondo_monto} """)
    except Exception as err:
        print(err)
        return 'Error'
    else:
        con.commit()
        return 'Ok'
    finally:
        cur.close()
        con.close()


def deuda_general():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()

    cur.execute('''SELECT recibos.edificio, recibos.apartamento, propietario, COUNT(fecha), SUM(monto) 
                FROM unidades 
                JOIN recibos ON (unidades.edificio, unidades.apartamento) = (recibos.edificio, recibos.apartamento) 
                WHERE pagado = False GROUP BY recibos.edificio, recibos.apartamento''')
    lista = cur.fetchall()
    cur.close()
    con.close()
    return lista  # lista de tuples
