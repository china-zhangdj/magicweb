import time

from magicweb import request,MagicWEB


def host(req:request,client) :
    server.render(client,"templates/aa.html", {"asd":"hello"})

def favicon(req:request,client) :
    server.render(client,"templates/aa.html", {"asd":"hello"})


server = MagicWEB("0.0.0.0",80)
server.addRouters({"/":host})
server.start()

while True:
    time.sleep(1)
