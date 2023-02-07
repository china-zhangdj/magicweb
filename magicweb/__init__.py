import json
import socket
import time
import _thread


class request :
    def __init__(self):
        '''
        请求对象
        :param path: 请求路径
        :param method: 请求方法
        :param head: 请求头
        :param body: 请求体
        '''
        self.method = None
        self.path = None
        self.version = None
        self.head = None
        self.body = None

    def procParams(self):
        '''
        处理请求参数 GET POST
        :return: 请求参数处理结果
        '''
        if self.method == "POST" :
            params = self.body.decode().split("&")
        elif self.method == "GET" :
            params = self.path.split("?")
        else:
            params = []
        params_res = {}
        for i in params:
            spl = i.split("=")
            if len(spl) == 2:
                params_res[spl[0]] = spl[1]
        return params_res

class MagicWEB:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

    # 响应状态码
    OK = b"200 OK"
    NOT_FOUND = b"404 Not Found"
    FOUND = b"302 Found"
    FORBIDDEN = b"403 Forbidden"
    BAD_REQUEST = b"400 Bad Request"
    ERROR = b"500 Internal Server Error"

    # 文件名:Content对应数组
    MIME_TYPES = {
        'css': 'text/css',
        'html': 'text/html',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'js': 'text/javascript',
        'json': 'application/json',
        'rtf': 'application/rtf',
        'svg': 'image/svg+xml',
        'ico':'application/ico',
        'bin':"file/bin"
    }

    # 不允许下载的文件
    BLACK_LIST = [
    ]

    # 不允许访问的目录
    BLACK_DIR = [
    ]

    RESP_FILE = {
        ERROR:"html/500.html",
        NOT_FOUND:"html/404.html"
    }

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.debug = False
        self.routes_dict = {}
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.bind((address,port))
        self.sock.listen(10)
        self.control = False
        _thread.start_new_thread(self.__server,())


    #BACKEND SERVER METHODS
    def setRoutes(self, routes={}):
        '''
        设置路由表
        :param routes:
        :return:
        '''
        self.routes_dict = routes

    def addRouters(self,routers:dict={}):
        '''
        添加路由
        :param routers:
        :return:
        '''
        self.routes_dict.update(routers)

    def start(self):
        '''
        开启服务线程
        :return: None
        '''
        self.control = True
        print("MyltyWeb web server started.")
        print("version: v1.2.0")
        print("tuntime: 0.0s")
        print("*"*20)


    def __server(self):
        while True :
            if self.control :
                cli,addr = self.sock.accept()
                _thread.start_new_thread(self.__router,(cli,))
            else:
                time.sleep(1)
        pass

    def __router(self,client):
        recv = client.recv(1024)
        req = self.__processRequest(recv,client)  # type:request
        print("[{}] : {}".format(req.method,req.path))
        # 有请求方法
        if req.method != None :
            # 已声明，执行请求方法
            reqpath = req.path.split("?")[0]
            if reqpath in self.routes_dict.keys():
                self.routes_dict[reqpath](req,client)

            # 未声明,按文件取
            else:
                self.sendFile(client,filename=reqpath[1:])
        # 没有请求方法
        else:
            pass
            self.render(client, html_file=self.RESP_FILE[self.ERROR], status=self.ERROR)
        pass


    def __processRequest(self,reqdata,client) -> request:
        '''
        处理请求
        :return: request对象
        '''
        try :
            request_line, rest_of_request = reqdata.split(b'\r\n', 1)
            request_line = request_line.decode().strip().split(' ')
        except ValueError :
            self.render(client,self.NOT_FOUND,status=self.NOT_FOUND)
            pass
        # 处理请求行
        req = request()
        if len(request_line) > 1:
            req.method = request_line[0]
            req.path = request_line[1]
            req.version = request_line[2]
        req.head = {}
        raw_headers, body = rest_of_request.split(b'\r\n\r\n', 1)
        raw_headers = raw_headers.split(b'\r\n')
        # 拆分请求头
        for header in raw_headers:
            split_header = header.decode().strip().split(': ')
            req.head[split_header[0]] = split_header[1]
        # 处理请求体
        req.body = body
        return req

    def __sendStatus(self,client,status_code:bytes):
        '''
        发送HTTP响应状态码
        :param status_code: 状态码
        :return:
        '''
        response_line = b"HTTP/1.1 "
        client.send(response_line + status_code + b'\n')

    def __sendHeaders(self,client,headers_dict:dict={}):
        '''
        发送HTTP响应头
        :param headers_dict: 响应头数组
        :return:
        '''
        for key, value in headers_dict.items():
            client.send(b"%s: %s\n" % (key.encode(), value.encode()))

    def __sendBody(self,client,body_content):
        '''
        发送HTTP响应体
        :param body_content:
        :return:
        '''
        client.send(b'\n' + body_content + b'\n\n')
        client.close()


    def render(self,client,html_file,variables=False, status=OK):
        '''
        模板引擎
        :param writer: ws:w 对象
        :param html_file: 模板路径
        :param variables: 变量
        :param status: 状态码
        :return: None
        '''
        try:
            self.__sendStatus(client,status_code=status)
            self.__sendHeaders(client,headers_dict={'Content-Type': 'text/html'})
            client.send(b'\n')
            with open(html_file,'rb') as f:
                for line in f :
                    if variables:
                        for var_name, value in variables.items():
                            line = line.replace(b"{{%s}}" % var_name.encode(), str(value).encode())
                    client.send(line)
            client.send(b"\n\n")
        except Exception as e:
            pass
        client.close()



    def sendJSON(self,client,jsonobj):
        # send JSON data to client
        self.__sendStatus(client,status_code=self.OK)
        self.__sendHeaders(client,headers_dict={'Content-Type': 'application/json'})
        self.__sendBody(client,body_content=json.dumps(jsonobj))
        pass

    def sendFile(self,client,filename):
        '''
        发送文件
        :param filename: 文件名称
        :return:
        '''
        fsplit = filename.split(".")
        fsplen = len(fsplit)
        if fsplen == 1 :
            extension = "bin"
        else:
            extension = fsplit[-1]
        try:
            # 无权限列表
            if filename in self.BLACK_LIST :
                raise IOError("Permision denide !")
            if "/" in filename :
                dir = filename.split("/")[0]
                # 无权限目录
                if dir in self.BLACK_DIR :
                    raise IOError("Permision denide !")
            with open(filename, 'rb') as f:
                self.__sendStatus(client,status_code=self.OK)
                if extension in self.MIME_TYPES.keys():
                    self.__sendHeaders(client,headers_dict={'Content-Type': self.MIME_TYPES[extension]})
                else:
                    self.__sendHeaders(client, headers_dict={'Content-Type': "application/file"})
                client.send(b"\n")
                while True :
                    buff = f.read(102400)
                    if not buff:
                        f.close()
                        break
                    else:
                        client.send(buff)
            client.send(b"\n\n")
            client.close()
        except Exception as e:
            self.render(client, html_file=self.RESP_FILE[self.NOT_FOUND],status=self.NOT_FOUND)