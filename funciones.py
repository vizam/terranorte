import sqlite3, re


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
                ORDER BY rowid DESC LIMIT 10''')
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


def consultar_pagos(edificio: int = 0, apartamento: str = '', fecha: str = '') -> [(),()]:
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


def propietario_editar(post):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    datos = post
    cur.execute(f'''UPDATE unidades
                    SET     propietario =   '{datos.get('propietario')}',
                            correo =        '{datos.get('correo')}',
                            telefono =      '{datos.get('telefono')}',
                            cuota_comun =    {datos.get('cuota_comun')},
                            cuota_edificio = {datos.get('cuota_edificio')},
                            cuota_agua =     {datos.get('cuota_agua')},
                            cuota_otro =     {datos.get('cuota_otro')}
                    WHERE   edificio =      {datos.get('edificio')}
                    AND     apartamento =   '{datos.get('apartamento')}'  ''')
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
    cuota_edificio      cuota_edificio  NTEGER  NOT NULL
    cuota_agua          cuota_agua      INTEGER NOT NULL
    cuota_otro          cuota_otro      INTEGER NOT NULL
                        procesado       INTEGER NOT NULL DEFAULT 0
    '''
    # column procesado is not requiered while inserting
    ordenes_sql = '''INSERT INTO recibos (edificio,
                                        apartamento,
                                        fecha,
                                        concepto,
                                        cuota_comun,
                                        cuota_edificio,
                                        cuota_agua,
                                        cuota_otro)
                    VALUES (?,?,?,?,?,?,?,?)'''
    # None will throw sqlite error NOT NULL constrain for fecha
    #
    tuple_datos = (int((datos.get('edificio') or None)),
                   (datos.get('apartamento') or None),
                   (datos.get('fecha') or None),
                   (datos.get('concepto') or None),
                   int((datos.get('cuota_comun') or None)),
                   int((datos.get('cuota_edificio') or None)),
                   int((datos.get('cuota_agua') or None)),
                   int((datos.get('cuota_otro') or None)))
    #
    return (ordenes_sql, tuple_datos)


def procesar_recibos_mes(datos):
    # datos --> bottle Forms.Dictionary
    '''
    FORM:                               TABLE:
    mes (ano-mes)                       edificio    
    concepto                            apartamento 
    cuota_comun                         fecha           TEXT NOT NULL
    cuota_edificio                      concepto      
    cuota_agua                          cuota_comun     INTEGER NOT 
    cuota_otro                          cuota_edificio  INTEGER NOT 
                                        cuota_agua      INTEGER NOT 
                                        cuota_otro      INTEGER NOT 
                                        procesado       INTEGER DEFAULT 0
    '''
    campos_comunes = (datos['mes']+'-01', datos['concepto'],
                      int(datos['cuota_comun']), int(datos['cuota_edificio']),
                      int(datos['cuota_agua']), int(datos['cuota_otro']))
    valores = []
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(''' SELECT edificio, apartamento FROM unidades ''')
    propiedades = cur.fetchall()
    for x in propiedades:
        valores.append(x + campos_comunes)
    try:
        cur.executemany('''INSERT INTO recibos (edificio,
                                                apartamento,
                                                fecha,
                                                concepto,
                                                cuota_comun,
                                                cuota_edificio,
                                                cuota_agua,
                                                cuota_otro)
                    VALUES (?,?,?,?,?,?,?,?)''', valores)
        con.commit()
        cur.close()
        con.close()
        return 'Ok'
    except sqlite3.Error as error:
        cur.close()
        con.close()
        return 'Error'


def eliminar_recibo(numero):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(f'''DELETE FROM recibos WHERE rowid = {numero}''')
        con.commit()
        cur.close()
        con.close()
        return 'OK'
    except sqlite3.Error as error:
        cur.close()
        con.close()
        return 'Error'


def procesar_pago(datos):
    # datos --> bottle Forms.Dictionary
    '''
    FORM:                               TABLE:
    edificio                            edificio    
    apartamento                         apartamento 
    fecha                               fecha       NOT NULL
    referencia                          referencia  TEXT
    monto                               pago_bs     REAL
                                        pago_usd    REAL
                                        pago_total  REAL
    moneda  (radio) ?   bolivares       procesado   INTEGER NOT NULL DEFAULT 0
                        dolares  
    tasa    (hidden)
    '''
    pago_bs = 0.00
    pago_usd = 0.00
    pago_total = 0.00
    if datos.get('moneda') == 'bolivar':
        pago_bs = datos.get('monto') or 0.00
        pago_total = float(pago_bs) / float(datos.get('tasa'))
    else:
        pago_usd = pago_total = datos.get('monto')
    ordenes_sql = '''INSERT INTO pagos (edificio,
                                        apartamento,
                                        fecha,
                                        referencia,
                                        pago_bs,
                                        pago_usd,
                                        pago_total)
                    VALUES (?,?,?,?,?,?,?)'''
    # None will throw sqlite error NOT NULL constrain for fecha
    # Some values could be Null, meaning non identified
    tuple_datos = (datos.get('edificio') if datos.get('edificio') else None,
                   datos.get('apartamento') if datos.get(
                       'apartamento') else None,
                   datos.get('fecha') if datos.get('fecha') else None,
                   datos.get('referencia') if datos.get(
                       'referencia') else None,
                   pago_bs,
                   pago_usd,
                   pago_total)
    return (ordenes_sql, tuple_datos)


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
