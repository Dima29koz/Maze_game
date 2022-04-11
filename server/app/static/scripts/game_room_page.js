document.addEventListener('DOMContentLoaded', () => {
    const room = document.querySelector('#get-room-name').innerHTML;
    const current_user = document.querySelector('#get-user-name').innerHTML;

    // Connect to websocket
    let socket = io('/game_room');
    //let socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        socket.emit('join', {'room': room});
    });

    socket.on('join', data => {
        drawPlayerSection(data);
        drawBotsSection(data);
        drawBtn(data);
    });

    socket.on('get_spawn', data => {
        drawSpawnMap(data);
    });

    socket.on('set_spawn', data => {
        drawBtn(data);
    });

    //redirect всех игроков в комнате в игру
    socket.on('start', () => {
        window.location.href = '/game?room='+room;
    });

    function drawPlayerSection(data) {
        let players = data.players;
        let players_amount = data.players_amount;
        let creator_name = data.creator;

        let div = document.getElementById('players');
        div.innerHTML = '';
        let p = document.createElement('p');
        p.innerHTML = 'Игроки'
        div.append(p);
        for (let player of players) {
            p = document.createElement('p');
            p.className  = 'list-group-item py-3 lh-tight';
            if (player == creator_name) {
                p.classList.add('creator');
            }
            if (player == current_user) {
                p.classList.add('current');
            }
            p.innerHTML = player;
            div.append(p);
        }
        for (let i=0; i < players_amount - players.length; i++) {
            p = document.createElement('p');
            p.className  = 'list-group-item py-3 lh-tight';
            div.append(p);
        }
    }

    function drawBotsSection(data) {
        let bots = data.bots_name;

        let div = document.getElementById('bots');
        if (div == null) {
            return;
        }
        if (data.bots_amount == 0 && div != null) {
            div.remove();
            return;
        }
        div.innerHTML = '';
        let p = document.createElement('p');
        p.innerHTML = 'Боты'
        div.append(p);
        for (let bot of bots) {
            p = document.createElement('p');
            p.className  = 'list-group-item py-3 lh-tight';
            p.innerHTML = bot;
            div.append(p);
        }
    }

    function drawBtn(data) {
        let creator = data.creator;

        if (creator == current_user) {

            let div = document.getElementById('control');
            div.innerHTML = '';

            let btn = document.createElement('button');
            btn.className = 'w-100 btn btn-lg btn-primary';
            btn.innerHTML = 'Начать игру';
            btn.onclick = () => socket.emit('start', {'room': room});
            btn.disabled = !data.is_ready;
            div.append(btn);
        }
    }

    function drawSpawnMap(data) {
        const field = data.field;
        const drawingCanvas = document.getElementById('map');
        const div = document.getElementById('map-container');
        width = div.clientWidth;
        height = div.clientHeight;
        tile_size = height < width ? height / field.length : width / field[0].length;
        if(drawingCanvas && drawingCanvas.getContext) {
            let context = drawingCanvas.getContext('2d');
            context.canvas.width  = tile_size * field[0].length;
            context.canvas.height = tile_size * field.length;
            let cells = drawField(context);
            if (data.spawn_info == null) {
                drawingCanvas.onclick = e => {
                    cells.forEach(cell_obj => {
                        if (cell_obj !== null) {
                            if(context.isPointInPath(cell_obj, e.offsetX, e.offsetY)){
                                socket.emit('set_spawn', {'room': room, 'spawn': cell_obj.data});
                                drawingCanvas.onclick = null;
                                drawCell(cell_obj.data, context, true);
                            }
                        }
                    })
                }
            }
            else {
                drawCell(data.spawn_info, context, true);
            }
        }

        function drawField(context) {
            let cells = [];
            for (row of field) {
                for (cell of row) {
                    if (cell != null) {
                        cells.push(drawCell(cell, context));
                    }
                }
            }
            return cells;
        }

        function drawCell(cell, context, is_pressed=false) {
            let cell_obj = new Path2D();
            x = cell.x * tile_size;
            y = cell.y * tile_size;
            cell_obj.rect(x+2, y+2, tile_size-4, tile_size-4);
            cell_obj.data = { 'x': cell.x, 'y': cell.y };
            context.fillStyle = is_pressed ? '#453E26' : '#6b623c';
            context.fill(cell_obj);
            return cell_obj;
        }
    }
});