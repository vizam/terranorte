import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for
from datetime import date
# from bottle import Bottle, template, request, redirect, static_file, install, response
# from bottle_flash2 import FlashPlugin
from funciones import unidades, ultimos_agregados, \
    fechas_disponibles, parse_propietario, \
    consultar_pagos


app = Flask(__name__)

app.config['SECRET_KEY'] = 'papupapa69'


@app.route('/', methods=['GET'])
def entrada():
    return '<h1>Hola Mundo</h1>'


# @app.route('/static/js/<filename>')
# def server_static(filename):
#     return static_file(filename, root='./static/js')

# @app.route('/static/css/<filename>')
# def server_static(filename):
#     return static_file(filename, root='./static/css')


@app.route('/listado', methods=['GET'])
def listado():
    propietarios = unidades()
    return render_template('listado.html', propietarios=propietarios)


@app.route('/listado/editar', methods=['POST'])
def listado_editar():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(f'''UPDATE unidades
                        SET     propietario =   '{request.form.get('propietario')}',
                                correo =        '{request.form.get('correo')}',
                                telefono =      '{request.form.get('telefono')}'
                        WHERE   edificio =      {request.form.get('edificio')}
                        AND     apartamento =   '{request.form.get('apartamento')}'  ''')
    except Exception as err:
        flash('Error al editar propietario', 'danger')
    else:
        con.commit()
        flash('Propietario editado con exito', 'success')
    finally:
        cur.close()
        con.close()
        return redirect(url_for('listado'))


@app.route('/recibos/generar', methods=['GET'])
def recibos_generar():
    ultimos = ultimos_agregados('recibos')
    return render_template('recibos_generar.html', ultimos=ultimos)


@app.route('/recibo/almacenar', methods=['POST'])
def recibo_almacenar():
    cuota_comun = int(request.form.get('cuota_comun'))
    cuota_edificio = int(request.form.get('cuota_edificio'))
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
                        VALUES (?,?,?,?,?,?,?)''', (int(request.form['edificio']),
                                                    request.form['apartamento'].lower(
        ),
            request.form['fecha'],
            request.form['concepto'],
            cuota_comun,
            cuota_edificio,
            saldo))
    except sqlite3.Error as err:
        match err.sqlite_errorcode:
            case 2067:
                flash('Error: recibo ya emitido en esa fecha', 'danger')
            case 275:
                flash('Error: revise: edificio, apartamento, montos', 'danger')
            case _:
                flash('Error no especificado...', 'danger')
    else:
        con.commit()
        flash('Recibo agregado con exito !', 'success')
    finally:
        cur.close()
        con.close()
        return redirect(request.headers.get('referer'))


@app.route('/recibos/almacenar', methods=['POST'])
def recibos_almacenar():
    cuota_comun = int(request.form.get('cuota_comun'))
    cuota_edificio = int(request.form.get('cuota_edificio'))
    saldo = cuota_comun + cuota_edificio
    campos_comunes = (request.form['mes'],
                      request.form['concepto'],
                      cuota_comun,
                      cuota_edificio,
                      saldo)
    valores = []
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(''' SELECT edificio, apartamento FROM unidades ''')
    propiedades = cur.fetchall()
    for propiedad in propiedades:
        # tupple aritmetic --> new tuple
        valores.append(propiedad + campos_comunes)
    try:
        cur.executemany('''INSERT INTO recibos (edificio,
                                                apartamento,
                                                fecha,
                                                concepto,
                                                cuota_comun,
                                                cuota_edificio,
                                                saldo)
                    VALUES (?,?,?,?,?,?,?)''', valores)
    except sqlite3.Error as err:
        match err.sqlite_errorcode:
            case 2067:
                flash('Recibos ya emitidos en ese periodo !', 'danger')
            case 275:
                flash('Error: revise: edificio, apartamento, montos', 'danger')
            case _:
                flash('Ha ocurrido un error', 'danger')
    else:
        con.commit()
        flash('Recibos emitidos con exito !', 'success')
    finally:
        cur.close()
        con.close()
        return redirect(request.headers.get('referer'))


@app.route('/recibos/eliminar/<id_or_period>', methods=['GET'])
def recibos_eliminar(id_or_period):
    if '-' not in id_or_period:
        sql = f"DELETE FROM recibos WHERE rowid = {
            id_or_period} AND procesado=0"
    else:
        sql = f"DELETE FROM recibos WHERE fecha LIKE '{
            id_or_period}%' AND procesado=0"
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(sql)
    except Exception as err:
        flash('Error al intentar borrar registro(s)', 'danger')
    else:
        con.commit()
        flash('Recibo(s) eliminado(s) con exito !', 'success')
    finally:
        cur.close()
        con.close()
        return redirect(request.headers.get('referer'))


@app.route('/recibos/consultar', methods=['GET'])
def recibos_consultar():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    propietarios = unidades()  # for select input
    fechas = fechas_disponibles('recibos')  # for select input
    deuda = 0   # for owner debt in case select goes for 'propietario'
    tabla = []  # empty for empty value
    # getter yield value or None, no Exception
    propietario = request.args.get('propietario')
    ano_mes = request.args.get('ano_mes')
    edificio = apartamento = ""
    if propietario:
        propietario = parse_propietario(request.args['propietario'])
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
        deuda = cur.fetchone()[0] or 0  # (saldo,)
    elif ano_mes:
        cur.execute(f''' SELECT rowid, * FROM recibos
                        WHERE fecha LIKE '{request.args['ano_mes']}%'
                        AND saldo > 0 ''')
        tabla = cur.fetchall()
    cur.close()
    con.close()
    return render_template('recibos_consultar.html', fechas=fechas, propietarios=propietarios,
                           edificio=edificio, apartamento=apartamento,
                           propietario=propietario, deuda=deuda,
                           tabla=tabla, ano_mes=ano_mes)


@app.route('/recibo/editar', methods=['POST'])
def recibo_editar():
    concepto = request.form['concepto']
    cuota_comun = int(request.form['cuota_comun'])
    cuota_edificio = int(request.form['cuota_edificio'])
    saldo = cuota_comun + cuota_edificio
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    try:
        cur.execute(f'''UPDATE recibos SET  concepto = '{concepto}',
                                            cuota_comun = {cuota_comun},
                                            cuota_edificio = {cuota_edificio},
                                            saldo = {saldo}
                        WHERE rowid = {request.form['rowid']}  and PROCESADO=0''')
    except sqlite3.Error as err:
        match err.sqlite_errorcode:
            case 275:
                flash('Error: revise montos', 'danger')
            case _:
                flash('Error no especificado...', 'danger')
    else:
        con.commit()
        flash('Recibo editado con exito !', 'success')
    finally:
        cur.close()
        con.close()
        return redirect(request.headers.get('referer'))

###
# PAGOS
###


@app.route('/pago/ingresar', methods=['GET'])
def pago_ingresar():
    ultimos = ultimos_agregados('pagos')
    return render_template('pago_ingresar.html', ultimos=ultimos)


@app.route('/pago/almacenar', methods=['POST'])
def pago_almacenar():
    match request.form.get('moneda'):
        case 'bolivar':
            pago_bs = float(request.form.get('monto'))
            pago_usd = saldo = round(
                pago_bs / float(request.form.get('tasa')))  # hidden field
        case 'dolar':
            pago_bs = 0.0
            pago_usd = saldo = int(request.form.get('monto'))
    valores = (request.form.get('edificio'),
               request.form.get('apartamento').lower(),
               request.form.get('fecha'),
               request.form.get('referencia'),
               pago_bs,
               pago_usd,
               saldo)
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
        flash('Se ha producido un error...', 'danger')
        print(err)
    else:
        con.commit()
        flash('Operacion realizada con exito...', 'success')
    finally:
        cur.close()
        con.close()
        return redirect(url_for('pago_ingresar'))


@app.route('/pago/eliminar/<rowid>', methods=['GET'])
def pago_eliminar(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(
        f'''DELETE FROM pagos WHERE rowid={rowid} AND procesado=0 ''')
    con.commit()
    cur.close()
    con.close()
    return redirect(request.headers.get('referer'))


@app.route('/pago/identificar', methods=['POST'])
def pago_identificar():
    rowid, edificio, apartamento = (request.form.get('rowid'),
                                    request.form.get('edificio'),
                                    request.form.get('apartamento'))
    if rowid and edificio and apartamento:
        con = sqlite3.connect("terranorte.db")
        cur = con.cursor()
        try:
            cur.execute(f'''UPDATE pagos SET edificio={edificio},
                                            apartamento='{apartamento}'
                            WHERE rowid={rowid}
                            AND edificio='' and apartamento=''
                            AND EXISTS (SELECT edificio, apartamento
                                        FROM unidades
                                        WHERE edificio={edificio}
                                        AND apartamento='{apartamento}'
                                        LIMIT 1 )''')
        except Exception as err:
            print(err)
            flash('Se ha producido un error...', 'danger')
        else:
            if cur.rowcount == 0:
                flash('No se logro identificar pago !', 'warning')
            else:
                con.commit()
                flash('Operacion realizada con exito', 'success')
        finally:
            cur.close()
            con.close()
            return redirect(request.headers.get("referer"))


@app.route('/pagos/consultar', methods=["GET"])
def pagos_consultar():
    propietarios = unidades()
    fechas = fechas_disponibles('pagos')
    datos_tabla = ""
    if request.args.get('propietario'):
        datos_propietario = parse_propietario(request.args.get('propietario'))
        # parse and extract data from 'edificio-apartamento-propietario' in select value
        # return [edificio: str ,apartamento: str, nombre: str]
        datos_tabla = consultar_pagos(
            int(datos_propietario[0]), datos_propietario[1])
    if request.args.get('ano_mes'):
        datos_tabla = consultar_pagos(fecha=request.args.get('ano_mes'))
    return render_template('pagos_consultar.html', propietarios=propietarios, fechas=fechas, datos_tabla=datos_tabla)


@app.route('/pagos/aplicar', methods=['GET'])
@app.route('/pagos/aplicar/<pago_id>', methods=['GET'])
def pagos_aplicar(pago_id=None):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()

    pago_aplicado = ()
    recibos_procesados = []  # [(saldo, rowid), (...)]
    if pago_id:
        # (...) or None
        edificio, apartamento, pago_saldo = cur.execute(f''' SELECT edificio, apartamento, saldo FROM pagos
                                                    WHERE rowid={pago_id} AND saldo > 0''').fetchone() or ('Null', 'Null', 0)
        # Recibos asociados por pagar ? -> [(...),...] or [] if no rows
        recibos = cur.execute(f'''SELECT rowid, saldo , cuota_comun, cuota_edificio FROM recibos
                        WHERE edificio={edificio} AND apartamento='{apartamento}' AND saldo > 0 ''').fetchall()
        if pago_saldo and recibos:  # recibos con saldo > 0, pago con saldo > 0
            for recibo in recibos:  # (...)
                # unpack (rowid, saldo, cuota_comun, cuota_edificio)
                recibo_id, recibo_saldo, recibo_cuota_comun, recibo_cuota_edificio = recibo
                # recibo_saldo = recibo[1]
                if pago_saldo > recibo_saldo:
                    # recibos_procesados.append((0, recibo[0])) # (saldo, rowid) order matters for UPDATE placeholders
                    pago_saldo -= recibo_saldo
                    recibo_saldo = 0
                    cur.execute(f"UPDATE pagos SET saldo={
                                pago_saldo}, procesado=1 WHERE rowid={pago_id}")
                    cur.execute(f"UPDATE recibos SET saldo={
                                recibo_saldo}, procesado=1 WHERE rowid={recibo_id}")
                    recibos_procesados.append(recibo_id)
                    # insertar actualizacion de fondos
                    fondo_comun, fondo_edificio = cur.execute(
                        f'''SELECT comun, e{edificio} FROM fondos''').fetchone()
                    cur.execute(f'''UPDATE fondos SET   comun={fondo_comun + recibo_cuota_comun},
                                                        e{edificio}={fondo_edificio + recibo_cuota_edificio}''')
                elif recibo_saldo > pago_saldo:
                    recibo_saldo -= pago_saldo
                    pago_saldo = 0
                    cur.execute(f"UPDATE pagos SET saldo={
                                pago_saldo}, procesado=1 WHERE rowid={pago_id}")
                    cur.execute(f"UPDATE recibos SET saldo={
                                recibo_saldo}, procesado=1 WHERE rowid={recibo_id}")
                    recibos_procesados.append(recibo_id)
                    break
                else:
                    pago_saldo = 0
                    recibo_saldo = 0
                    cur.execute(f"UPDATE pagos SET saldo={
                                pago_saldo}, procesado=1 WHERE rowid={pago_id}")
                    cur.execute(f"UPDATE recibos SET saldo={
                                recibo_saldo}, procesado=1 WHERE rowid={recibo_id}")
                    recibos_procesados.append(recibo_id)
                    # insertar actualizacion de fondos
                    fondo_comun, fondo_edificio = cur.execute(
                        f'''SELECT comun, e{edificio} FROM fondos''').fetchone()
                    cur.execute(f'''UPDATE fondos SET   comun={fondo_comun + recibo_cuota_comun},
                                                        e{edificio}={fondo_edificio + recibo_cuota_edificio}''')
                    break
            con.commit()
            flash('Pago aplicado con exito...', 'success')
            pago_aplicado = cur.execute(f'''SELECT rowid,fecha, pago_usd, saldo
                                            FROM pagos WHERE rowid={pago_id} ''').fetchone()
            # IN clause wont work with a single element tuple
            if len(recibos_procesados) == 1:
                recibos_procesados.append('Null')
            recibos_procesados = cur.execute(f'''SELECT rowid,fecha, concepto, saldo
                                        FROM recibos
                                        WHERE rowid IN {tuple(recibos_procesados)} ''').fetchall()
        elif not pago_saldo:
            flash('No hay pago con saldo ...', 'warning')
        else:
            flash('No hay cuentas por pagar...', 'warning')

    # Crear tabla de pagos con saldo, actualizada luego de operaciones previas, si fuera el caso
    pagos_con_saldo = cur.execute(f"""SELECT rowid, edificio, apartamento, fecha, pago_bs, pago_usd, saldo
                                    FROM pagos
                                    WHERE saldo > 0 AND edificio != '' AND apartamento != '' """).fetchall()
    cur.close()
    con.close()
    return render_template('pagos_aplicar.html', pagos_con_saldo=pagos_con_saldo,
                           pago_aplicado=pago_aplicado, recibos_procesados=recibos_procesados)


@app.route('/gastos/ingresar', methods=['GET'])
def gastos_ingresar():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    gastos = cur.execute(f'''SELECT  rowid, * FROM gastos WHERE procesado=0
                ORDER BY fecha ''').fetchall()
    cur.execute('''SELECT * FROM fondos''')
    columnas = cur.description
    montos = cur.fetchone()
    cur.close()
    con.close()
    # [(columna, monto), ...]
    fondos = [x for x in map(lambda x, y: (x[0], y), columnas, montos)]
    return render_template('gastos_ingresar.html', gastos=gastos, fondos=fondos)


@app.route('/gastos/almacenar', methods=['POST'])
def gastos_almacenar():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    match request.form.get('moneda'):
        case 'bolivar':
            gasto_bs, gasto_usd = float(request.form.get('monto')), round(
                float(request.form.get('monto')) / float(request.form.get('tasa')))
        case 'dolar':
            gasto_usd, gasto_bs = int(request.form.get('monto')), 0.00
    try:
        cur.execute(f'''INSERT   INTO gastos (fecha, concepto, referencia, gasto_bs, gasto_usd, fondo)
                                VALUES (   '{request.form.get('fecha')}',
                                            '{request.form.get('concepto')}',
                                            '{request.form.get('referencia')}',
                                            {gasto_bs},
                                            {gasto_usd},
                                            '{request.form.get('fondo')}' ) ''')
        fondo_monto = cur.execute(f'''SELECT {request.form.get(
            'fondo')} FROM fondos''').fetchone()[0]  # -> (fondo,)
        fondo_monto -= gasto_usd
        cur.execute(f"""UPDATE fondos SET {
                    request.form.get('fondo')}={fondo_monto} """)
    except Exception as err:
        print(err)
        flash('Ha ocurrido un error...', 'danger')
    else:
        con.commit()
        flash('Operacion realizada con exito ...', 'success')
    finally:
        cur.close()
        con.close()
    return redirect(request.headers.get('referer'))


@app.route('/gastos/cerrar', methods=['GET'])
def gastos_cerrar():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''UPDATE gastos SET procesado=1 WHERE procesado=0''')
    con.commit()
    cur.close()
    con.close()
    return redirect(request.headers.get('referer'))


@app.route('/gasto/eliminar/<rowid>', methods=['GET'])
def gasto_eliminar(rowid):
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT gasto_usd, fondo
                                FROM gastos WHERE rowid={rowid}
                                AND procesado=0''')
    gasto_usd, fondo = cur.fetchone()  # tuple of two if any, or None
    fondo_monto = cur.execute(f'''SELECT {fondo} FROM fondos''').fetchone()[
        0]  # (int,)
    fondo_monto += gasto_usd
    cur.execute(f'''UPDATE fondos SET {fondo}={fondo_monto} ''')
    cur.execute(f'''DELETE FROM gastos WHERE rowid={rowid} AND procesado=0''')
    con.commit()
    cur.close()
    con.close()
    return redirect(request.headers.get('referer'))


@app.route('/gastos/consultar', methods=['GET'])
def gastos_consultar():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    print('primer cursor es', id(cur))
    # cur.execute('''SELECT fecha FROM gastos''')
    # fechas = cur.fetchall() # -> [(fecha,)...]
    # fechas = set([x[0][:7] for x in fechas])
    # print(fechas)
    fechas = fechas_disponibles('gastos')
    if request.args.get('ano_mes'):
        ano_mes = request.args.get('ano_mes')
        gastos = cur.execute(f'''SELECT rowid,*
                                FROM gastos
                                WHERE procesado=1
                                AND fecha LIKE '{ano_mes}%' ''')
        print('segunda identidad ?...', id(gastos))
        gastos = cur.fetchall()
    else:
        gastos = []
    cur.close()
    con.close()
    return render_template('gastos_consultar.html', fechas=fechas, gastos=gastos)

@app.route('/balance/bs', methods=['GET'])
def balance_bs():
    fechas = fechas_disponibles('gastos')
    ano_mes = request.args.get('ano_mes')
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    pagos = cur.execute(f'''SELECT fecha, edificio, apartamento, referencia, pago_bs
                    FROM pagos
                    WHERE pago_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''').fetchall()
    pagos_balance = [(x[0], str(x[1]) + '-' + x[2], x[3], '', x[4])
                     for x in pagos]
    cur.execute(f'''SELECT SUM(pago_bs)
                    FROM pagos
                    WHERE pago_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''')
    creditos = cur.fetchone()[0] or 0  # (value,) value can be None
    # print(pagos_balance)
    cur.execute(f'''SELECT fecha, concepto, referencia, gasto_bs FROM gastos
                    WHERE gasto_bs > 0.0 AND fecha LIKE '{ano_mes}%' ''')
    gastos = cur.fetchall()
    gastos_balance = [(x[0], x[1], x[2], x[3], '') for x in gastos]
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
    return render_template('balance_bs.html', fechas=fechas, pagos=pagos, gastos = gastos, 
                            balance=balance, debitos=debitos, creditos=creditos, ano_mes=ano_mes)


@app.route('/balance/usd', methods=['GET'])
#@app.route('/reporte/balance/usd/<ano_mes>', method='GET')
def balance_usd():
    fechas = fechas_disponibles('gastos')
    ano_mes = request.args.get('ano_mes')
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(f'''SELECT fecha, edificio, apartamento, pago_usd
                    FROM pagos
                    WHERE pago_bs = 0.0 AND fecha LIKE '{ano_mes}%' ''')
    pagos = cur.fetchall()
    print(pagos)
    pagos_balance = [(x[0], str(x[1]) + '-' + x[2], '', x[3])
                     for x in pagos]
    cur.execute(f'''SELECT SUM(pago_usd)
                    FROM pagos
                    WHERE pago_bs = 0 AND fecha LIKE '{ano_mes}%' ''')
    creditos = cur.fetchone()[0] or 0 # (value,) value can be None
    cur.execute(f'''SELECT fecha, concepto, gasto_usd
                    FROM gastos
                    WHERE gasto_bs = 0 AND fecha LIKE '{ano_mes}%' ''')
    gastos = cur.fetchall()
    gastos_balance = [(x[0], x[1], x[2], '') for x in gastos]
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
    return render_template('balance_usd.html', fechas=fechas, pagos=pagos, gastos=gastos, ano_mes=ano_mes,
                           debitos = debitos, creditos = creditos, balance=balance )

@app.route('/morosidad', methods=['GET'])
def morosidad():
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
                        GROUP BY recibos.edificio, recibos.apartamento
                        HAVING COUNT(recibos.fecha) >=3 ''')
    morosidad = cur.fetchall()
    cur.close()
    con.close()
    hoy = date.today()
    return render_template('morosidad.html', morosidad=morosidad, deuda=deuda, hoy=hoy)



# app.run(host='localhost', port=8080, debug=True)  # , reloader=True)
