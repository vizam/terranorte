import sqlite3
import re
from bottle import template, route, request, run, redirect, static_file
from funciones import procesar_recibo, procesar_recibos_mes, eliminar_recibo, \
    procesar_pago, unidades_todos, propietario_editar, \
    ultimos_agregados, fechas_todas, fecha_periodo, parse_propietario, \
    consultar_pagos, almacenar_gasto, aplicar_pagos


@route('/', method='GET')
def entrada():
    return 'Hola'


@route('/static/js/<filename>')
def server_static(filename):
    return static_file(filename, root='./static/js')


@route('/propietarios', method='GET')
@route('/propietarios/<operacion>', method='GET')
def listado(operacion=''):
    unidades = unidades_todos()
    return template('propietarios.html', unidades=unidades, operacion=operacion)


@route('/propietarios/editar/<edificio>/<apartamento>', method='POST')
def actualizar_propietario(edificio='', apartamento=''):
    respuesta = propietario_editar(request.POST)
    return redirect(f'/propietarios/{respuesta}')


@route('/recibos/ingresar', method='GET')
@route('/recibos/ingresar/<operacion>', method='GET')
def recibos_ingresar(operacion=''):
    ultimos = ultimos_agregados('recibos')
    return template('recibos_ingresar.html', ultimos=ultimos)

# intended for single invoice


@route('/recibos/almacenar', method='POST')
def recibo_individual():
    # caller = request.headers.get('Referer') # type: ignore
    resultado = procesar_recibo(request.POST)
    if resultado == 'Error':
        redirect('/recibos/ingresar/Error')
    else:
        redirect('/recibos/ingresar/Ok')


@route('/recibos/eliminar/<numero>', method='GET')
def eliminar(numero):
    resultado = eliminar_recibo(numero)
    redirect(request.headers.get('Referer'))


@route('/recibos/consultar', method='GET')
@route('/recibos/consultar/<operacion>', method='GET')
def recibos_editar_propietario(operacion=''):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    propietarios = unidades_todos()  # for select input
    fechas = fechas_todas('recibos')
    monto = 0
    tabla = []
    edificio = apartamento = propietario = ''
    if request.query_string:
        if request.query.get('propietario'):
            propietario = parse_propietario(request.query['propietario'])
            edificio = int(propietario[0])
            apartamento = propietario[1]
            propietario = propietario[2]
            cur.execute(f'''SELECT rowid, * FROM recibos
                            WHERE edificio={edificio}
                            AND apartamento='{apartamento}'
                            AND saldo > 0 ''')
            tabla = cur.fetchall()
            cur.execute(f'''SELECT SUM(cuota_comun), SUM(cuota_edificio)
                            FROM recibos
                            WHERE edificio={edificio} AND apartamento = '{apartamento}' AND saldo > 0 ''')
            # result is a list with one tuple of two elements, could be [(None, None)]
            cuotas = cur.fetchall()
            monto += (cuotas[0][0] or 0) + (cuotas[0][1] or 0)
        elif request.query['ano_mes']:
            cur.execute(f''' SELECT rowid, * FROM recibos
                            WHERE fecha LIKE '{request.query['ano_mes']}%'
                            AND saldo > 0 ''')
            tabla = cur.fetchall()
    cur.close()
    con.close()
    return template('recibos_consultar.html', edificio=edificio,
                    apartamento=apartamento, propietario=propietario, monto=monto,
                    tabla=tabla, fechas=fechas, propietarios=propietarios)


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
                    WHERE rowid = {datos['rowid']}  ''')
    con.commit()
    cur.close()
    con.close()
    redirect(request.headers.get('Referer'))
    # return redirect(f"/recibos/editar/Ok?propietario={datos.get('edificio')}-{datos.get('apartamento')}-{datos.get('propietario')}")


@route('/recibos/mes', method='GET')
@route('/recibos/mes/<operacion>', method='GET')
def recibo_masivo(operacion=''):
    recibos = []
    ano_mes = ''
    fechas = fechas_todas('recibos')
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    if request.query_string:
        ano_mes = request.query.get('ano_mes')
        # edificio, apartamento, fecha, concepto, cuota_comun, cuota_edificio, saldo
        cur.execute(f'''SELECT rowid, *
                        FROM recibos
                        WHERE fecha LIKE '{ano_mes}%'  ''')
        recibos = cur.fetchall()
        cur.close()
        con.close()
    return template('recibos_mes.html', recibos=recibos, fechas=fechas, operacion=operacion, ano_mes=ano_mes)


@route('/recibos/almacenar/mes', method='POST')
def almacenar_mes():
    match procesar_recibos_mes(request.POST):
        case ('Ok', periodo):
            redirect(f"/recibos/mes/Ok?ano_mes={periodo}")
        case 'Error':
            redirect('/recibos/mes/Error')


@route('/recibos/eliminar/mes/<ano_mes>', method='GET')
def recibos_eliminar_mes(ano_mes=''):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f''' DELETE FROM recibos WHERE fecha LIKE '{ano_mes}%' ''')
    con.commit()
    cur.close()
    con.close()
    return redirect('/recibos/mes/OK')


# template to enter new pago
@route('/pagos', method='GET')
@route('/pagos/<operacion>', method='GET')
def pago(operacion=''):
    # Table: pagos....edificio, apartamento, fecha, referencia, pago_bs, pago_usd, saldo
    ultimos = ultimos_agregados('pagos')
    return template('pagos.html', ultimos=ultimos, operacion=operacion)


@route('/pagos/consultar', method="GET")
def pagos():
    fechas_disponibles = fechas_todas('pagos')
    propietarios = unidades_todos()
    if request.query_string:
        if request.query.get('propietario'):
            datos_propietario = parse_propietario(
                request.query.get('propietario'))
            # parse and extract data from 'edificio-apartamento-propietario' in select value
            # return [edificio: str ,apartamento: str, nombre: str]
            datos_tabla = consultar_pagos(
                int(datos_propietario[0]), datos_propietario[1])
        if request.query.get('ano_mes'):
            # query LIKE 'yyyy-mm%'
            datos_tabla = consultar_pagos(fecha=request.query.get('ano_mes'))
        return template('pagos_consultar.html', propietarios=propietarios, fechas=fechas_disponibles, datos_tabla=datos_tabla)
    return template('pagos_consultar.html', propietarios=propietarios, fechas=fechas_disponibles, datos_tabla='')


@route('/pagos/almacenar', method='POST')
def registrar_pago():
    # argumentos (sql, tuple)
    argumentos = procesar_pago(request.POST)
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(argumentos[0], argumentos[1])
        con.commit()
    except Exception as err:
        print(err)
        redirect('/pagos/Error')
    else:
        redirect('/pagos/Ok')
    finally:
        cur.close()
        con.close()


@route('/pagos/eliminar/<rowid>', method='GET')
def eliminar_pago(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(
        f'''DELETE FROM pagos WHERE rowid={rowid} AND procesado=0 ''')
    con.commit()
    cur.close()
    con.close()
    redirect('/pagos/Ok')


@route('/pagos/aplicar', method='GET')
def pagos_aplicar():
    pagos_con_saldo = ""
    pago_aplicado = request.query.get('pago') or ""
    recibos_aplicados = request.query.get('recibos') or ""
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f"""SELECT rowid, edificio, apartamento, fecha, saldo
                    FROM pagos
                    WHERE saldo > 0""")
    pagos_con_saldo = cur.fetchall()
    if pago_aplicado:
        cur.execute(f''' SELECT rowid,fecha,saldo FROM pagos WHERE rowid={pago_aplicado} ''')
        pago_aplicado = cur.fetchone()
    if recibos_aplicados:
        # IN clause require tuple
        recibos_aplicados = tuple(recibos_aplicados.split(','))
        cur.execute(
            f'''SELECT rowid,fecha,concepto, saldo FROM recibos WHERE rowid IN {recibos_aplicados} ''')
        recibos_aplicados = cur.fetchall()
    cur.close()
    con.close()
    return template('pagos_aplicar.html', pagos_con_saldo=pagos_con_saldo, pago_aplicado=pago_aplicado, recibos_aplicados=recibos_aplicados)


@route('/pagos/aplicar/<pago_id>', method='GET')
def pagos_aplicar(pago_id=''):
    recibos = ""
    if pago_id:
        recibos_procesados = aplicar_pagos(pago_id)  # [rowid,... ]
        recibos = ','.join(recibos_procesados)
        redirect(f"/pagos/aplicar?pago={pago_id}&recibos={recibos}")
    redirect('/pagos/aplicar')


@route('/gastos', method='GET')
@route('/gastos/<operacion>', method='GET')
def definir_gastos(operacion=''):
    fondos = ['comun', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7',
              'e8', 'e9', 'e10', 'e11', 'e12', 'e13', 'e14', 'e15', 'e16']
    ultimos = ultimos_agregados('gastos')
    return template('gastos.html', fondos=fondos, operacion=operacion, ultimos=ultimos)


@route('/gastos/almacenar', method='POST')
def gastos():
    resultado = almacenar_gasto(request.POST)
    redirect(f'/gastos/{resultado}')


@route('/gastos/eliminar/<rowid>', method='GET')
def eliminar_gasto(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''DELETE FROM gastos WHERE rowid=? AND procesado=0''', rowid)
    con.commit()
    cur.close()
    con.close()
    redirect('/gastos/Ok')


@route('/reportes/general', method='GET')
def recibos(operacion=""):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''SELECT   SUM(cuota_comun),
                            SUM(cuota_edificio),
                            SUM(cuota_agua),
                            SUM(cuota_otro)
                    FROM recibos ''')
    cuotas = cur.fetchall()
    deuda = int((cuotas[0][0] or 0) + (cuotas[0][1] or 0) +
                (cuotas[0][2] or 0) + (cuotas[0][3] or 0))
    cur.execute('''SELECT recibos.edificio, recibos.apartamento, unidades.propietario,
                        COUNT(recibos.fecha),  SUM(recibos.cuota_comun), SUM(recibos.cuota_edificio),
                        SUM(recibos.cuota_agua), SUM(recibos.cuota_otro)
                        FROM recibos
                        INNER JOIN unidades ON recibos.edificio = unidades.edificio AND recibos.apartamento = unidades.apartamento
                        WHERE recibos.procesado = 0
                        GROUP BY recibos.edificio, recibos.apartamento ''')
    datos_tabla = cur.fetchall()
    cur.close()
    con.close()
    return template('reportes_recibos.html', datos_tabla=datos_tabla, operacion=operacion, deuda=deuda)


run(host='localhost', port=8080, debug=True)  # , reloader=True)
