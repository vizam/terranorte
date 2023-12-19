import sqlite3
import re
from bottle import template, route, request, run, redirect, static_file
from bottle_flash2 import FlashPlugin
from funciones import procesar_recibo, procesar_recibos_mes, \
    procesar_pago, unidades, propietario_editar, \
    ultimos_agregados, fechas_disponibles, parse_propietario, \
    consultar_pagos, almacenar_gasto, aplicar_pago, no_procesados



@route('/', method='GET')
def entrada():
    return 'Hola'


@route('/static/js/<filename>')
def server_static(filename):
    return static_file(filename, root='./static/js')

@route('/static/css/<filename>')
def server_static(filename):
    return static_file(filename, root='./static/css')



@route('/propietarios', method='GET')
@route('/propietarios/<operacion>', method='GET')
def listado(operacion=''):
    propietarios = unidades()
    return template('propietarios.html', propietarios=propietarios, operacion=operacion)


@route('/propietarios/editar/<edificio>/<apartamento>', method='POST')
def actualizar_propietario(edificio='', apartamento=''):
    respuesta = propietario_editar(request.POST)
    return redirect(f'/propietarios/{respuesta}')


@route('/recibos/generar', method='GET')
@route('/recibos/generar/<operacion>', method='GET')
def recibos_ingresar(operacion=''):
    ultimos = ultimos_agregados('recibos')
    return template('recibos_generar.html', ultimos=ultimos)


@route('/recibo/almacenar', method='POST')
def recibo_individual():
    resultado = procesar_recibo(request.POST)
    redirect(f'/recibos/generar/{resultado}')


@route('/recibos/consultar', method='GET')
@route('/recibos/consultar/<operacion>', method='GET')
def recibos_editar_propietario(operacion=''):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    propietarios = unidades()  # for select input
    fechas = fechas_disponibles('recibos')  # for select input
    monto = 0   # for owner debt in case select goes for 'propietario'
    tabla = []  # empty for empty value
    # getter yield value or None, no Exception
    propietario = request.query.get('propietario') or ""
    ano_mes = request.query.get('ano_mes') or ""
    edificio = apartamento = ""
    if propietario:
        propietario = parse_propietario(request.query['propietario'])
        edificio = int(propietario[0])
        apartamento = propietario[1]
        propietario = propietario[2]
        cur.execute(f'''SELECT rowid, * FROM recibos
                        WHERE edificio={edificio}
                        AND apartamento='{apartamento}'
                        AND saldo > 0 ''')
        tabla = cur.fetchall()
        cur.execute(f'''SELECT SUM(saldo) FROM recibos
                        WHERE edificio={edificio} AND apartamento = '{apartamento}' AND saldo > 0 ''')
        # result is a list with one tuple of one elements, could be [(None, )]
        saldo = cur.fetchone()  # (saldo,)
        print(saldo)
        monto = saldo[0] if saldo else 0
    elif ano_mes:
        cur.execute(f''' SELECT rowid, * FROM recibos
                        WHERE fecha LIKE '{request.query['ano_mes']}%'
                        AND saldo > 0 ''')
        tabla = cur.fetchall()
    cur.close()
    con.close()
    return template('recibos_consultar.html', edificio=edificio,
                    apartamento=apartamento, propietario=propietario, monto=monto,
                    tabla=tabla, fechas=fechas, ano_mes=ano_mes, propietarios=propietarios)


@route('/recibos/eliminar/<id_or_period>', method='GET')
def eliminar(id_or_period):
    if '-' not in id_or_period:
        sql = f"DELETE FROM recibos WHERE rowid = {
            id_or_period} AND procesado=0"
    else:
        sql = f"DELETE FROM recibos WHERE fecha LIKE '{
            id_or_period}%' AND procesado=0"
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(sql)
    con.commit()
    if '-' in id_or_period:  # identifies masive delete, is better redirect without query string, giving some malfunction
        redirect(request.headers.get('Referer'))
    else:
        redirect(request.headers.get('Referer'))


@route('/recibos/editar', method='POST')
def recibos_editar():
    datos = request.POST
    concepto = datos['concepto']
    cuota_comun = int(datos['cuota_comun'])
    cuota_edificio = int(datos['cuota_edificio'])
    saldo = cuota_comun + cuota_edificio
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''UPDATE recibos SET  concepto = '{concepto}',
                                        cuota_comun = {cuota_comun},
                                        cuota_edificio = {cuota_edificio},
                                        saldo = {saldo}
                    WHERE rowid = {datos['rowid']}  and PROCESADO=0''')
    con.commit()
    cur.close()
    con.close()
    redirect(request.headers.get('Referer'))


@route('/recibos/almacenar/mes', method='POST')
def almacenar_mes():
    resultado = procesar_recibos_mes(request.POST)
    redirect(f"/recibos/generar/{resultado}")


@route('/pagos/ingresar', method='GET')
@route('/pagos/ingresar/<operacion>', method='GET')
def pago(operacion=''):
    ultimos = ultimos_agregados('pagos')
    return template('pagos_ingresar.html', ultimos=ultimos, operacion=operacion)


@route('/pagos/almacenar', method='POST')
def registrar_pago():
    # argumentos (sql, tuple)
    resultado = procesar_pago(request.POST)
    match resultado:
        case 'Ok':
            redirect('/pagos/ingresar/Ok')
        case 'Error':
            redirect('/pagos/ingresar/Error')


@route('/pagos/consultar', method="GET")
def pagos():
    propietarios = unidades()
    fechas = fechas_disponibles('pagos')
    datos_tabla = ""
    if request.query.get('propietario'):
        datos_propietario = parse_propietario(request.query.get('propietario'))
        # parse and extract data from 'edificio-apartamento-propietario' in select value
        # return [edificio: str ,apartamento: str, nombre: str]
        datos_tabla = consultar_pagos(
            int(datos_propietario[0]), datos_propietario[1])
    if request.query.get('ano_mes'):
        datos_tabla = consultar_pagos(fecha=request.query.get('ano_mes'))
    return template('pagos_consultar.html', propietarios=propietarios, fechas=fechas, datos_tabla=datos_tabla)


@route('/pagos/eliminar/<rowid>', method='GET')
def eliminar_pago(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(
        f'''DELETE FROM pagos WHERE rowid={rowid} AND procesado=0 ''')
    con.commit()
    cur.close()
    con.close()
    redirect(request.headers.get('Referer'))


@route('/pago/identificar', method='POST')
def identificar_pago():
    post = request.POST
    if post.get('rowid') and post.get('edificio') and post.get('apartamento'):
        con = sqlite3.connect("terranorte.db")
        cur = con.cursor()
        cur.execute(f'''UPDATE pagos SET edificio={post.get('edificio')},
                                        apartamento='{post.get('apartamento')}'
                        WHERE rowid={post.get('rowid')}
                        AND edificio='' and apartamento='' ''')
        con.commit()
        cur.close()
        con.close()
        redirect(request.headers.get("Referer"))


@route('/pagos/aplicar', method='GET')
@route('/pagos/aplicar/<pago_id>', method='GET')
def pagos_aplicar(pago_id=0):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    pago = ""
    recibos = ""
    if pago_id:
        # (rowid,... ) or () # IN clause require parenthesis (tuple without final comma)
        recibos_procesados = tuple(aplicar_pago(pago_id))
        cur.execute(
            f'''SELECT rowid,fecha, pago_usd, saldo 
                FROM pagos WHERE rowid={pago_id} ''')
        pago = cur.fetchone()
        cur.execute(
            f'''SELECT rowid,fecha, concepto, saldo 
                FROM recibos WHERE rowid IN {recibos_procesados} ''')
        recibos = cur.fetchall()
    cur.execute(f"""SELECT rowid, edificio, apartamento, fecha, pago_usd, saldo
                    FROM pagos
                    WHERE saldo > 0 AND edificio != '' AND apartamento != '' """)
    pagos_con_saldo = cur.fetchall()
    cur.close()
    con.close()
    return template('pagos_aplicar.html', pagos_con_saldo=pagos_con_saldo, pago=pago, recibos=recibos)


@route('/gastos/ingresar', method='GET')
@route('/gastos/ingresar/<operacion>', method='GET')
def definir_gastos(operacion=''):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''SELECT * FROM fondos''')
    columnas = cur.description
    montos = cur.fetchone()
    cur.close()
    con.close()
    # [(columna, monto), ...]
    fondos = [x for x in map(lambda x, y: (x[0], y), columnas, montos)]
    gastos = no_procesados('gastos')
    return template('gastos_ingresar.html', fondos=fondos, operacion=operacion, gastos=gastos)


@route('/gastos/almacenar', method='POST')
def gastos():
    resultado = almacenar_gasto(request.POST)
    redirect(f'/gastos/ingresar/{resultado}')


@route('/gastos/cerrar', method='GET')
def cerrar_mes():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''UPDATE gastos SET procesado=1 WHERE procesado=0''')
    con.commit()
    cur.close()
    con.close()
    redirect('/gastos/ingresar')


@route('/gastos/eliminar/<rowid>', method='GET')
def eliminar_gasto(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT gasto_usd, fondo FROM gastos WHERE rowid={
                rowid} AND procesado=0''')
    gasto = cur.fetchone()  # tuple of two if any, or None
    gasto_usd = gasto[0]  # int
    fondo = gasto[1]  # str
    cur.execute(f'''SELECT {fondo} FROM fondos''')  # (int,)
    fondo_monto = cur.fetchone()[0]  # int
    fondo_monto += gasto_usd
    cur.execute(f'''UPDATE fondos SET {fondo}={fondo_monto} ''')
    cur.execute(f'''DELETE FROM gastos WHERE rowid={rowid} AND procesado=0''')
    con.commit()
    cur.close()
    con.close()
    redirect('/gastos/ingresar')


@route('/gastos/consultar')
def consultar_gastos():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    # cur.execute('''SELECT fecha FROM gastos''')
    # fechas = cur.fetchall() # -> [(fecha,)...]
    # fechas = set([x[0][:7] for x in fechas])
    # print(fechas)
    fechas = fechas_disponibles('gastos')
    if request.query.get('ano_mes'):
        ano_mes = request.query.get('ano_mes')
        cur.execute(
            f'''SELECT rowid,* FROM gastos WHERE procesado=1 AND fecha LIKE '{ano_mes}%' ''')
        gastos = cur.fetchall()
        print(gastos)
    else:
        gastos = ""
    cur.close()
    con.close()
    return template('gastos_consultar.html', fechas=fechas, gastos=gastos)


@route('/reporte/morosidad', method='GET')
def morosidad(operacion=""):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(''' SELECT SUM(saldo)
                    FROM recibos 
                    WHERE saldo > 0''')
    deuda = cur.fetchone()[0] or 0 # (suma,) can be (None,)
    cur.execute('''SELECT recibos.edificio, recibos.apartamento, unidades.propietario,
                        COUNT(recibos.fecha),  SUM(recibos.saldo)
                        FROM recibos
                        INNER JOIN unidades 
                        ON recibos.edificio = unidades.edificio AND recibos.apartamento = unidades.apartamento
                        WHERE recibos.saldo > 0
                        GROUP BY recibos.edificio, recibos.apartamento ''')
    datos_tabla = cur.fetchall()
    cur.close()
    con.close()
    return template('reporte_morosidad.html', datos_tabla=datos_tabla, operacion=operacion, deuda=deuda)


@route('/reporte/balance/bsd', method='GET')
@route('/reporte/balance/bsd/<resultado>', method='GET')
def balance():
    fechas = fechas_disponibles('gastos')
    ano_mes = request.query.get('ano_mes')
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT fecha, edificio, apartamento, referencia, pago_bs
                    FROM pagos
                    WHERE pago_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''')
    pagos = cur.fetchall()
    pagos_balance = [(x[0], str(x[1]) + '-' + x[2], x[3], 0.0, x[4])
                     for x in pagos]
    cur.execute(f'''SELECT SUM(pago_bs)
                    FROM pagos
                    WHERE pago_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''')
    creditos = cur.fetchone()[0] or 0 # (value,) value can be None
    # print(pagos_balance)
    cur.execute(f'''SELECT fecha, concepto, referencia, gasto_bs FROM gastos
                    WHERE gasto_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''')
    gastos = cur.fetchall()
    gastos_balance = [(x[0], x[1], x[2], x[3], 0.0) for x in gastos]
    cur.execute(f'''SELECT SUM(gasto_bs)
                    FROM gastos
                    WHERE gasto_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''')
    debitos = cur.fetchone()[0] or 0
    # print(gastos_balance)
    cur.close()
    con.close()
    # 5 elements
    balance = pagos_balance + gastos_balance
    balance.sort()
    # print(balance)
    return template('reporte_balanceBsD.html', fechas=fechas, balance=balance, debitos=debitos, creditos=creditos)


@route('/reporte/balance/usd', method='GET')
@route('/reporte/balance/usd/<ano_mes>', method='GET')
def balance(ano_mes=''):
    fechas = fechas_disponibles('gastos')
    ano_mes = request.query.get('ano_mes')
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT fecha, edificio, apartamento, referencia, pago_usd
                    FROM pagos
                    WHERE pago_bs = 0.0 AND fecha LIKE '{ano_mes}%' ''')
    pagos = cur.fetchall()
    pagos_balance = [(x[0], str(x[1]) + '-' + x[2], x[3], 0.0, x[4])
                     for x in pagos]
    # print(pagos_balance)
    cur.execute(f'''SELECT SUM(pago_usd)
                    FROM pagos
                    WHERE pago_bs = 0 AND fecha LIKE '{ano_mes}%' ''')
    creditos = cur.fetchone()[0] or 0 # (value,) value can be None
    cur.execute(f'''SELECT fecha, concepto, referencia, gasto_usd
                    FROM gastos
                    WHERE gasto_bs = 0 AND fecha LIKE '{ano_mes}%' ''')
    gastos = cur.fetchall()
    gastos_balance = [(x[0], x[1], x[2], x[3], 0.0) for x in gastos]
    # print(gastos_balance)
    cur.execute(f'''SELECT SUM(gasto_usd)
                    FROM gastos
                    WHERE gasto_bs = 0 AND fecha LIKE '{ano_mes}%' ''')
    debitos = cur.fetchone()[0] or 0
    cur.close()
    con.close()
    # 5 elements
    balance = pagos_balance + gastos_balance
    balance.sort()
    # print(balance)
    return template('reporte_balanceUSD.html', fechas=fechas, balance=balance, debitos = debitos, creditos = creditos)


run(host='localhost', port=8080, debug=True)  # , reloader=True)
