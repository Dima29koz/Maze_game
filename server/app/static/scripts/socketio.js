document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io('/game_room');
    //var socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        socket.emit('message', {data: 'wow connected!'});
        console.log(`posted`)
    });

    socket.on('message', data => {
         console.log(`msg received: ${data.data}`);
    });

    // Set default room
    let room = "Lounge"
    joinRoom("Lounge");

    // Trigger 'join' event
    function joinRoom(room) {
        const user_name = document.querySelector('#get-username').innerHTML;
        // Join room
        socket.emit('join', {'username': user_name, 'room': room});

        console.log(`user ${user_name} join ${room}`);
    }
});