import sqlite3
import re
from bottle import template, route, request, run, redirect, static_file
from funciones import procesar_recibo, procesar_recibos_mes, eliminar_recibo, \
    procesar_pago, unidades_todos, propietario_editar, \
    ultimos_agregados, fechas_todas, fecha_periodo, parse_propietario, \
    consultar_pagos


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
def recibos(operacion=''):
    ultimos = ultimos_agregados('recibos')
    return template('recibos_ingresar.html', ultimos=ultimos)


@route('/recibos/almacenar', method='POST')
def recibo_individual():
    # argumentos (sql, tuple)
    caller = request.headers.get('Referer')
    argumentos = procesar_recibo(request.POST)
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(argumentos[0], argumentos[1])
        con.commit()
        cur.close()
        con.close()
        redirect(caller+'/Ok')
    except sqlite3.Error as error:
        cur.close()
        con.close()
        redirect(caller+'/Error')


@route('/recibos/eliminar/<numero>', method='GET')
def eliminar(numero):
    resultado = eliminar_recibo(numero)
    redirect(request.headers.get('Referer'))


@route('/recibos/consultar', method='GET')
@route('/recibos/consultar/<operacion>', method='GET')
def recibos_editar_propitario(operacion=''):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    propietarios = unidades_todos()  # for select input
    fechas = fechas_todas('recibos')
    monto = 0
    tabla = []
    edificio = apartamento = propietario = ''
    if request.query_string:
        if request.query.get('propietario'):
            propietario = parse_propietario(request.query.get('propietario'))
            edificio = int(propietario[0])
            apartamento = propietario[1]
            propietario = propietario[2]
            cur.execute(f'''SELECT rowid, * FROM recibos
                            WHERE edificio={edificio}
                            AND apartamento='{apartamento}'
                            AND procesado = 0 ''')
            tabla = cur.fetchall()
            cur.execute(f'''SELECT SUM(cuota_comun), SUM(cuota_edificio), SUM(cuota_agua), SUM(cuota_otro)
                            FROM recibos
                            WHERE edificio={edificio} AND apartamento = '{apartamento}' AND procesado = 0 ''')
            montos = cur.fetchall()
            monto = (montos[0][0] or 0) + (montos[0][1] or 0) + \
                (montos[0][2] or 0) + (montos[0][3] or 0)
        elif request.query.get('ano_mes'):
            cur.execute(f''' SELECT rowid, * FROM recibos
                            WHERE fecha LIKE '{request.query.get('ano_mes')}%' 
                            AND procesado = 0 ''')
            tabla = cur.fetchall()
    cur.close()
    con.close()
    return template('recibos_consultar.html', edificio=edificio, \
                    apartamento=apartamento, propietario=propietario, monto=monto, \
                    tabla=tabla, fechas = fechas, propietarios=propietarios)



@route('/recibos/editar', method='POST')
def recibos_editar():
    datos = request.POST
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''UPDATE recibos SET  concepto =          '{datos.get('concepto')}',
                                        cuota_comun =       {datos.get('cuota_comun')},
                                        cuota_edificio =    {datos.get('cuota_edificio')},
                                        cuota_agua =        {datos.get('cuota_agua')},
                                        cuota_otro =        {datos.get('cuota_otro')}
                    WHERE rowid = {datos.get('rowid')}  ''')
    con.commit()
    cur.close()
    con.close()
    redirect(request.headers.get('Referer'))
    # return redirect(f"/recibos/editar/Ok?propietario={datos.get('edificio')}-{datos.get('apartamento')}-{datos.get('propietario')}")


@route('/recibos/mes', method='GET')
@route('/recibos/mes/<operacion>', method='GET')
def recibo_masivo(operacion = ''):
    recibos = []
    ano_mes = ''
    fechas = fechas_todas('recibos')
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    if request.query_string:
        ano_mes = request.query.get('ano_mes')
        cur.execute(f''' SELECT rowid, edificio, apartamento, fecha, cuota_comun, cuota_edificio,
                                cuota_agua, cuota_otro 
                        FROM recibos 
                        WHERE procesado=0 AND fecha LIKE '{ano_mes}%'  ''')
        recibos = cur.fetchall()
        cur.close()
        con.close()
    return template('recibos_mes.html', recibos = recibos, fechas = fechas, operacion = operacion, ano_mes = ano_mes)


@route('/recibos/almacenar/mes', method='POST')
def almacenar_mes():
    resultado = procesar_recibos_mes(request.POST)
    if resultado == 'Ok':
        return redirect('/recibos/mes/Ok')
    else:
        return redirect('/recibos/mes/Error')


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
    # Table: pagos....edificio, apartamento, fecha, referencia, pago_bs, pago_usd, pago_total, procesado
    # This selection is rowid, * (Total 9 values)
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
        cur.close()
        con.close()
        redirect('/pagos/Ok')
    except sqlite3.Error as error:
        cur.close()
        con.close()
        redirect('/pagos/Error')


@route('/pagos/eliminar/<rowid>', method='GET')
def eliminar_pago(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''DELETE FROM pagos WHERE rowid=?''', rowid)
    con.commit()
    cur.close()
    con.close()
    redirect('/pagos/Ok')




@route('/reportes/general', method='GET')
def recibos(operacion=""):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''SELECT   SUM(cuota_comun),
                            SUM(cuota_edificio),
                            SUM(cuota_agua),
                            SUM(cuota_otro)
                    FROM recibos ''')
    montos = cur.fetchall()
    deuda = int((montos[0][0] or 0) + (montos[0][1] or 0) +
                (montos[0][2] or 0) + (montos[0][3] or 0))
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
    return template('recibos.html', datos_tabla=datos_tabla, operacion=operacion, deuda=deuda)    


run(host='localhost', port=8080, debug=True)  # , reloader=True)
