import sqlite3
import re


def unidades_todos():
    # tabla unidades: edificio, apartamento, propietario, correo, telefono,
    #                cuota_comun, cuota_edificio, cuota_agua, cuota_otro, saldo
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
                ORDER BY rowid DESC LIMIT 30''')
    # if no record, return []
    resultado = cur.fetchall()
    cur.close()
    con.close()
    return resultado


def fecha_periodo(tabla: str) -> [(), ()]:
    pass


def fechas_todas(tabla: str) -> [(), ()]:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f''' SELECT DISTINCT fecha FROM {tabla} ORDER BY fecha''')
    fechas = cur.fetchall()
    cur.close()
    con.close()
    return fechas


def parse_propietario(propietario: str) -> [str, str, str]:
    edificio = re.findall('[0-9]+', propietario)[0]
    apartamento = re.findall('(?<=-)\\w+', propietario)[0]
    propietario = re.findall('(?<=-)[\\w\\s]+$', propietario)[0]
    return [edificio, apartamento, propietario]

def propietario_editar(post):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''UPDATE unidades
                    SET     propietario =   '{post.get('propietario')}',
                            correo =        '{post.get('correo')}',
                            telefono =      '{post.get('telefono')}'
                    WHERE   edificio =      {post.get('edificio')}
                    AND     apartamento =   '{post.get('apartamento')}'  ''')
    con.commit()
    cur.close()
    con.close()
    return 'OK'

def procesar_recibo(datos):
# datos --> bottle Forms.Dictionary
    '''
    FORM:                               TABLE:
    edificio            edificio        NOT NULL
    apartamento         apartamento     NOT NULL
    fecha               fecha           NOT NULL
    concepto            concepto
    cuota_comun         cuota_comun     INTEGER NOT NULL
    cuota_edificio      cuota_edificio  INTEGER  NOT NULL
                        saldo           INTEGER NOT NULL
    '''
    cuota_comun = int(datos['cuota_comun'])
    cuota_edificio = int(datos['cuota_edificio'])
    saldo = cuota_comun + cuota_edificio
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(''' INSERT INTO recibos (   edificio,
                                                apartamento,
                                                fecha,
                                                concepto,
                                                cuota_comun,
                                                cuota_edificio,
                                                saldo  )
                        VALUES (?,?,?,?,?,?,?)''', (  int(datos['edificio']),
                                                    datos['apartamento'],
                                                    datos['fecha'], # input type month
                                                    datos['concepto'],
                                                    cuota_comun,
                                                    cuota_edificio,
                                                    saldo   ))
        con.commit()
    except Exception as err:
        print(err)
        return 'Error'
    else:
        return 'Ok'
    finally:
        cur.close()
        con.close()


def procesar_recibos_mes(datos):
    # datos --> bottle Forms.Dictionary
    '''
    FORM:                               TABLE:
    mes (ano-mes)                       edificio    
    concepto                            apartamento 
    cuota_comun                         fecha           TEXT NOT NULL
    cuota_edificio                      concepto      
                                        cuota_comun     INTEGER NOT 
                                        cuota_edificio  INTEGER NOT 
                                        saldo           INTEGER DEFAULT 0
    '''
    cuota_comun = int(datos['cuota_comun'])
    cuota_edificio = int(datos['cuota_edificio'])
    saldo = cuota_comun + cuota_edificio
    campos_comunes = (  datos['mes'],
                        datos['concepto'],
                        cuota_comun,
                        cuota_edificio,
                        saldo       )
    valores = []
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(''' SELECT edificio, apartamento FROM unidades ''')
    propiedades = cur.fetchall()
    for x in propiedades:
        # tupple aritmetic --> new tuple
        valores.append(x + campos_comunes)
    try:
        cur.executemany('''INSERT INTO recibos (edificio,
                                                apartamento,
                                                fecha,
                                                concepto,
                                                cuota_comun,
                                                cuota_edificio,
                                                saldo)
                    VALUES (?,?,?,?,?,?,?)''', valores)
        con.commit()
    except Exception as err:
        print(err)
        return 'Error'
    else:
        return ("Ok", datos['mes'])
    finally:
        cur.close()
        con.close()


def eliminar_recibo(numero):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(f'''DELETE FROM recibos WHERE rowid = {numero}''')
        con.commit()
    except Exception as err:
        print(err)
        return 'Error'
    else:
        return 'OK'
    finally:
        cur.close()
        con.close()

def consultar_pagos(edificio: int = 0, apartamento: str = '', fecha: str = '') -> [(), ()]:
    if edificio and apartamento:
        con = sqlite3.connect("terranorte.db")
        cur = con.cursor()
        sql = f'''SELECT rowid, * FROM pagos WHERE edificio = {
            edificio} AND apartamento = '{apartamento}' '''
    if fecha:
        con = sqlite3.connect("terranorte.db")
        cur = con.cursor()
        sql = f'''SELECT rowid, * FROM pagos WHERE fecha LIKE '{fecha}%' '''
    cur.execute(sql)
    resultado = cur.fetchall()
    cur.close()
    con.close()
    return resultado

def procesar_pago(datos):
    # datos --> bottle Forms.Dictionary
    '''
    FORM:                               TABLE:
    edificio                            edificio    
    apartamento                         apartamento 
    fecha                               fecha       NOT NULL
    referencia                          referencia  TEXT
    monto                               pago_bs     REAL DEFAULT 0.0
                                        pago_usd    INTEGER DEFAULT 0
                                        saldo       INTEGER INTEGER NOT NULL
                                        procesado   INTEGER NOT NULL DEFAULT 0
     moneda  (radio) ?   bolivares       
                        dolares  
    tasa    (hidden)
    '''
    pago_bs = float(datos['monto'] if datos['moneda'] == 'bolivar' else 0.0)
    pago_usd = int(datos['monto'] if datos['moneda'] == 'dolar' else 0)
    # saldo need calculation 
    ordenes_sql = '''   INSERT INTO pagos ( edificio,
                                            apartamento,
                                            fecha,
                                            referencia,
                                            pago_bs,
                                            pago_usd,
                                            saldo       )
                        VALUES (?,?,?,?,?,?,?)        '''
    if datos.get('moneda') == 'bolivar':
        saldo = int(float(pago_bs) / float(datos['tasa']))
    else:
        saldo = int(pago_usd)
    # None will throw sqlite error NOT NULL constrain for fecha
    # Some values could be Null, meaning non identified
    tuple_datos = ( datos.get('edificio') or None,
                    datos.get('apartamento') or None, 
                    datos.get('fecha') or None, 
                    datos.get('referencia') or None, 
                    round(pago_bs, 2),
                    pago_usd,
                    saldo   )
    return (ordenes_sql, tuple_datos)

def aplicar_pagos(pago_id: int) -> [str,]:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f''' SELECT rowid, * FROM pagos
                    WHERE rowid={pago_id} ''')
    pago = cur.fetchone() # (...)
    edificio = pago[1]
    apartamento = pago[2]
    pago_saldo = pago[7]
    recibos_lista = [] # [(saldo, rowid), (...)]
    cur.execute(f''' SELECT rowid, * FROM recibos
                    WHERE edificio={edificio} AND apartamento='{apartamento}' AND saldo > 0 ''')
    recibos = cur.fetchall() # [(...)...]
    if recibos and pago_saldo:
        for recibo in recibos: # (...)
            if pago_saldo > recibo[7]:
                pago_saldo = pago_saldo - recibo[7]
                recibos_lista.append((0, recibo[0])) # (saldo, rowid) order matters for UPDATE placeholders
            elif recibo[7] > pago_saldo:
                recibos_lista.append((recibo[7] - pago_saldo, recibo[0]))
                pago_saldo = 0
                break
            else:
                pago_saldo = 0
                recibos_lista.append((0, recibo[0]))
                break
        cur.execute(f'''UPDATE pagos SET    saldo={pago_saldo},
                                            procesado=1
                        WHERE rowid={pago_id} ''')
        cur.executemany(''' UPDATE recibos SET saldo=?
                            WHERE rowid=?''', recibos_lista)
        con.commit()    
        ret = [str(x[1]) for x in recibos_lista]  
        if len(ret) % 2 != 0: ret.append(0) 
        cur.close()
        con.close()
        return ret
    return []

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
            gasto_bs, gasto_usd = post.get('monto'), 0
        case 'dolar':
            gasto_usd, gasto_bs = post.get('monto'), 0.00
    cur.execute(f'''INSERT   INTO gastos (fecha, concepto, referencia, gasto_bs, gasto_usd, fondo)
                             VALUES (   '{post.get('fecha')}',
                                        '{post.get('concepto')}',
                                        '{post.get('referencia')}',
                                        {float(gasto_bs)},{int(gasto_usd)},
                                        '{post.get('fondo')}' ) ''' )
    con.commit()
    cur.close()
    con.close()
    return 'Ok'


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
