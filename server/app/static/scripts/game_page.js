document.addEventListener('DOMContentLoaded', () => {
    const room = document.querySelector('#get-room-name').innerHTML;
    const room_id = document.querySelector('#get-room-id').innerHTML;

    let is_ended = false;
    let current_user = '';
    // Connect to websocket
    let socket = io('/game');
    //let socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        drawMapInteractive(getMapContext(4, 5)); // fixme
        socket.emit('join', {'room': room});
    });

    socket.on('join', data => {
        current_user = data.current_user;

        let response = fetch(`./api/game_data/${room_id}`)
            .then(response => response.json())
            .then(response_json => {
                is_ended = response_json.is_ended;
                drawTurnMessages(response_json.turns);
                socket.emit('get_allowed_abilities', {'room': room});
            });

        response = fetch(`./api/players_stat/${room_id}`)
            .then(response => response.json())
            .then(stats_json => drawPlayersStat(stats_json));
    });

    socket.on('turn_info', data => {
        drawTurnMessage(data.turn_data);
        scrollDownChatWindow();
        drawPlayersStat(data.players_stat);
        socket.emit('get_allowed_abilities', {'room': room});

        // del it after testing
        let response = fetch(`./api/game_field/${room_id}`)
            .then(response => response.json())
            .then(response_json => {
                drawMap(response_json.field, response_json.treasures, response_json.players, current_user);
            });
        // -------------
    });

    socket.on('win_msg', data => {
        drawTurnMessage(data);
        scrollDownChatWindow();
        is_ended = true;
        drawButtons();
    });

    socket.on('set_allowed_abilities', data => {
        drawButtons(data.allowed_abilities, data.is_active);
    });

    function drawButtons(allowed_abilities = null, is_active=false) {
        let div = document.getElementById('control');
        div.innerHTML = '';
        if (is_ended) {
            return;
        }
        let dirs = [
            ['top', '⬆'],
            ['left', '⬅'],
            ['bottom', '⬇'],
            ['right', '➡'],
        ];

        let acts = [
            ['shoot_bow', '🏹', false],
            ['throw_bomb', '💣', false],
            ['move', '🏃', true],
        ];

        let btn_group = document.createElement('div');
        btn_group.className = 'btn-group';

        let btn_gr_vert = document.createElement('div');
        btn_gr_vert.className = 'btn-group-vertical';
        let btn = createButton([null, '⭲'], 'skip', allowed_abilities.skip);
        btn_gr_vert.append(btn);
        btn = createButton(dirs[1], null);
        btn_gr_vert.append(btn);
        btn_group.append(btn_gr_vert);

        btn_gr_vert = document.createElement('div');
        btn_gr_vert.className = 'btn-group-vertical';
        btn = createButton(dirs[0], null);
        btn_gr_vert.append(btn);
        btn = createButton(dirs[2], null);
        btn_gr_vert.append(btn);
        btn_group.append(btn_gr_vert);

        btn_gr_vert = document.createElement('div');
        btn_gr_vert.className = 'btn-group-vertical';
        btn = createButton([null, '🔄'], 'swap_treasure', allowed_abilities.swap_treasure);
        btn_gr_vert.append(btn);
        btn = createButton(dirs[3], null);
        btn_gr_vert.append(btn);
        btn_group.append(btn_gr_vert);

        btn_gr_vert = document.createElement('div');
        btn_gr_vert.className = 'btn-group-vertical';
        res = createRadioBtn(acts[0], allowed_abilities.shoot_bow);
        btn_gr_vert.append(res[0]);
        btn_gr_vert.append(res[1]);
        res = createRadioBtn(acts[1], allowed_abilities.throw_bomb);
        btn_gr_vert.append(res[0]);
        btn_gr_vert.append(res[1]);
        res = createRadioBtn(acts[2], allowed_abilities.move);
        btn_gr_vert.append(res[0]);
        btn_gr_vert.append(res[1]);
        btn_group.append(btn_gr_vert);

        div.append(btn_group);


        function createButton(args, act, is_allowed=true) {
            let btn = document.createElement('button');
            btn.className = 'btn btn-lg btn-primary';
            btn.innerHTML = args[1];
            btn.onclick = () => onBtnClick(args[0], act);
            btn.disabled = !(is_active && is_allowed);
            return btn;
        }

        function onBtnClick(direction, action) {
            if (action == null) {
                action = document.querySelector('input[name="action"]:checked').value;
            }
            socket.emit('action', {'room': room, 'action': action, 'direction': direction});
        }

        function createRadioBtn(args, is_allowed=true) {

            let btn = document.createElement('input');
            btn.type = 'radio';
            btn.className = "btn-check";
            btn.id = args[0];
            btn.name = 'action';
            btn.value = args[0];
            btn.checked = args[2];
            btn.disabled = !(is_active && is_allowed);

            let label = document.createElement('label');
            label.className = "btn btn-outline-primary";
            label.htmlFor = args[0];
            label.innerHTML = args[1];
            return [btn, label];
        }
    }

    function drawTurnMessages(turns) {
        for (turn of turns) { drawTurnMessage(turn); }
        scrollDownChatWindow();
    }

    function drawTurnMessage(turn_data) {
        const div = document.createElement('div');
        div.className = "d-flex flex-row";
        const p = document.createElement('p');
        p.className = "msg";
        const span_username = document.createElement('span');
        const span_turn_info = document.createElement('span');
        const br = document.createElement('br')

        if (typeof turn_data.player == 'undefined' || turn_data.player == 'System') { printSysMsg(turn_data.response); }
        else {
            // user's own message
            if (turn_data.player == current_user) {
                div.classList.add('justify-content-end');
                p.classList.add('my-msg');
                span_username.classList.add('my-username');
            }

            // other users' messages
            else {
                div.classList.add('justify-content-start');
                p.classList.add('others-msg');
                span_username.classList.add('other-username');
            }

            span_username.innerText = turn_data.player;

            // TurnInfo
            span_turn_info.setAttribute("class", "text-muted");
            span_turn_info.innerText = ' (' + turn_data.action + dir() + ')';
            function dir() {
                if (turn_data.direction) {
                    return ' ' + turn_data.direction;
                }
                return '';
            };

            // HTML to append
            p.innerHTML += span_username.outerHTML + span_turn_info.outerHTML + br.outerHTML + turn_data.response + br.outerHTML;

            //Append
            div.append(p);
            document.getElementById('game-info').append(div);
        }
    }

    // Print system messages
    function printSysMsg(winner) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = `${winner} wins`;
        document.getElementById('game-info').append(p);
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.getElementById('game-info');
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function drawPlayersStat(players_data) {
        const div = document.getElementById('player-stats');
        div.innerHTML = '';
        for (player_data of players_data) {
            div.append(drawPlayerStat(player_data));
        }
    }

    function drawPlayerStat(player_data) {
        const div = document.createElement('div');
        div.className = 'col';
        const card = document.createElement('div');
        card.className = 'card bg-secondary';
        const card_header = document.createElement('div');
        card_header.className = 'card-header bg-info';
        let header_row = document.createElement('div');
        header_row.className = 'row';
        let header_col = document.createElement('div');
        header_col.className = 'col-2 g-0';
        let img = document.createElement('img');
        img.src = `./img/${player_data.name}`;
        img.alt = 'ave';
        img.width = 128;
        img.height = 128;
        img.className = "img-fluid rounded-circle";

        header_col.append(img);
        header_row.append(header_col);

        header_col = document.createElement('div');
        header_col.className = 'col-10';
        let content = document.createElement('p');
        content.className = 'card-title h5';
        content.innerText = player_data.name;
        header_col.append(content);
        let bar = document.createElement('div');
        bar.className = 'd-flex justify-content-between';
        content = document.createElement('p');
        content.className = 'card-text my-0';
        content.innerText = '❤'.repeat(player_data.health); //'❤❤🖤';
        bar.append(content);
        content = document.createElement('p');
        content.className = 'card-text my-0';
        content.innerText = player_data.has_treasure ? '💰' : '-'; //'💰';
        bar.append(content);
        header_col.append(bar);
        header_row.append(header_col);
        card_header.append(header_row);
        card.append(card_header);

        let card_body = document.createElement('div');
        card_body.className = 'card-body d-flex justify-content-between py-1';
        content = document.createElement('p');
        content.className = 'card-text my-0';
        content.innerText = player_data.arrows > 0 ? '🏹'.repeat(player_data.arrows): '-'; //'🏹🏹🏹';
        card_body.append(content);
        content = document.createElement('p');
        content.className = 'card-text my-0';
        content.innerText = player_data.bombs > 0 ? '💣'.repeat(player_data.bombs) : '-'; //'💣💣💣';
        card_body.append(content);
        card.append(card_body);
        div.append(card);

        return div;
    }

    function getMapContext(rows, cols) {
        const drawingCanvas = document.getElementById('map');
        const div = document.getElementById('map-container');
        let width = div.clientWidth;
        let height = div.clientHeight;
        tile_size = height < width ? height / (rows + 3) : width / (cols + 3);
        if(drawingCanvas && drawingCanvas.getContext) {
            drawingCanvas.getContext('2d').canvas.width  = width;
            drawingCanvas.getContext('2d').canvas.height = tile_size * (rows + 1);
            return {
                'canvas': drawingCanvas, 'tile_size': tile_size,
                'width': width, 'height': height, 'cols': cols, 'rows': rows
                }
        }
    }

});