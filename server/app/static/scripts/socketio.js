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

    //redirect всех игроков в комнате в игру
    socket.on('start', () => {
         window.location.href = '/game';
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
            p.className  = 'list-group-item list-group-item-action py-3 lh-tight';
            if (player == creator_name) {
                p.classList.add('creator');
            }
            p.innerHTML = player;
            div.append(p);
        }
        for (let i=0; i < players_amount - players.length; i++) {
            p = document.createElement('p');
            p.className  = 'list-group-item list-group-item-action py-3 lh-tight';
            div.append(p);
        }
    }

    function drawBotsSection(data) {
        let bots_amount = data.bots_amount;

        let div = document.getElementById('bots');
        div.innerHTML = '';
        let p = document.createElement('p');
        p.innerHTML = 'Боты'
        div.append(p);
        for (let i=0; i < bots_amount; i++) {
            let p = document.createElement('p');
            p.className  = 'list-group-item list-group-item-action py-3 lh-tight';
            div.append(p);
        }
    }

    function drawBtn(data) {
        let creator = data.creator;

        if (creator == current_user) {
            let players = data.players;

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
});