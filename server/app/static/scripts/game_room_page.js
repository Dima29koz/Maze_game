document.addEventListener('DOMContentLoaded', () => {
    const room = document.querySelector('#get-room-name').innerHTML;
    const room_id = document.querySelector('#get-room-id').innerHTML;
    const current_user = document.querySelector('#get-user-name').innerHTML;

    // Connect to websocket
    let socket = io('/game_room');
    //let socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        socket.emit('join', {'room': room});
    });

    document.querySelector("#logout-room-btn").onclick = () => {
        socket.emit('leave', {'room': room});
    };

    socket.on('join', data => {
        drawPlayers(data);
        drawBtn(data);
    });

    socket.on('get_spawn', data => {
        drawSpawnMap(data);
    });

    //redirect всех игроков в комнате в игру
    socket.on('start', () => {
        window.location.href = '/game?room='+room+'&room_id='+room_id;
    });

    class Player {
        constructor(player_data, creator_name) {
            this.name = player_data.name;
            //this.is_online = player_data.is_online;
            this.is_spawned = player_data.is_spawned;
            this.is_creator = player_data.name == creator_name;
        }

        create_card() {
            let card = document.createElement('div');
            card.className = 'card bg-secondary my-1 border border-4';
            if (this.name == current_user) {
                card.className += ' border-warning';
            }

            let card_body = document.createElement('div');
            card_body.className = 'card-body d-flex py-2 align-items-center';

            let div_img = document.createElement('div');
            div_img.className = 'my-0 pe-2';

            let img = document.createElement('img');
            img.src = `./img/${this.name}`;
            img.alt = 'ave';
            img.width = 32;
            img.height = 32;
            img.className = "img-fluid rounded-circle ";
            div_img.append(img);
            card_body.append(div_img);

            if (this.is_creator) {
                let div_creator = document.createElement('div');
                div_creator.className = 'my-0 pe-2';
                div_creator.innerText = '⭐';
                card_body.append(div_creator);
            }

//            let div_online = document.createElement('div');
//            div_online.className = 'my-0 pe-2';
//            div_online.innerText = this.is_online ? '🟢' : '🔴';
//            card_body.append(div_online);

            let div_name = document.createElement('h5');
            div_name.className = 'my-0';
            div_name.innerText = this.name;
            card_body.append(div_name);

            let div_spawned = document.createElement('div');
            div_spawned.className = 'ms-auto my-0';
            div_spawned.innerText = this.is_spawned ? '🟢' : '🔴';
            card_body.append(div_spawned);

            card.append(card_body);

            return card;
        }
    }

    function drawPlayers(data) {
        const players = data.players;
        const slots_amount = data.players_amount;
        const bots = data.bots;

        let div = document.getElementById('players');
        div.innerHTML = '';

        for (let player of players) {
            player_obj = new Player(player, data.creator);
            div.append(player_obj.create_card());
        }

        for (let i=0; i < slots_amount - players.length; i++) {
            let div_slot = document.createElement('div');
            div_slot.className = 'card bg-secondary my-1';
            let card_body = document.createElement('div');
            card_body.className = 'card-body d-flex py-2 justify-content-center h5 my-0';
            card_body.innerText = 'Empty slot';
            div_slot.append(card_body);
            div.append(div_slot);
        }

        let div_bots = document.getElementById('bots');
        if (div_bots == null) {
            return;
        }
        if (data.bots.length == 0 && div_bots != null) {
            div_bots.remove();
            return;
        }
        div_bots.innerHTML = '';
        div_bots.className = 'pt-2'

        for (let bot of bots) {
            bot_obj = new Player(bot, data.creator);
            div_bots.append(bot_obj.create_card());
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