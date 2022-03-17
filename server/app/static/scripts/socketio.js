document.addEventListener('DOMContentLoaded', () => {
    // Set default
    const room = document.querySelector('#get-room-name').innerHTML;
    const user_name = document.querySelector('#get-username').innerHTML;

    // Connect to websocket
    let socket = io('/game_room');
    //var socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        socket.emit('message', {data: 'wow connected!'});
        console.log(`posted`)
    });

    socket.on('message', data => {
         console.log(`msg received: ${data.data}`);
    });

    socket.on('join', data => {
         let players = data.players;
         let max_players = data.max_players;
         drawPlayers(players, max_players);
    });


    joinRoom(room);


    // Trigger 'join' event
    function joinRoom(room) {
        // Join room
        socket.emit('join', {'username': user_name, 'room': room});

        console.log(`user ${user_name} join ${room}`);
    }

    function drawPlayers(players, max_players) {
        let div = document.getElementById('players');
        div.innerHTML = '';
        for (let player of players) {
            let p = document.createElement('p');
            p.className  = 'list-group-item list-group-item-action py-3 lh-tight'
            p.innerHTML = player;
            div.append(p);
        }

        if (players.length == max_players) {
            let btn = document.getElementById('start-btn');
            btn.disabled = false;
        }
    }

});