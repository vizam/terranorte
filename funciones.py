
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

def no_procesados(tabla: str) -> [(), ()]:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT  rowid, * FROM {tabla} WHERE procesado=0
                ORDER BY fecha ''')
    resultado = cur.fetchall()
    cur.close()
    con.close()
    return resultado

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
    '''
    FORM:                               TABLE:
    edificio            edificio        NOT NULL
    apartamento         apartamento     NOT NULL
    fecha               fecha           NOT NULL
    concepto            concepto        TEXT
    cuota_comun         cuota_comun     INTEGER NOT NULL
    cuota_edificio      cuota_edificio  INTEGER  NOT NULL
                        saldo           INTEGER NOT NULL
                        procesado       INTEGER NOT NULL DEFAULT 0
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
                                                    datos['apartamento'].lower(),
                                                    datos['fecha'], 
                                                    datos['concepto'],
                                                    cuota_comun,
                                                    cuota_edificio,
                                                    saldo   ))
    except Exception as err:
        print(err)
        return 'Error'
    else:
        con.commit()
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
                                        pago_saldo           INTEGER DEFAULT 0
    '''
    cuota_comun = int(datos['cuota_comun'])
    cuota_edificio = int(datos['cuota_edificio'])
    pago_saldo = cuota_comun + cuota_edificio
    campos_comunes = (  datos['mes'],
                        datos['concepto'],
                        cuota_comun,
                        cuota_edificio,
                        pago_saldo       )
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
                                                pago_saldo)
                    VALUES (?,?,?,?,?,?,?)''', valores)
        con.commit()
    except Exception as err:
        print(err)
        return 'Error'
    else:
        return ("Ok")
    finally:
        cur.close()
        con.close()

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

def procesar_pago(datos):
    # datos --> bottle Forms.Dictionary
    '''
    FORM:                               TABLE:
    edificio                            edificio    INTEGER
    apartamento                         apartamento TEXT
    fecha                               fecha       NOT NULL
    referencia                          referencia  TEXT
    monto                               pago_bs     REAL NOT NULL DEFAULT 0.0
                                        pago_usd    INTEGER NOT NULL
                                        saldo       INTEGER NOT NULL
                                        procesado   INTEGER NOT NULL DEFAULT 0
    moneda  (radio) ?   bolivares       
                        dolares  
    tasa    (hidden)
    '''
    match datos.get('moneda'):
        case 'bolivar':
            pago_bs = float(datos.get('monto'))
            pago_usd = saldo = round(pago_bs / float(datos.get('tasa')))
        case 'dolar':
            pago_bs = 0.0
            pago_usd = saldo = int(datos.get('monto'))
    valores = (     datos.get('edificio'),              
                    datos.get('apartamento').lower(), 
                    datos.get('fecha'), 
                    datos.get('referencia'), 
                    pago_bs,
                    pago_usd,
                    saldo   )
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute('''   INSERT INTO pagos ( edificio,
                                                apartamento,
                                                fecha,
                                                referencia,
                                                pago_bs,
                                                pago_usd,
                                                saldo       )
                            VALUES (?,?,?,?,?,?,?)  ''', valores)
    except Exception as err:
        print(err)
        return 'Error'
    else:
        con.commit()
    finally:
        cur.close()
        con.close()
    return 'Ok'

def aplicar_pago(pago_id: int) -> [str,] or []:
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f''' SELECT edificio, apartamento, saldo FROM pagos
                    WHERE rowid={pago_id} ''')
    pago = cur.fetchone() # (...) or None
    edificio = pago[0]
    apartamento = pago[1]
    pago_saldo = pago[2]
    recibos_lista = [] # [(saldo, rowid), (...)]
    cur.execute(f''' SELECT rowid, saldo FROM recibos
                    WHERE edificio={edificio} AND apartamento='{apartamento}' AND saldo > 0 ''')
    recibos = cur.fetchall() # [(...)...]
    if recibos and pago_saldo:  # recibos con saldo > 0, pago con saldo > 0
        for recibo in recibos: # (...)
            recibo_saldo = recibo[1]
            if pago_saldo > recibo_saldo:
                recibos_lista.append((0, recibo[0])) # (saldo, rowid) order matters for UPDATE placeholders
                pago_saldo = pago_saldo - recibo_saldo
            elif pago_saldo < recibo_saldo:
                recibos_lista.append((recibo_saldo - pago_saldo, recibo[0]))
                pago_saldo = 0
                break
            else:
                recibos_lista.append((0, recibo[0]))
                pago_saldo = 0
                break
        cur.execute(f'''UPDATE pagos SET saldo={pago_saldo}, procesado=1
                        WHERE rowid={pago_id} ''')
        cur.executemany(''' UPDATE recibos SET saldo=?, procesado=1 WHERE rowid=?''', recibos_lista)
        ## preparing data for fondos
        recibos_alfondo = [recibo[1] for recibo in recibos_lista if recibo[0] == 0] # [(saldo, rowid)] ->  [rowid, *]
        if len(recibos_alfondo) == 1 : recibos_alfondo.append(0) # IN clause require tuple without final comma
        recibos_alfondo = tuple(recibos_alfondo) # (1,2,...)
        cur.execute(f'''SELECT edificio, cuota_comun, cuota_edificio FROM recibos WHERE rowid IN {recibos_alfondo}''')
        recibos_alfondo = cur.fetchall() # shadowing previous variable
        for recibo in recibos_alfondo:
            recibo_edificio = recibo[0]
            cuota_comun = recibo[1]
            cuota_edificio = recibo[2]
            cur.execute(f'''SELECT comun, e{recibo_edificio} FROM fondos''')
            fondos = cur.fetchone() # could be None, recibos_alfondo could have 0 as last record
            fondo_comun = fondos[0]
            fondo_edificio = fondos[1]
            fondo_comun += cuota_comun
            fondo_edificio += cuota_edificio
            cur.execute(f'''UPDATE fondos SET comun={fondo_comun}, e{recibo_edificio}={fondo_edificio} ''')
        con.commit()
    ret = [str(x[1]) for x in recibos_lista]  
    if len(ret) == 1 : ret.append(0) # IN clause wont work with a single element tuple
    cur.close()
    con.close()
    return ret

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
