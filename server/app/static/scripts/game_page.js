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
    });

    socket.on('turn_info', data => {
        console.log(data);
        drawGameMessages(data);
        socket.emit('check_active', {'room': room});

    });

    socket.on('set_active', data => {
        is_active = data.is_active;
        drawButtons(data.allowed_abilities);
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

        let row = document.createElement('div');
        row.className = 'row row-cols-5';

        let btn = createButton([null, '⭲'], 'skip', allowed_abilities.skip);
        btn.classList.add('col-md-1');
        row.append(btn);

        btn = createButton([null, '🔄'], 'swap_treasure', allowed_abilities.swap_treasure);
        btn.classList.add('col-md-1');
        btn.classList.add('offset-md-1');
        row.append(btn);

        res = createRadioBtn(acts[0], allowed_abilities.shoot_bow);
        res[1].classList.add('col-md-1');
        res[1].classList.add('offset-md-1');
        row.append(res[0]);
        row.append(res[1]);

        div.append(row);

        row = document.createElement('div');
        row.className = 'row row-cols-5';
        btn = createButton(dirs[0], null);
        btn.classList.add('col-md-1');
        btn.classList.add('offset-md-1');
        row.append(btn);

        res = createRadioBtn(acts[1], allowed_abilities.throw_bomb);
        res[1].classList.add('col-md-1');
        res[1].classList.add('offset-md-2');
        row.append(res[0]);
        row.append(res[1]);

        div.append(row);

        row = document.createElement('div');
        row.className = 'row row-cols-5';
        for (let elem = 1; elem < 4; elem++) {
            btn = createButton(dirs[elem], null);
            btn.classList.add('col-md-1');
            row.append(btn);
        }

        res = createRadioBtn(acts[2], allowed_abilities.move);
        res[1].classList.add('col-md-1');
        res[1].classList.add('offset-md-1');
        row.append(res[0]);
        row.append(res[1]);

        div.append(row);


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

    function drawGameMessages(data) {
        const p = document.createElement('p');
        const span_username = document.createElement('span');
        const span_turn_info = document.createElement('span');
        const br = document.createElement('br')
        // Display user's own message
        if (typeof data.player == 'undefined') { printSysMsg(data.msg); }
        else {
            if (data.player == current_user) {
                p.setAttribute("class", "my-msg");
                span_username.setAttribute("class", "my-username");
            }

            // Display other users' messages
            else {
                p.setAttribute("class", "others-msg");
                span_username.setAttribute("class", "other-username");
            }

            span_username.innerText = data.player;

            // TurnInfo
            span_turn_info.setAttribute("class", "text-muted");
            span_turn_info.innerText = ' (' + data.action + dir() + ')';
            function dir() {
                if (data.direction) {
                    return ' ' + data.direction;
                }
                return '';
            };

            // HTML to append
            p.innerHTML += span_username.outerHTML + span_turn_info.outerHTML + br.outerHTML + data.response + br.outerHTML;

            //Append
            document.getElementById('game-info').append(p);
        }
        scrollDownChatWindow();
    }

    // Print system messages
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.getElementById('game-info').append(p);
        scrollDownChatWindow();
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.getElementById('game-info');
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
});