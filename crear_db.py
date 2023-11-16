import sqlite3, csv

def crear_db():
    con = sqlite3.connect("terranorte.db")
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS unidades (
                        edificio        INTEGER NOT NULL ,
                        apartamento     TEXT NOT NULL, 
                        propietario     TEXT,
                        correo          TEXT,
                        telefono        TEXT,
                        cuota_comun     INTEGER NOT NULL DEFAULT 0,
                        cuota_edificio  INTEGER NOT NULL DEFAULT 0,
                        cuota_agua      INTEGER NOT NULL DEFAULT 0,
                        cuota_otro      INTEGER NOT NULL DEFAULT 0,
                        saldo           INTEGER NOT NULL DEFAULT 0,
                        CHECK   (   edificio IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ,11 ,12, 13, 14, 15, 16) 
                                    AND 
                                    apartamento IN ('pba', 'pbb', 'pbc', '1a', '1b', '1c', '2a', '2b', '2c', '3a', '3b', '3c')
                                ),        
                        PRIMARY KEY (edificio ,apartamento))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS pagos (
                        edificio        INTEGER,
                        apartamento     TEXT,        
                        fecha           TEXT NOT NULL,
                        referencia      TEXT,
                        pago_bs         REAL DEFAULT 0.00,
                        pago_usd        REAL DEFAULT 0.00,
                        pago_total      REAL NOT NULL,
                        procesado       INTEGER DEFAULT 0)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS recibos (
                        edificio        INTEGER NOT NULL,
                        apartamento     TEXT NOT NULL,
                        fecha           TEXT NOT NULL,
                        concepto        TEXT,        
                        cuota_comun     INTEGER NOT NULL,
                        cuota_edificio  INTEGER NOT NULL,
                        cuota_agua      INTEGER NOT NULL,
                        cuota_otro      INTEGER NOT NULL,
                        procesado       INTEGER DEFAULT 0,
                        CHECK   (   edificio IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ,11 ,12, 13, 14, 15, 16) 
                                    AND 
                                    apartamento IN ('pba', 'pbb', 'pbc', '1a', '1b', '1c', '2a', '2b', '2c', '3a', '3b', '3c')
                                ))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS fondos (
                        comun                   REAL NOT NULL DEFAULT 0.00,
                        edificio_1              REAL NOT NULL DEFAULT 0.00,
                        edificio_2              REAL NOT NULL DEFAULT 0.00,
                        edificio_3              REAL NOT NULL DEFAULT 0.00,
                        edificio_4              REAL NOT NULL DEFAULT 0.00,
                        edificio_5              REAL NOT NULL DEFAULT 0.00,
                        edificio_6              REAL NOT NULL DEFAULT 0.00,
                        edificio_7              REAL NOT NULL DEFAULT 0.00,
                        edificio_8              REAL NOT NULL DEFAULT 0.00,
                        edificio_9              REAL NOT NULL DEFAULT 0.00,
                        edificio_10             REAL NOT NULL DEFAULT 0.00,
                        edificio_11             REAL NOT NULL DEFAULT 0.00,
                        edificio_12             REAL NOT NULL DEFAULT 0.00,
                        edificio_13             REAL NOT NULL DEFAULT 0.00,
                        edificio_14             REAL NOT NULL DEFAULT 0.00,
                        edificio_15             REAL NOT NULL DEFAULT 0.00,
                        edificio_16             REAL NOT NULL DEFAULT 0.00,
                        agua_1                  REAL NOT NULL DEFAULT 0.00,
                        agua_2                  REAL NOT NULL DEFAULT 0.00,
                        agua_3                  REAL NOT NULL DEFAULT 0.00,
                        agua_4                  REAL NOT NULL DEFAULT 0.00,
                        agua_5                  REAL NOT NULL DEFAULT 0.00,
                        agua_6                  REAL NOT NULL DEFAULT 0.00,
                        agua_7                  REAL NOT NULL DEFAULT 0.00,
                        agua_8                  REAL NOT NULL DEFAULT 0.00,
                        agua_9                  REAL NOT NULL DEFAULT 0.00,
                        agua_10                 REAL NOT NULL DEFAULT 0.00,
                        agua_11                 REAL NOT NULL DEFAULT 0.00,
                        agua_12                 REAL NOT NULL DEFAULT 0.00,
                        agua_13                 REAL NOT NULL DEFAULT 0.00,
                        agua_14                 REAL NOT NULL DEFAULT 0.00,
                        agua_15                 REAL NOT NULL DEFAULT 0.00,
                        agua_16                 REAL NOT NULL DEFAULT 0.00,
                        otro_1                  REAL NOT NULL DEFAULT 0.00,
                        otro_2                  REAL NOT NULL DEFAULT 0.00,
                        otro_3                  REAL NOT NULL DEFAULT 0.00,
                        otro_4                  REAL NOT NULL DEFAULT 0.00,
                        otro_5                  REAL NOT NULL DEFAULT 0.00,
                        otro_6                  REAL NOT NULL DEFAULT 0.00,
                        otro_7                  REAL NOT NULL DEFAULT 0.00,
                        otro_8                  REAL NOT NULL DEFAULT 0.00,
                        otro_9                  REAL NOT NULL DEFAULT 0.00,
                        otro_10                 REAL NOT NULL DEFAULT 0.00,
                        otro_11                 REAL NOT NULL DEFAULT 0.00,
                        otro_12                 REAL NOT NULL DEFAULT 0.00,
                        otro_13                 REAL NOT NULL DEFAULT 0.00,
                        otro_14                 REAL NOT NULL DEFAULT 0.00,
                        otro_15                 REAL NOT NULL DEFAULT 0.00,
                        otro_16                 REAL NOT NULL DEFAULT 0.00)''')
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
                                                    telefono,
                                                    cuota_comun,
                                                    cuota_edificio,
                                                    cuota_agua,
                                                    cuota_otro,
                                                    saldo     )
                            VALUES (?,?,?,?,?,?,?,?,?,?)''', reader)
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
                                                    cuota_agua,
                                                    cuota_otro  )
                            VALUES (?,?,?,?,?,?,?,?)''', reader)
    con.commit()
    cur.close()
    con.close()


# crear_db()
# cargar_unidades()
cargar_recibos()

