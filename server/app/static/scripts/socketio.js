document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io('/game_room');
    //var socket = io(location.protocol + '//' + document.domain + ':' + location.port + '/game_room');
    socket.on('connect', () => {
        socket.emit('my_event', 'wow connected!');
        console.log(`posted`)
    });

    socket.on('message', data => {
         console.log(`msg received: ${data}`);
    });
});