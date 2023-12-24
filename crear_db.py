import sqlite3
import csv


def crear_db():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS unidades (
                        edificio        INTEGER NOT NULL ,
                        apartamento     TEXT NOT NULL, 
                        propietario     TEXT,
                        correo          TEXT,
                        telefono        TEXT,
                        CHECK           (edificio IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ,11 ,12, 13, 14, 15, 16) 
                                        AND 
                                        apartamento IN ('pba', 'pbb', 'pbc', '1a', '1b', '1c', '2a', '2b', '2c', '3a', '3b', '3c'))        
                        PRIMARY KEY     (edificio ,apartamento))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS recibos (
                        edificio        INTEGER NOT NULL,
                        apartamento     TEXT NOT NULL,
                        fecha           TEXT NOT NULL,
                        concepto        TEXT,        
                        cuota_comun     INTEGER NOT NULL,
                        cuota_edificio  INTEGER NOT NULL,
                        saldo           INTEGER NOT NULL,
                        procesado       INTEGER NOT NULL DEFAULT 0,
                        UNIQUE          (edificio, apartamento, fecha)
                        CHECK           (edificio IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ,11 ,12, 13, 14, 15, 16) 
                                        AND 
                                        apartamento IN ('pba', 'pbb', 'pbc', '1a', '1b', '1c', '2a', '2b', '2c', '3a', '3b', '3c')
                                        AND cuota_comun > 0 AND cuota_edificio >=0))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS pagos (
                        edificio        INTEGER,
                        apartamento     TEXT,        
                        fecha           TEXT NOT NULL,
                        referencia      TEXT,
                        pago_bs         REAL NOT NULL DEFAULT 0.00,
                        pago_usd        INTEGER NOT NULL,
                        saldo           INTEGER NOT NULL,
                        procesado       INTEGER NOT NULL DEFAULT 0,
                        CHECK           (pago_usd > 0))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS gastos (
                        fecha           TEXT NOT NULL,
                        concepto        TEXT NOT NULL,
                        referencia      TEXT,
                        gasto_bs        REAL DEFAULT 0.00,
                        gasto_usd       INTEGER DEFAULT 0,
                        fondo           TEXT NOT NULL,
                        procesado       INTEGER DEFAULT 0,
                        CHECK           (fondo IN ('comun', 'e1', 'e2', 'e3', 'e4', 'e5', 
                                                    'e6', 'e7', 'e8', 'e9', 'e10', 'e11', 
                                                    'e12', 'e13', 'e14', 'e15', 'e16' ))) ''')
    
    cur.execute('''CREATE TABLE IF NOT EXISTS fondos  (
                        comun           INTEGER NOT NULL DEFAULT 0,
                        e1              INTEGER NOT NULL DEFAULT 0,
                        e2              INTEGER NOT NULL DEFAULT 0,
                        e3              INTEGER NOT NULL DEFAULT 0,
                        e4              INTEGER NOT NULL DEFAULT 0,
                        e5              INTEGER NOT NULL DEFAULT 0,
                        e6              INTEGER NOT NULL DEFAULT 0,
                        e7              INTEGER NOT NULL DEFAULT 0,
                        e8              INTEGER NOT NULL DEFAULT 0,
                        e9              INTEGER NOT NULL DEFAULT 0,
                        e10             INTEGER NOT NULL DEFAULT 0,
                        e11             INTEGER NOT NULL DEFAULT 0,
                        e12             INTEGER NOT NULL DEFAULT 0,
                        e13             INTEGER NOT NULL DEFAULT 0,
                        e14             INTEGER NOT NULL DEFAULT 0,
                        e15             INTEGER NOT NULL DEFAULT 0,
                        e16             INTEGER NOT NULL DEFAULT 0)''')
    con.commit()
    cur.close()
    con.close()


def cargar_unidades():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    with open('unidades.csv', mode='r') as csvfile:
        reader = csv.reader(csvfile)
        cur.executemany('''INSERT INTO unidades (   edificio,
                                                    apartamento,
                                                    propietario,
                                                    correo,
                                                    telefono    )
                            VALUES (?,?,?,?,?)''', reader)
    con.commit()
    cur.close()
    con.close()


def cargar_recibos():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    with open('recibos.csv', mode='r') as csvfile:
        reader = csv.reader(csvfile)
        cur.executemany('''INSERT INTO recibos (    edificio,
                                                    apartamento,
                                                    fecha,
                                                    concepto,
                                                    cuota_comun,
                                                    cuota_edificio,
                                                    saldo,
                                                    procesado         )
                            VALUES (?,?,?,?,?,?,?,?)''', reader)
    con.commit()
    cur.close()
    con.close()

def iniciar_fondos():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute(''' INSERT INTO fondos 
                    VALUES (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)''')
    con.commit()
    cur.close()
    con.close()


crear_db()
cargar_unidades()
#cargar_recibos()
iniciar_fondos()
