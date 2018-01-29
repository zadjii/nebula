# Threading Breakdown

This is what the threading model looked like prior to the early Janurary 2018
  refactoring. It used asyncio to power the websocket. That for some reason
  didn't work well with ssl, so I switched it to Twisted.

- zadjii, 15 jan 2018

## Thread (0) - Main Thread
- `HostController::start()`
    - `NetworkController::__init__()`
    - `NetworkController::refresh_external_ip`
    - `HostController::spawn_net_thread`
        - `NetworkThread::__init__`
            - `NetworkThread::setup_socket`
                - Creates the TCP socket, binds it.
                - maps it to an external port
        - `Thread(NetworkThread::work_thread).start()` -> Thread(1)
        - `Thread(NetworkThread::ws_work_thread).start()` -> Thread(2)
    - `HostController::do_local_updates`

## Thread (1) - TCP Socket Thread
- `NetworkThread::work_thread`
    - Listens to the tcp socket
    - adds connections to the connection queue
    - signals the host to handle the new connection.

## Thread (2) - Websocket Thread
- `NetworkThread::ws_work_thread`
    - `NetworkThread::setup_web_socket`
        - `NetworkThread::_make_internal_socket`
            - create the localhost socket for the internal side of the WS
        - `ws_event_loop = asyncio.new_event_loop`
        - `asyncio.set_event_loop(self.ws_event_loop)`
        - Bind the socket for the websocket
        - map it's port to an external port
        - `factory = WebSocketServerFactory(ws_url)`
        - `factory.protocol = MyBigFuckingLieServerProtocol`
        - `ws_event_loop.create_server(factory`
    - listen on the `ws_internal_server_socket`
    - `ws_event_loop.run_until_complete(self.ws_coro)`
    - `ws_event_loop.run_forever`
