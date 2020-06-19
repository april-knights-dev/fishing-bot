import sqlite3 

class fishDb():
    
    def __init__(self,dbName):
        self.dbName=dbName

    def selectFishInfoAll(self):
        conn = sqlite3.connect(self.dbName)
        c = conn.cursor()

        sql = "select * from fish_info"
        c.execute(sql)

        resultSet = c.fetchall

        c.close()
        conn.close()

        return resultSet
