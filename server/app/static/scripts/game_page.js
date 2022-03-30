document.addEventListener('DOMContentLoaded', () => {
    const room = document.querySelector('#get-room-name').innerHTML;
    //const current_user = document.querySelector('#get-user-name').innerHTML;
    let is_active = false;
    let current_user = '';
    // Connect to websocket
    let socket = io('/game');
    //let socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        socket.emit('join', {'room': room});
    });

    socket.on('join', data => {
        current_user = data.current_user;
        socket.emit('check_active', {'room': room});
        socket.emit('get_history', {'room': room});
    });

    socket.on('turn_info', data => {
        drawTurnMessage(data);
        scrollDownChatWindow();
        socket.emit('check_active', {'room': room});

    });

    socket.on('set_active', data => {
        is_active = data.is_active;
        drawButtons(data.allowed_abilities);
    });

    socket.on('set_history', data => {
        drawTurnMessages(data.turns);
    });

    function drawButtons(allowed_abilities) {
        let div = document.getElementById('control');
        div.innerHTML = '';

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

        if (typeof turn_data.player == 'undefined') { printSysMsg(turn_data.msg); }
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
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.getElementById('game-info').append(p);
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.getElementById('game-info');
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});