from server.manage import app, sio


if __name__ == "__main__":
    sio.run(app, host='127.0.0.1', port=5001)
