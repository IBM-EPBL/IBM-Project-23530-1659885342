import ibm_db

def connection():
    try:
        #samreen db2 credential
        conn=ibm_db.connect("DATABASE=bludb;\
                             HOSTNAME=19af6446-6171-4641-8aba-9dcff8e1b6ff.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;\
                             PORT=30699;\
                             PROTOCOL=TCPIP;\
                             UID=ddb22023;\
                             PWD=pm6CGacdO7nzi3pU;\
                             SECURITY=SSL;\
                             SSLServerCertificate=DigiCertGlobalRootCA.crt;\
                             ", "", "")
        print("CONNECTED TO DATABASE")
        return conn
    except:
        print(ibm_db.conn_errormsg())
        print("CONNECTION FAILED")

if __name__=='__main__':
    connection()